#!/usr/bin/env python3
"""生成 draw.io / diagrams.net (mxGraph XML) 图表的通用图元库。

产出 .drawio 文件，可导入 diagrams.net、next-ai-drawio 等 draw.io 内核编辑器
（File > Open/Import，或 Extras > Edit Diagram 粘贴 XML）。导入后每个模块都是
独立可编辑对象。坐标单位 = draw.io 像素，直接按原图相对位置摆放即可。

关键坑（本库已处理）：
  - draw.io 的 value 属性即使含 HTML（<br>/<b>/<font>），整个属性值也必须做
    XML 转义（< -> &lt; 等），draw.io 读入后会自行还原再按 html=1 渲染。
    -> 值内用「原始 HTML」构造，emit 时统一 esc()，切勿只转义纯文本部分。

用法示例：
    from drawio_helpers import Drawio, BLUE, GREEN, L_BLUE, L_GREEN, INK
    d = Drawio()
    d.text(0, 8, 1200, 40, "标题", INK, size=20, bold=True, align="center")
    d.container(90, 55, 600, 120, BLUE, dashed=True)          # 预留域(虚线)
    a = d.box(120, 80, 180, 60, "模块A", fill=L_BLUE, stroke=BLUE, bold=True)
    b = d.box(400, 80, 200, 60, d.val("模块B", "(说明)"), fill=L_GREEN, stroke=GREEN)
    d.edge(a, b, color=GREEN, label="流转", dashed=True)
    d.legend_item(90, 220, "蓝色通道", BLUE)
    d.save("out.drawio")
"""

# ---------- 常用配色（按图例增删） ----------
BLUE, GREEN, ORANGE, RED, PURPLE = "#2563eb", "#16a34a", "#ea580c", "#dc2626", "#7c3aed"
INK, GRAY = "#1f2937", "#6b7280"
L_BLUE, L_GREEN, L_ORNG, L_RED, L_PURP, L_GRAY = \
    "#eff6ff", "#f0fdf4", "#fff7ed", "#fef2f2", "#f5f3ff", "#fafafa"
# 深色文字（描边同色系的可读文字色）
BLUE_INK, GREEN_INK, ORNG_INK, RED_INK, PURP_INK = \
    "#1e3a8a", "#166534", "#9a3412", "#7f1d1d", "#5b21b6"


def _esc(s):
    """XML 属性值转义（HTML 标签一并转义，draw.io 会自行还原）。"""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


class Drawio:
    """一页式 draw.io 图。坐标单位 = 像素。"""

    def __init__(self, page_w=1350, page_h=820, name="Diagram"):
        self.name = name
        self.page_w, self.page_h = page_w, page_h
        self.cells = []
        self._n = 1

    def _nid(self):
        self._n += 1
        return f"n{self._n}"

    @staticmethod
    def val(main, sub=None, sub_color=GRAY, sub_size=9):
        """构造带灰色小字副标题的原始 HTML 值（未转义，交给 box/text 处理）。"""
        v = main
        if sub:
            v += (f"<br><font style='font-size:{sub_size}px' "
                  f"color='{sub_color}'>{sub}</font>")
        return v

    # ---- 盒子（圆角矩形顶点） ----
    def box(self, x, y, w, h, value, fill="#ffffff", stroke=INK, fcolor=INK,
            fsize=11, bold=False, dashed=False, rounded=True, align="center",
            valign="middle", mono=False, sw=1.5):
        style = (f"{'rounded=1;' if rounded else 'rounded=0;'}whiteSpace=wrap;html=1;"
                 f"fillColor={fill};strokeColor={stroke};fontColor={fcolor};"
                 f"fontSize={fsize};align={align};verticalAlign={valign};"
                 f"strokeWidth={sw};{'fontStyle=1;' if bold else ''}"
                 f"{'dashed=1;' if dashed else ''}"
                 f"{'fontFamily=Courier New;' if mono else ''}")
        return self._vertex(x, y, w, h, value, style)

    # ---- 分组容器（虚线域/实体域；fill=None 表示透明） ----
    def container(self, x, y, w, h, stroke, dashed=True, fill=None, sw=2.0):
        return self.box(x, y, w, h, "", fill=(fill or "none"), stroke=stroke,
                        dashed=dashed, sw=sw)

    # ---- 纯文字标签（无边框无填充） ----
    def text(self, x, y, w, h, value, color=INK, size=12, bold=True,
             align="left", valign="top", mono=False):
        style = (f"text;html=1;strokeColor=none;fillColor=none;align={align};"
                 f"verticalAlign={valign};whiteSpace=wrap;fontColor={color};"
                 f"fontSize={size};{'fontStyle=1;' if bold else ''}"
                 f"{'fontFamily=Courier New;' if mono else ''}")
        return self._vertex(x, y, w, h, value, style)

    # ---- 带箭头连接符 ----
    def edge(self, src, tgt, color=GRAY, dashed=False, label="", ortho=True, sw=1.75):
        style = (f"edgeStyle={'orthogonalEdgeStyle' if ortho else 'none'};rounded=0;"
                 f"html=1;endArrow=block;endFill=1;strokeColor={color};"
                 f"strokeWidth={sw};fontColor={color};fontSize=9;fontStyle=1;"
                 f"{'dashed=1;' if dashed else ''}")
        i = self._nid()
        self.cells.append(
            f'<mxCell id="{i}" value="{_esc(label)}" style="{style}" edge="1" '
            f'parent="1" source="{src}" target="{tgt}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>')
        return i

    # ---- 图例项（色样细条 + 文字） ----
    def legend_item(self, x, y, text, color, dashed=False, swatch_len=36,
                    text_size=9):
        self.box(x, y + 4, swatch_len, 4, "", fill=color, stroke=color,
                 rounded=False, sw=2, dashed=dashed)
        self.text(x + swatch_len + 6, y, 460, 16, text, "#374151",
                  size=text_size, bold=False)

    # ---- 内部：写入一个顶点 ----
    def _vertex(self, x, y, w, h, value, style):
        i = self._nid()
        self.cells.append(
            f'<mxCell id="{i}" value="{_esc(value)}" style="{style}" vertex="1" '
            f'parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
            f'as="geometry"/></mxCell>')
        return i

    # ---- 输出 ----
    def dumps(self):
        body = "\n        ".join(self.cells)
        return (
            '<mxfile host="app.diagrams.net" type="device">\n'
            f'  <diagram name="{_esc(self.name)}" id="diagram-1">\n'
            '    <mxGraphModel dx="1333" dy="800" grid="1" gridSize="10" guides="1" '
            'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.page_w}" pageHeight="{self.page_h}" math="0" shadow="0">\n'
            '      <root>\n'
            '        <mxCell id="0"/>\n'
            '        <mxCell id="1" parent="0"/>\n'
            f'        {body}\n'
            '      </root>\n'
            '    </mxGraphModel>\n'
            '  </diagram>\n'
            '</mxfile>\n')

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.dumps())
        return path
