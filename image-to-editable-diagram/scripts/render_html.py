#!/usr/bin/env python3
"""把生成的 HTML 图表渲染成 PNG，用于自检排版（遮挡/溢出/错位）。

用法：
    python3 render_html.py diagram.html                 # 输出 diagram.png
    python3 render_html.py diagram.html --out check.png --width 1520 --height 1160

依赖 playwright（首次需装浏览器）：
    pip install playwright --break-system-packages
    python3 -m playwright install chromium

若环境无法安装无头浏览器，脚本会给出提示并退出；
此时可让用户在本地浏览器打开 HTML 自行核对，或用 --width/--height 说明画布尺寸。
渲染出的 PNG 应与原参考图并排对照：文字、箭头方向、虚实线、颜色是否一致。
"""
import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="渲染 HTML 图表为 PNG 以自检")
    ap.add_argument("html", help="HTML 文件路径")
    ap.add_argument("--out", default="", help="输出 PNG，默认与 HTML 同名")
    ap.add_argument("--width", type=int, default=1600, help="视口宽度")
    ap.add_argument("--height", type=int, default=1200, help="视口高度")
    ap.add_argument("--full", action="store_true", default=True,
                    help="整页截图（默认开启）")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print(f"找不到 HTML：{args.html}", file=sys.stderr)
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("未安装 playwright。请执行：", file=sys.stderr)
        print("  pip install playwright --break-system-packages", file=sys.stderr)
        print("  python3 -m playwright install chromium", file=sys.stderr)
        print("（若环境禁止安装，请让用户在本地浏览器打开 HTML 核对排版。）",
              file=sys.stderr)
        return 2

    out = args.out or os.path.splitext(os.path.abspath(args.html))[0] + ".png"
    url = "file://" + os.path.abspath(args.html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": args.width, "height": args.height},
                                    device_scale_factor=2)
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=out, full_page=args.full)
            browser.close()
    except Exception as e:  # noqa: BLE001
        print(f"渲染失败：{e}", file=sys.stderr)
        print("（可能缺少浏览器，执行 python3 -m playwright install chromium）",
              file=sys.stderr)
        return 2

    print(f"已渲染：{out}")
    print("下一步：用 Read 查看该 PNG，与原参考图逐项对照（文字/箭头/虚实线/颜色）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
