#!/usr/bin/env python3
"""分区裁剪 + 放大参考图，便于「精确读图」。

低分辨率或文字密集的架构图，直接整图查看极易看错/漏字。
本脚本把图片切成带重叠的网格（或自定义区域），逐块放大后另存，
供视觉工具逐块精读，确保 100% 还原文字。

用法：
    # 默认 3x3 网格、放大 3 倍
    python3 prepare_image.py path/to/diagram.png

    # 自定义网格与倍数
    python3 prepare_image.py diagram.png --grid 4x3 --scale 4

    # 自定义区域（像素坐标 left,top,right,bottom，多个用分号分隔）
    python3 prepare_image.py diagram.png --regions "title:0,0,1536,90;tree:0,300,330,760"

输出：在图片同目录下的 `_zoom/` 子目录，打印每块的路径与尺寸。
之后用 Read 工具逐块查看这些放大图。
"""
import argparse
import os
import sys


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print("需要 Pillow：pip install Pillow --break-system-packages", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description="分区裁剪并放大参考图")
    ap.add_argument("image", help="参考图片路径")
    ap.add_argument("--grid", default="3x3", help="网格 行x列，默认 3x3")
    ap.add_argument("--scale", type=int, default=3, help="放大倍数，默认 3")
    ap.add_argument("--overlap", type=float, default=0.12,
                    help="相邻块重叠比例，避免文字被切断，默认 0.12")
    ap.add_argument("--regions", default="",
                    help="自定义区域 name:l,t,r,b 用分号分隔（提供则忽略 --grid）")
    ap.add_argument("--outdir", default="", help="输出目录，默认 <图片目录>/_zoom")
    args = ap.parse_args()

    if not os.path.isfile(args.image):
        print(f"找不到图片：{args.image}", file=sys.stderr)
        return 1

    im = Image.open(args.image).convert("RGB")
    W, H = im.size
    outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(args.image)), "_zoom")
    os.makedirs(outdir, exist_ok=True)

    regions = []  # (name, l, t, r, b)
    if args.regions.strip():
        for part in args.regions.split(";"):
            part = part.strip()
            if not part:
                continue
            name, coords = part.split(":")
            l, t, r, b = (int(x) for x in coords.split(","))
            regions.append((name.strip(), l, t, r, b))
    else:
        try:
            rows, cols = (int(x) for x in args.grid.lower().split("x"))
        except ValueError:
            print("--grid 格式应为 行x列，例如 3x3", file=sys.stderr)
            return 1
        cw, ch = W / cols, H / rows
        ox, oy = int(cw * args.overlap), int(ch * args.overlap)
        for ri in range(rows):
            for ci in range(cols):
                l = max(0, int(ci * cw) - ox)
                t = max(0, int(ri * ch) - oy)
                r = min(W, int((ci + 1) * cw) + ox)
                b = min(H, int((ri + 1) * ch) + oy)
                regions.append((f"r{ri}c{ci}", l, t, r, b))

    print(f"原图 {W}x{H} -> 输出目录 {outdir}")
    for name, l, t, r, b in regions:
        crop = im.crop((l, t, r, b))
        crop = crop.resize((crop.width * args.scale, crop.height * args.scale),
                           Image.LANCZOS)
        path = os.path.join(outdir, f"zoom_{name}.png")
        crop.save(path)
        print(f"  {path}  ({crop.width}x{crop.height})  <= 原区域 {l},{t},{r},{b}")

    print("\n下一步：用 Read 工具逐块查看上述放大图，精确抄录每一块的文字。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
