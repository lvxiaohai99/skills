---
name: web-to-markdown
description: >-
  把一篇或多篇网络文章抓成带图的本地 Markdown，再整理成干净、有章节逻辑的标准文档。
  特别支持微信公众号（mp.weixin.qq.com）和 CSDN，也覆盖博客园、掘金、知乎专栏等。
  当用户说「把这个链接存成 md」「抓几篇博客落地」「归档网页文章」「把 URL 转成笔记」
  「保存公众号文章」「抓 CSDN」「去掉网页杂质只留正文和配图」时必须使用本 skill。
  即使用户只丢了若干 http(s) 链接、没提 markdown，只要意图是保存/阅读/整理网页文章，也要用它，
  不要手写临时抓取脚本，也不要只用浏览器可读接口丢掉图片。
---

# 网页文章 → 本地标准 Markdown

两步走，缺一不可：

1. **脚本落地**：把链接抓成 `raw.md`，正文配图下载到 `images/`。
2. **模型整理**：按 `references/polish_guide.md` 写成 `article.md`，去掉网页杂质，理顺章节，**配图和代码都留下**。

脚本不会替你「写好文章」。`raw.md` 只是原料。

## 第 1 步：收集链接、定输出位置

- 用户消息、附件、`urls.txt` 里所有 `http://` / `https://` 都算一篇。
- 去重，保持用户给出的顺序。
- 输出目录：用户指定了就用指定的；否则用当前工作目录下的 `articles/`。
  若用户正在某个任务子目录里，就放那个子目录，不要写到 skill 自己的文件夹。
- 多篇默认**一篇一个子目录**。只有用户明确说「合成一篇」时，才在各自整理完之后再合并。

## 第 2 步：跑抓取脚本

统一走 `scripts/run.sh`。`$SKILL_DIR` 是本 skill 根目录（本文件所在目录）。首次会自动建虚拟环境，稍慢一次。

**多个链接（推荐）：**

```bash
bash "$SKILL_DIR/scripts/run.sh" \
  "https://example.com/a" \
  "https://example.com/b" \
  -d <输出目录>
```

**从文件读链接：**

```bash
bash "$SKILL_DIR/scripts/run.sh" -f <urls.txt> -d <输出目录>
```

**只要一篇，并且用户点名了文件名：**

```bash
bash "$SKILL_DIR/scripts/run.sh" "<url>" -o <文件.md> --download-images
```

批量模式默认就会下载图片。不要加 `--no-download-images`，除非用户只要网上的图片地址。

脚本会打印：每篇是否定位到正文、保留/跳过的图片数、代码块数、`manifest.json` 路径。

## 第 3 步：整理成标准 md

对 `manifest.json` 里 `ok: true` 的每一篇：

1. 读该目录的 `raw.md`。
2. 打开 `references/polish_guide.md`，按里面的「必须保留 / 必须丢掉 / 标准版式」改写。
3. 写成**同目录**的 `article.md`，不要覆盖 `raw.md`，不要改 `images/` 里的文件名。
4. 对照检查：
   - 文首仍有原文链接
   - `raw.md` 里的正文配图在 `article.md` 里都还在（路径写成 `./images/...`，不要用网上的地址）
   - 用脚本再生成一次预览：把 `article.md` 交给 `write_preview_html`，或再跑一遍整理后用浏览器打开 `preview.html` 核对配图。Cursor 里直接看 md **经常看不到本地图片**，这不是图丢了。
   - 代码块没有变少、没有被改坏
   - 没有推荐栏、关注按钮、评论区残留

失败的篇目（`ok: false`）向用户说明原因：站点要登录、纯前端渲染、公众号验证码、或选择器没命中。不要假装抓到了。

## 公众号和 CSDN

脚本已经按站点做了专项处理，**不要**再手写另一套抓取：

- **公众号** `mp.weixin.qq.com`：桌面浏览器头（不要用手机微信 UA）、正文 `#js_content`、图片走 `data-src`、下载带微信 Referer。文首会带「公众号: 名称」。整理时丢掉关注/在看/赞赏/二维码/往期推荐。
- **CSDN** `blog.csdn.net`：正文 `#content_views`，先访问首页减 521。整理时丢掉版权套话、相关推荐、关注作者。

若公众号报「触发了访问验证」，告诉用户稍后再试，或请他用浏览器打开后把全文贴过来。

## 导入语雀

用户要「自动导入语雀」时：

1. **Chrome 插件（推荐）**：`normal_process/save_web_to_md/chrome-extension/`  
   打开文章页一点即可抓正文+图写入语雀（用浏览器登录态）。
2. **命令行**：`normal_process/save_web_to_md/yuque_import.py`  
   Token 只让用户自己写进 `yuque.local.json` 或环境变量 `YUQUE_TOKEN`，**不要让用户把 Token 发到对话里**。  
   要带图可再填 Cookie；或提醒用语雀网页「导入 Markdown」选 zip。

先 `whoami` / `repos` 确认知识库 `namespace`，再 `push` / `push-dir`。

## 第 4 步：向用户交代

用几句人话汇报，不要丢一堆路径了事：

- 成功几篇、失败几篇
- 每篇：标题、`article.md` 路径、配图张数、代码块数量
- 失败的链接和原因
- 多篇时，输出目录根下再写一份简短 `README.md` 当目录

## 适配新站点

正文/标题选择器在 `scripts/web_to_md.py` 顶部的 `SITE_RULES`。某个站反复抓偏时，按域名加一条：

```python
SITE_RULES = {
    "example.com": {
        "content": ["article.post", "#main-content"],
        "title":   ["h1.post-title"],
    },
}
```

## 局限

- 只抓服务端渲染的 HTML。内容必须跑 JS 才出现时，脚本会报定位失败或图片/代码为 0。这时如实告诉用户，需要的话再改用无头浏览器。
- 登录墙、反爬可能导致正文残缺。可请用户导出已登录的 HTML，或换可公开访问的地址。
