#!/usr/bin/env python3
"""网页文章落地为本地 Markdown。

把一篇或多篇网页抓成 Markdown,严格保留正文里的图片与代码块:
  - 代码块输出为带语言标注的围栏代码(```lang ... ```);
  - 图片补全为绝对地址,默认下载到每篇文章自己的 images/ 目录;
  - 支持一次传入多个链接,或从文本文件批量读取。

脚本只做「抓取 + 粗清洗」。语义整理(去广告残留、理顺标题层级、写成标准 md)
由使用本工具的模型按 skill 说明完成,避免脚本误删正文。

用法:
    python web_to_md.py <url> [url ...] [-d 输出目录] [--download-images]
    python web_to_md.py -f urls.txt -d articles --download-images
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 默认请求头。公众号不要用手机微信 UA:实测会跳到验证码页。
HEADERS = {
    "User-Agent": CHROME_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 各站点的正文/标题选择器,按顺序尝试,命中即用。
# 没写进表里的站点会走 GENERIC_CONTENT 启发式。
# 匹配时用后缀: blog.csdn.net 也能对上 xxx.csdn.net。
SITE_RULES = {
    "blog.csdn.net": {
        "content": ["#content_views", "article .blog-content-box", "#article_content"],
        "title": ["h1.title-article", "#articleContentId", "h1"],
    },
    "csdn.net": {
        "content": ["#content_views", "article .blog-content-box", "#article_content"],
        "title": ["h1.title-article", "h1"],
    },
    "mp.weixin.qq.com": {
        "content": ["#js_content", ".rich_media_content"],
        "title": ["#activity-name", "h1.rich_media_title", "h1"],
        "author": ["#js_name", ".rich_media_meta_nickname", "a.rich_media_meta_link"],
        "author_label": "公众号",
    },
    "www.cnblogs.com": {
        "content": ["#cnblogs_post_body"],
        "title": ["#cb_post_title_url", ".postTitle"],
    },
    "juejin.cn": {
        "content": [".markdown-body", "#article-root"],
        "title": [".article-title", "h1"],
    },
    "zhuanlan.zhihu.com": {
        "content": [".Post-RichText", ".RichText"],
        "title": [".Post-Title", "h1"],
    },
    "www.jianshu.com": {
        "content": ["article", ".show-content"],
        "title": ["h1.title", "h1"],
    },
    "github.com": {
        "content": ["article.markdown-body"],
        "title": ["h1", "title"],
    },
    "segmentfault.com": {
        "content": ["article.article-content", ".article-content"],
        "title": ["h1"],
    },
    "www.zhihu.com": {
        "content": [".RichText", ".Post-RichText"],
        "title": ["h1"],
    },
}

# 通用正文候选(按优先级);标题统一回退到 <h1> / <title>。
GENERIC_CONTENT = [
    "article",
    "main",
    ".post-content",
    ".article-content",
    ".entry-content",
    "#content",
    ".content",
    ".markdown-body",
]

# 正文里需要剔除的噪声:脚本、广告、目录、评论、推荐、分享条等。
# 只删「明显不是正文」的节点,宁可多留一点给模型整理,也不误删段落。
NOISE_SELECTORS = [
    "script", "style", "noscript", "iframe",
    ".hljs-button", ".copy-btn", ".code-copy", "[data-report-click]",
    ".pre-numbering", ".hljs-ln-numbers", ".gutter",
    ".csdn-watermark", "[class*=watermark]",
    ".article-copyright", ".blog-tags-box", ".toc", ".table-of-contents",
    ".recommend-box", ".recommend-item-box", ".insert-baidu-box",
    ".comment-box", "#comment_title", ".comment-list",
    ".more-toolbox", ".article-info-box", ".blog-footer-bottom",
    ".hide-article-box", ".look-more-preCode",
    ".article-source-box", ".follow-nickName",
    "aside", ".sidebar", ".side-bar",
    ".share-box", ".social-share",
    ".ad", ".ads", ".advertisement", "[class*=advert]",
    ".related-posts", ".related-articles",
    # CSDN
    ".blog-intro", "#blogColumnPayAdvert",
    ".first-recommend-box", ".second-recommend-box",
    ".csdn-side-toolbar", ".article-type-img",
    # 微信公众号
    "mp-common-profile", "#js_tags", ".reward_area",
    "#js_profile_qrcode", ".qr_code_pc", "#js_pc_qr_code",
    ".rich_media_tool", "#js_content_end",
    ".wx_follow_checkbox", ".wx_follow_context",
]

# 装饰图/追踪像素常见特征,下载前丢弃,避免污染 images/。
DECORATIVE_IMG_RE = re.compile(
    r"(avatar|emoji|badge|icon[-_]|favicon|pixel|spacer|1x1|tracking|"
    r"qrcode|qr[-_]?code|weixin[-_]?qr|logo[-_]?small|"
    r"we-emoji|wx_follow|qr_code_pc|jump_wx_qrcode)",
    re.I,
)

# 公众号文末装饰块(往期推荐、关注引导),整段丢掉。
WEIXIN_FOOTER_RE = re.compile(
    r"^(往期推荐|相关阅读|推荐阅读|阅读原文|关注我们|点击关注|end|END)$"
)

# 解析图片真实地址时的属性顺序:公众号/CSDN 的 src 经常是占位图。
IMG_SRC_ATTRS = (
    "data-src", "data-original", "data-actualsrc",
    "data-lazy-src", "data-echo", "data-backsrc", "src",
)


def site_rule(host):
    """按域名后缀找到站点规则。blog.csdn.net 也能命中 csdn.net。"""
    host = (host or "").lower()
    if host in SITE_RULES:
        return SITE_RULES[host]
    for domain, rule in SITE_RULES.items():
        if host == domain or host.endswith("." + domain):
            return rule
    return {}


def is_weixin(host_or_url):
    text = (host_or_url or "").lower()
    return "mp.weixin.qq.com" in text or "weixin.qq.com" in text


def is_csdn(host_or_url):
    return "csdn.net" in (host_or_url or "").lower()


def page_headers(url):
    """按站点拼页面请求头。公众号必须用桌面 Chrome,手机微信 UA 会跳验证码。"""
    headers = dict(HEADERS)
    if is_weixin(url):
        headers["Referer"] = "https://mp.weixin.qq.com/"
    elif is_csdn(url):
        headers["Referer"] = "https://blog.csdn.net/"
    return headers


def image_headers(img_url, page_url=""):
    """下载图片用的请求头。公众号 CDN 需要带 Referer,否则可能被拦。"""
    headers = {
        "User-Agent": CHROME_UA,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    host = urlparse(img_url).netloc.lower()
    if is_weixin(page_url) or "mmbiz.qpic.cn" in host or host.endswith("qpic.cn"):
        headers["Referer"] = "https://mp.weixin.qq.com/"
    elif is_csdn(page_url) or "csdnimg.cn" in host:
        headers["Referer"] = "https://blog.csdn.net/"
    elif page_url:
        headers["Referer"] = page_url
    return headers


def warmup(session, url):
    """部分站点(尤其 CSDN)先访问首页拿 cookie,能少碰到 521。"""
    if not is_csdn(url):
        return
    try:
        session.get("https://blog.csdn.net/", headers=page_headers("https://blog.csdn.net/"),
                    timeout=15)
    except requests.RequestException:
        pass


def fetch(url, session=None, retries=3):
    """抓取网页 HTML,自动处理编码。遇到 5xx/超时会重试几次。"""
    sess = session or requests.Session()
    last_exc = None
    headers = page_headers(url)
    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            # 优先用响应声明的编码;若为可疑的 ISO-8859-1 则改用内容推断,保证中文不乱码。
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding
            html = resp.text
            if "wappoc_appmsgcaptcha" in resp.url or "环境异常" in html[:4000]:
                raise RuntimeError(
                    "微信公众号触发了访问验证,稍后再试,或用浏览器打开后把全文复制过来"
                )
            return html
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= retries:
                break
            wait = 1.5 * attempt
            print("  [重试 %d/%d] %s, %.1f 秒后再试" % (attempt, retries, exc, wait),
                  file=sys.stderr)
            time.sleep(wait)
    raise last_exc


def _pick(soup, selectors):
    """按选择器顺序返回第一个命中的元素。"""
    for sel in selectors:
        el = soup.select_one(sel)
        if el is not None:
            return el
    return None


def find_title(soup, host):
    """提取文章标题。"""
    rule = site_rule(host)
    el = _pick(soup, rule.get("title", []) + ["h1", "title"])
    if el is None:
        return "untitled"
    text = el.get_text(strip=True)
    # 去掉 CSDN/博客常见的 "-xxx博客" 站点后缀
    text = re.sub(r"[-_|]\s*[^-_|]*(博客|CSDN|掘金|知乎|简书).*$", "", text).strip()
    return text or "untitled"


def find_author(soup, host):
    """提取作者/公众号名。没有就返回空字符串。"""
    rule = site_rule(host)
    el = _pick(soup, rule.get("author", []))
    if el is None:
        return "", ""
    name = el.get_text(strip=True)
    return name, rule.get("author_label", "作者")


def find_content(soup, host):
    """定位正文容器:先用站点规则,再用通用候选,最后回退到 <body>。

    通用候选会挑选「文本量最大」的那个,避免选到侧边栏等小块。
    """
    rule = site_rule(host)
    el = _pick(soup, rule.get("content", []))
    if el is not None:
        return el

    best, best_len = None, 0
    for sel in GENERIC_CONTENT:
        for cand in soup.select(sel):
            length = len(cand.get_text(strip=True))
            if length > best_len:
                best, best_len = cand, length
    return best or soup.body or soup


def clean(content_el):
    """移除正文中的噪声元素(脚本、复制按钮、行号、水印、推荐栏等)。"""
    for sel in NOISE_SELECTORS:
        for tag in content_el.select(sel):
            tag.decompose()
    return content_el


def _img_dimension(el, attr):
    """读取 img 的宽/高。HTML 属性优先,其次 style。读不到返回 None。"""
    raw = el.get(attr)
    if raw:
        digits = re.sub(r"[^\d.]", "", str(raw))
        if digits:
            try:
                return float(digits)
            except ValueError:
                pass
    style = el.get("style") or ""
    m = re.search(r"%s\s*:\s*([\d.]+)" % attr, style, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def is_decorative_image(el):
    """判断是否为装饰图/追踪像素,不应随正文落地。

    只根据尺寸、文件名、class 做保守判断;拿不准的图一律保留,交给模型再筛。
    """
    width = _img_dimension(el, "width")
    height = _img_dimension(el, "height")
    if width is not None and height is not None and width <= 32 and height <= 32:
        return True
    if (width is not None and width <= 2) or (height is not None and height <= 2):
        return True

    blob = " ".join([
        el.get("src") or "",
        el.get("data-src") or "",
        el.get("data-lazy-bgimg") or "",
        el.get("class") and " ".join(el.get("class")) or "",
        el.get("alt") or "",
        el.get("id") or "",
    ])
    if "mmbiz_svg" in blob or "we-emoji" in blob:
        return True
    return bool(DECORATIVE_IMG_RE.search(blob))


def resolve_img_src(el):
    """取出图片真实地址。跳过 data: 占位图,优先懒加载属性。"""
    for attr in IMG_SRC_ATTRS:
        val = (el.get(attr) or "").strip()
        if not val or val.startswith("data:"):
            continue
        if "placeholder" in val.lower():
            continue
        return val
    return ""


def prepare_weixin_content(content_el):
    """公众号正文预处理:把懒加载图变成普通 img,丢掉文末推荐块。"""
    for el in list(content_el.select("[data-lazy-bgimg]")):
        url = (el.get("data-lazy-bgimg") or "").strip()
        text = el.get_text(strip=True)
        if (not url) or WEIXIN_FOOTER_RE.match(text) or "mmbiz_svg" in url:
            if WEIXIN_FOOTER_RE.match(text):
                el.decompose()
            continue
        if not el.find("img"):
            img = content_el.new_tag("img", src=url)
            el.insert(0, img)
    for img in content_el.find_all("img"):
        src = resolve_img_src(img)
        if src:
            img["src"] = src
    return content_el


def drop_decorative_images(content_el):
    """从正文 DOM 里去掉装饰图,返回删除数量。"""
    removed = 0
    for img in list(content_el.find_all("img")):
        if is_decorative_image(img):
            img.decompose()
            removed += 1
    return removed


def detect_language(el):
    """从 <pre>/<code> 的 class 中识别编程语言,供围栏代码块标注。

    兼容 highlight.js / prismjs 风格:language-xxx、lang-xxx、hljs-xxx。
    """
    candidates = [el]
    code = el.find("code") if el.name == "pre" else None
    if code is not None:
        candidates.append(code)
    ignore = {"hljs", "prism", "highlight", "prettyprint", "linenums", "code"}
    for node in candidates:
        for cls in node.get("class", []) or []:
            low = cls.lower()
            for prefix in ("language-", "lang-", "brush:"):
                if low.startswith(prefix):
                    lang = low[len(prefix):].strip(" :")
                    if lang:
                        return lang
            if low.startswith("code-snippet__") and low != "code-snippet__fix":
                # 公众号代码块: class="code-snippet__js"
                lang = low.split("__", 1)[-1]
                if lang and lang not in {"fix", "nowrap"}:
                    return lang
            if low not in ignore and re.fullmatch(r"[a-z0-9+#-]+", low):
                # 形如 class="python" 的直接语言标注
                if low not in {"line", "number", "numbers", "ln"}:
                    return low
    return ""


class WebConverter(MarkdownConverter):
    """自定义转换器:补全图片地址、可选下载图片到本地。"""

    def __init__(self, base_url="", downloader=None, **options):
        super().__init__(**options)
        self.base_url = base_url
        self.downloader = downloader  # 可调用对象: (abs_url) -> 本地相对路径

    def convert_img(self, el, text, parent_tags):
        # 兼容懒加载:公众号/CSDN 的真实地址在 data-src,src 经常是 1x1 占位图
        src = resolve_img_src(el)
        if not src:
            return ""
        src = urljoin(self.base_url, src.strip())
        alt = (el.get("alt") or "").replace("\n", " ").strip()
        title = el.get("title")
        if self.downloader is not None:
            local = self.downloader(src)
            if local:
                src = local
        title_part = ' "%s"' % title.replace('"', "") if title else ""
        return "![%s](%s%s)" % (alt, src, title_part)


class ImageDownloader:
    """下载图片到指定目录,返回相对路径;同一 URL 只下载一次。"""

    def __init__(self, img_dir, base_dir, session, page_url=""):
        self.img_dir = img_dir
        self.base_dir = base_dir
        self.session = session
        self.page_url = page_url
        self.cache = {}
        self.seq = 0
        os.makedirs(img_dir, exist_ok=True)

    def __call__(self, url):
        if url in self.cache:
            return self.cache[url]
        try:
            resp = self.session.get(
                url, headers=image_headers(url, self.page_url), timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # 下载失败则保留原始网络地址,不中断整体转换
            print("  [警告] 图片下载失败,保留原链接: %s (%s)" % (url, exc),
                  file=sys.stderr)
            self.cache[url] = url
            return url
        ext = self._guess_ext(url, resp.headers.get("Content-Type", ""))
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        self.seq += 1
        name = "img_%03d_%s%s" % (self.seq, digest, ext)
        path = os.path.join(self.img_dir, name)
        with open(path, "wb") as fh:
            fh.write(resp.content)
        rel = os.path.relpath(path, self.base_dir).replace(os.sep, "/")
        self.cache[url] = rel
        return rel

    @staticmethod
    def _guess_ext(url, content_type):
        path = urlparse(url).path
        ext = os.path.splitext(unquote(path))[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"):
            return ext
        # 公众号图片常写成 /0?wx_fmt=jpeg,路径没有后缀
        qs = urlparse(url).query
        m = re.search(r"wx_fmt=([a-zA-Z0-9]+)", qs)
        if m:
            fmt = m.group(1).lower()
            if fmt == "jpeg":
                return ".jpg"
            if fmt in ("png", "jpg", "gif", "webp", "bmp"):
                return "." + fmt
        guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
        return guessed or ".png"


def _tidy(body_md, title):
    """清理转换后 Markdown 的常见噪声(不触碰代码块内部)。

    - 删除 CSDN 用作空段落的零宽字符(U+200B/200D/FEFF)行;
    - 删除与文章标题完全重复的开头标题行;
    - 压缩多余空行。
    """
    out_lines = []
    in_fence = False
    title_norm = title.strip()
    title_dropped = False
    for ln in body_md.splitlines():
        if re.match(r"^\s*`{3,}", ln):
            in_fence = not in_fence
            out_lines.append(ln)
            continue
        if not in_fence:
            # 去掉零宽字符后若整行为空,则视为噪声行丢弃
            stripped = ln.translate({0x200b: None, 0x200d: None, 0xfeff: None}).strip()
            if not stripped and ln.strip():
                continue
            # 丢弃正文开头与标题重复的一级/二级标题
            if not title_dropped:
                m = re.match(r"^#{1,3}\s+(.*)$", ln.strip())
                if m and m.group(1).strip() == title_norm:
                    title_dropped = True
                    continue
                if stripped:
                    title_dropped = True  # 出现实质内容后不再尝试去重标题
        out_lines.append(ln)
    text = "\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert(url, download_images=False, img_dir=None, out_path=None):
    """主流程:抓取 -> 定位正文 -> 清洗 -> 转 Markdown。

    返回 dict,方便批量模式写清单;失败时抛出异常。
    """
    session = requests.Session()
    print("抓取页面: %s" % url)
    warmup(session, url)
    html = fetch(url, session)
    soup = BeautifulSoup(html, "lxml")
    host = urlparse(url).netloc

    title = find_title(soup, host)
    author, author_label = find_author(soup, host)
    content = find_content(soup, host)
    if content is None:
        raise RuntimeError("未能定位正文容器,页面结构可能不受支持")
    clean(content)
    if is_weixin(host):
        prepare_weixin_content(content)
    skipped_img = drop_decorative_images(content)

    n_img = len(content.find_all("img"))
    n_pre = len(content.find_all("pre"))
    print("正文定位成功: 图片 %d 张(另跳过装饰图 %d), 代码块 %d 个"
          % (n_img, skipped_img, n_pre))
    if author:
        print("来源: %s %s" % (author_label, author))

    downloader = None
    if download_images:
        base_dir = os.path.dirname(os.path.abspath(out_path)) if out_path else os.getcwd()
        img_dir = img_dir or os.path.join(base_dir, "images")
        downloader = ImageDownloader(img_dir, base_dir, session, page_url=url)

    converter = WebConverter(
        base_url=url,
        downloader=downloader,
        heading_style="ATX",          # 用 # 形式的标题
        code_language_callback=detect_language,
        bullets="-",
    )
    body_md = converter.convert_soup(content).strip()
    body_md = _tidy(body_md, title)

    meta = ["> 原文链接: %s" % url]
    if author:
        meta.append("> %s: %s" % (author_label, author))
    md = rewrite_md_image_paths("# %s\n\n%s\n\n%s\n" % (title, "\n".join(meta), body_md))

    downloaded = downloader.seq if downloader is not None else 0
    if downloader is not None:
        print("已下载图片 %d 张到: %s" % (downloaded, downloader.img_dir))

    return {
        "title": title,
        "markdown": md,
        "url": url,
        "images_kept": n_img,
        "images_skipped": skipped_img,
        "images_downloaded": downloaded,
        "code_blocks": n_pre,
        "located": True,
    }


def safe_filename(name):
    """把标题转成安全的文件夹名。

    必须去掉 ? 和全角 ？： 等符号。Markdown 预览会把路径当 URL,
    问号后面的 images/xxx.png 会被当成查询串,图片全部裂开。
    """
    repl = {
        "？": "", "?": "",
        "：": "-", ":": "-",
        "、": "-",
        "，": "-",
        "。": "",
        "！": "",
        "《": "", "》": "",
        "（": "(", "）": ")",
        "/": "-", "\\": "-",
        "*": "", '"': "", "<": "", ">": "", "|": "",
    }
    for src, dst in repl.items():
        name = name.replace(src, dst)
    name = re.sub(r"\s+", "-", name).strip()
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return (name or "article")[:80]


def rewrite_md_image_paths(md_text):
    """把 ](images/ 改成 ](./images/ ,方便编辑器按当前文件定位图片。"""
    return re.sub(r"\]\((?!https?://|\./|#)(images/)", r"](./\1", md_text)


def write_preview_html(md_path, title=""):
    """把 Markdown 转成可双击打开的 preview.html,浏览器一定能显示本地图片。"""
    return _write_preview_html_from_md(os.path.abspath(md_path), title)


def _write_preview_html_from_md(md_path, title=""):
    """真正写 preview.html:按行处理,代码块原样保留,图片变成 <img>。"""
    text = open(md_path, "r", encoding="utf-8").read()
    text = rewrite_md_image_paths(text)
    lines = text.splitlines()
    out = []
    in_fence = False
    fence_buf = []
    fence_lang = ""
    i = 0

    def esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def flush_para(buf):
        if not buf:
            return
        out.append("<p>%s</p>" % "<br>\n".join(buf))
        buf.clear()

    para = []
    while i < len(lines):
        ln = lines[i]
        fence = re.match(r"^```(\w*)\s*$", ln)
        if fence:
            flush_para(para)
            if not in_fence:
                in_fence = True
                fence_lang = fence.group(1)
                fence_buf = []
            else:
                out.append('<pre><code class="language-%s">%s</code></pre>'
                           % (esc(fence_lang), esc("\n".join(fence_buf))))
                in_fence = False
            i += 1
            continue
        if in_fence:
            fence_buf.append(ln)
            i += 1
            continue

        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", ln)
        if img:
            flush_para(para)
            out.append('<p><img src="%s" alt="%s"></p>'
                       % (img.group(2).replace('"', ""),
                          img.group(1).replace('"', "")))
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush_para(para)
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, esc(m.group(2)), level))
            i += 1
            continue

        if ln.startswith("> "):
            flush_para(para)
            quote = [ln[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:])
                i += 1
            out.append("<blockquote>%s</blockquote>" % esc(" ".join(quote)))
            continue

        if re.match(r"^\|.*\|$", ln) and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            flush_para(para)
            rows = [ln]
            i += 1
            i += 1  # skip separator
            while i < len(lines) and re.match(r"^\|.*\|$", lines[i]):
                rows.append(lines[i])
                i += 1
            table = ["<table>"]
            for idx, row in enumerate(rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if idx == 0 else "td"
                table.append("<tr>" + "".join("<%s>%s</%s>" % (tag, esc(c), tag) for c in cells) + "</tr>")
            table.append("</table>")
            out.append("\n".join(table))
            continue

        if re.match(r"^[-*]\s+", ln) or re.match(r"^\d+\.\s+", ln):
            flush_para(para)
            items = []
            ordered = bool(re.match(r"^\d+\.\s+", ln))
            while i < len(lines) and (re.match(r"^[-*]\s+", lines[i]) or re.match(r"^\d+\.\s+", lines[i])):
                items.append(re.sub(r"^([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (
                tag,
                "".join("<li>%s</li>" % esc(x) for x in items),
                tag))
            continue

        if not ln.strip():
            flush_para(para)
            i += 1
            continue

        # 行内图片
        def inline_img(m):
            return '<img src="%s" alt="%s">' % (
                m.group(2).replace('"', ""), m.group(1).replace('"', ""))

        rendered = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", inline_img, ln)
        # 粗体/行内代码做一点简单处理
        rendered = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % esc(m.group(1)), rendered)
        rendered = re.sub(r"\*\*([^*]+)\*\*", lambda m: "<strong>%s</strong>" % m.group(1), rendered)
        para.append(rendered)
        i += 1

    flush_para(para)
    if not title:
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else "article"
    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
body{max-width:860px;margin:32px auto;padding:0 20px 64px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;line-height:1.75;color:#222;}
img{max-width:100%%;height:auto;display:block;margin:16px 0;border-radius:6px;}
pre{background:#f6f8fa;padding:12px 16px;overflow:auto;border-radius:6px;}
code{font-family:ui-monospace,Consolas,monospace;font-size:0.92em;}
pre code{font-size:0.88em;}
table{border-collapse:collapse;width:100%%;margin:12px 0;}
th,td{border:1px solid #ddd;padding:6px 10px;text-align:left;}
th{background:#f6f8fa;}
blockquote{margin:12px 0;padding:4px 12px;border-left:4px solid #ddd;color:#555;}
h1,h2,h3{line-height:1.35;}
</style>
</head>
<body>
%s
</body>
</html>
""" % (esc(title), "\n".join(out))
    html_path = os.path.join(os.path.dirname(md_path), "preview.html")
    write_text(html_path, page)
    return html_path


def read_urls_file(path):
    """从文本文件读取链接:每行一个,忽略空行和 # 注释。"""
    urls = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # 允许 "标题<空格或制表符>URL" 这种两列写法,取最后一个 http 开头的字段
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line.split()[0])
            else:
                parts = line.split()
                http_parts = [p for p in parts if p.startswith("http://") or p.startswith("https://")]
                if http_parts:
                    urls.append(http_parts[-1])
    return urls


def collect_urls(cli_urls, urls_file):
    """合并命令行链接和文件里的链接,去重但保持顺序。"""
    urls = []
    if urls_file:
        urls.extend(read_urls_file(urls_file))
    urls.extend(cli_urls or [])
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def write_text(path, text):
    """写出 UTF-8 文本,自动创建父目录。"""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def convert_one(url, article_dir, download_images=True):
    """转换单篇,写入 article_dir/raw.md 和 images/。失败不抛到外层。"""
    os.makedirs(article_dir, exist_ok=True)
    raw_path = os.path.join(article_dir, "raw.md")
    img_dir = os.path.join(article_dir, "images")
    try:
        result = convert(
            url,
            download_images=download_images,
            img_dir=img_dir if download_images else None,
            out_path=raw_path,
        )
        write_text(raw_path, rewrite_md_image_paths(result["markdown"]))
        preview = write_preview_html(raw_path, result["title"])
        print("已写出: %s (%d 字符)" % (raw_path, len(result["markdown"])))
        print("预览页: %s  (用浏览器打开才能稳定看到图片)" % preview)
        return {
            "ok": True,
            "url": url,
            "title": result["title"],
            "dir": article_dir,
            "raw": raw_path,
            "images_dir": img_dir if download_images else None,
            "images_kept": result["images_kept"],
            "images_skipped": result["images_skipped"],
            "images_downloaded": result["images_downloaded"],
            "code_blocks": result["code_blocks"],
            "error": None,
        }
    except Exception as exc:
        print("[错误] %s: %s" % (url, exc), file=sys.stderr)
        write_text(os.path.join(article_dir, "error.txt"), str(exc) + "\n")
        return {
            "ok": False,
            "url": url,
            "title": None,
            "dir": article_dir,
            "raw": None,
            "images_dir": None,
            "images_kept": 0,
            "images_skipped": 0,
            "images_downloaded": 0,
            "code_blocks": 0,
            "error": str(exc),
        }


def default_out_dir():
    """批量输出目录默认名,带时间戳避免互相覆盖。"""
    return "articles_%s" % datetime.now().strftime("%Y%m%d_%H%M%S")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="把一篇或多篇网页转成 Markdown,保留正文图片与代码块。")
    parser.add_argument("urls", nargs="*", help="文章网页地址,可写多个")
    parser.add_argument("-f", "--urls-file",
                        help="从文本文件读取链接(每行一个,支持 # 注释)")
    parser.add_argument("-o", "--output",
                        help="单篇时的输出 .md 路径;多篇时忽略,请用 -d")
    parser.add_argument("-d", "--out-dir",
                        help="输出目录。多篇时每篇文章一个子目录;单篇未指定 -o 时也用它")
    parser.add_argument("--download-images", action="store_true",
                        help="下载图片到本地并改写为相对路径(归档推荐打开)")
    parser.add_argument("--no-download-images", action="store_true",
                        help="不下载图片,正文里保留原始网络地址")
    parser.add_argument("--img-dir",
                        help="单篇模式的图片目录(默认:输出文件同级的 images/)")
    args = parser.parse_args(argv)

    urls = collect_urls(args.urls, args.urls_file)
    if not urls:
        parser.error("请至少提供一个 URL,或用 -f 指定链接文件")

    download_images = True
    if args.no_download_images:
        download_images = False
    elif args.download_images:
        download_images = True
    # 批量归档默认下载图片;单篇且显式 -o 时保持旧行为(需加 --download-images)
    if len(urls) == 1 and args.output and not args.download_images and not args.no_download_images:
        download_images = False

    # ----- 单篇 + 指定文件:兼容旧用法 -----
    if len(urls) == 1 and args.output and not args.out_dir:
        out_path = args.output
        result = convert(
            urls[0],
            download_images=download_images,
            img_dir=args.img_dir,
            out_path=out_path,
        )
        write_text(out_path, rewrite_md_image_paths(result["markdown"]))
        print("已写出: %s (%d 字符)" % (out_path, len(result["markdown"])))
        print("预览页: %s" % write_preview_html(out_path, result["title"]))
        return 0

    # ----- 统一目录模式(单篇或多篇) -----
    out_dir = args.out_dir or (os.path.dirname(os.path.abspath(args.output)) if args.output else None)
    if not out_dir:
        out_dir = default_out_dir() if len(urls) > 1 else os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    items = []
    width = max(2, len(str(len(urls))))
    for idx, url in enumerate(urls, 1):
        print("\n==== [%d/%d] ====" % (idx, len(urls)))
        # 先用序号占位目录,转换成功后再尽量带上标题缩写,方便人眼查找
        slug_dir = os.path.join(out_dir, "%0*d" % (width, idx))
        item = convert_one(url, slug_dir, download_images=download_images)
        if item["ok"] and item["title"]:
            pretty = "%0*d-%s" % (width, idx, safe_filename(item["title"]))
            pretty_dir = os.path.join(out_dir, pretty)
            if pretty_dir != slug_dir and not os.path.exists(pretty_dir):
                os.rename(slug_dir, pretty_dir)
                item["dir"] = pretty_dir
                item["raw"] = os.path.join(pretty_dir, "raw.md")
                if item["images_dir"]:
                    item["images_dir"] = os.path.join(pretty_dir, "images")
        items.append(item)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": os.path.abspath(out_dir),
        "count": len(items),
        "ok": sum(1 for i in items if i["ok"]),
        "failed": sum(1 for i in items if not i["ok"]),
        "articles": items,
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("\n清单: %s  (成功 %d / 共 %d)"
          % (manifest_path, manifest["ok"], manifest["count"]))
    return 0 if manifest["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
