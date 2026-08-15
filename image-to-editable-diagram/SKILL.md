---
name: image-to-editable-diagram
description: "将架构图、流程图、时序图等参考图片转换为可编辑的专业格式（HTML/SVG、Mermaid、PPTX）。适用于：根据图片还原架构、把截图/草图变成可编辑技术文档、优化现有图表排版。"
---

# Image to Editable Diagram

把不可编辑的参考图（截图、草图、低清图）转换为高质量、可编辑的结构化图表。
核心目标：**100% 还原文字与逻辑**，并输出**源码级可编辑**的成果，而非再生成一张图片。

## 工作流程

### 第 1 步：精确读图（强制，不可跳过）
低分辨率或文字密集的图，**直接整图识别极易整体看错主题、漏字**。因此：

1. 先查看整图，建立全局印象。
2. **必须**用脚本分区放大后逐块精读：
   ```bash
   python3 scripts/prepare_image.py <图片> --grid 3x3 --scale 3
   ```
   （文字很密时用 `--grid 4x3 --scale 4`，或用 `--regions` 指定关键区域。）
3. 用 Read 工具逐块查看 `_zoom/` 下的放大图，抄录每一块文字。
4. 看不清就继续放大——**绝不猜测填充**。

### 第 2 步：结构化提取
把读到的内容整理成清单（供后续绘制核对）：
- 标题与副标题
- 所有模块/节点文本 + 括号补充说明
- 层级与分组（虚线域=预留/逻辑，实线域=物理实体）
- 连接关系：方向、**实线/虚线**、颜色分组、线上标签、步骤编号
- 图例与配色方案

### 第 3 步：选择输出格式
按用户对「保真度」与「可编辑性」的需求路由：

| 需求 | 推荐方案 | 做法 | 参考 |
| :--- | :--- | :--- | :--- |
| **高保真还原 + 演示级美观**（首选） | **HTML + SVG 单文件** | 绝对定位盒子 + SVG 连线，自包含、可打印 PDF | `references/html_svg_guide.md` |
| **快速逻辑迭代 / 文本驱动** | **Mermaid** | 写 `.mmd` 源码，diff 友好 | `references/mermaid_guide.md` |
| **需要真正的 PPTX 文件** | **python-pptx** | 用 `python-pptx` 生成 `.pptx`（形状+连接符） | 见下方说明 |
| **导入 draw.io / diagrams.net 类编辑器** | **draw.io XML** | 生成 `.drawio`（mxGraph XML），节点+连线均可再编辑 | 见下方说明 |
| **图标化矢量** | **纯 SVG** | 直接写 `.svg`，无限缩放 | — |

> 环境说明：本 skill 面向通用环境（如 Claude Code），**不依赖任何平台专有工具**。
> 优先用 HTML+SVG——它在任何浏览器可打开、可编辑、可导出 PDF，兼顾保真与可编辑。

### 第 4 步：绘制
- **HTML+SVG（首选）**：复制 `templates/diagram_template.html` 起步，
  样式参考 `templates/diagram_styles.css`（改 `:root` 变量即可整体换色）。
  要点：画布尺寸取原图比例；节点绝对定位；SVG `viewBox` 与画布同尺寸使坐标=像素；
  每种颜色定义一个箭头 `marker`；**实线/虚线严格对应原图语义**。
- **Mermaid**：按 `references/mermaid_guide.md` 的语义映射表编写 `.mmd`。
- **PPTX**：`pip install python-pptx`，**直接复用 `scripts/pptx_helpers.py`**——
  它封装了 python-pptx 缺失的能力（中文东亚字体、虚线、连接符箭头、无阴影矢量外观）。
  用 `Diagram` 类的 `box/container/label/multiline/arrow/legend_item` 按原图坐标与配色
  摆放，`save()` 交付 `.pptx`。坐标单位 = 0.01 英寸，先量好各模块相对位置再套用。
  注意：**只把通用图元放进 skill；每张图的具体内容/坐标写在任务目录的一次性脚本里**，
  不要污染 skill。
- **draw.io XML**：**直接复用 `scripts/drawio_helpers.py`**——`Drawio` 类的
  `box/container/text/edge/legend_item` 生成 mxGraph XML，`save()` 输出 `.drawio`。
  坐标单位 = 像素；`edge(源id, 目标id, ...)` 连线会随节点移动而重连。
  交付后告知用户导入方式：编辑器里 `File > Open/Import` 选文件，
  或 `Extras > Edit Diagram` 粘贴 XML（最稳，不受上传限制）。
  同样只放通用图元入 skill，具体内容留任务目录。

### 第 5 步：渲染验证
```bash
python3 scripts/render_html.py <生成的.html>
```
渲染成 PNG 后用 Read 查看，与原参考图**并排对照**。
若环境无法安装无头浏览器，请让用户在本地浏览器打开 HTML 自检。

### 第 6 步：质量检查
对照 `references/quality_checklist.md` 逐项确认：读图准确性、逻辑一致性、
排版无遮挡、交付为可编辑源码。**交付前清理 `_zoom/` 等中间产物。**

## 资源清单
- `scripts/prepare_image.py` — 分区裁剪+放大，用于精确读图。
- `scripts/render_html.py` — HTML→PNG 渲染自检。
- `scripts/pptx_helpers.py` — 生成可编辑 PPTX 的通用图元库（`Diagram` 类）。
- `scripts/drawio_helpers.py` — 生成 draw.io/.drawio (mxGraph XML) 的通用图元库（`Drawio` 类）。
- `templates/diagram_template.html` — 单文件 HTML 骨架。
- `templates/diagram_styles.css` — 常用组件样式（盒子/虚线容器/图例/SVG 连线）。
- `references/html_svg_guide.md` — HTML+SVG 高保真绘制技法。
- `references/mermaid_guide.md` — Mermaid 语义映射与图型。
- `references/quality_checklist.md` — 交付前检查清单。

## 注意事项
- **绝不**用 AI 图像生成工具（DALL·E 等）生成架构图——文字不可控、不可编辑。
- 用户要「可编辑」时，务必交付**源码/Office 格式**，不要只给图片。
- 忠实还原优先于美化：先保证文字、方向、虚实线、分组全部正确，再谈排版美观。
