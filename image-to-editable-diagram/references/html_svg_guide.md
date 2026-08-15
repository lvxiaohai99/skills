# HTML + SVG 高保真架构图指南

用「绝对定位盒子 + SVG 连线」还原架构图，是本 skill 在通用环境下的**首选方案**：
自包含单文件、任何浏览器可打开、可打印为 PDF、文字与结构 100% 可编辑。

## 1. 画布与坐标系

- `.canvas` 用 `position:relative`，宽高设为原图比例（如原图 1536×1024 → 画布 1520×1160）。
- 所有节点 `position:absolute`，用 `left/top` 定位；尺寸用 `width/height`。
- SVG 连线层覆盖整个画布：`<svg class="wires" viewBox="0 0 W H">`，`viewBox` 与画布同尺寸，
  这样 SVG 坐标 = 像素坐标，节点边缘坐标可直接算出接线点。

> 对齐技巧：先把所有盒子摆好，记下每个盒子的 `left/top/width/height`，
> 连线的起止点就是「起点盒子右边缘中点 → 终点盒子左边缘中点」等，直接套用。

## 2. 箭头（marker）

SVG 箭头必须先在 `<defs>` 里定义 `marker`，每种颜色一个：

```html
<defs>
  <marker id="arrow-blue" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">
    <polygon points="0 0,9 3.5,0 7" fill="#2563eb"/>
  </marker>
</defs>
<path d="M260,120 H360" stroke="#2563eb" stroke-width="2" fill="none" marker-end="url(#arrow-blue)"/>
```

- `refX` 设为接近箭头宽度，让箭尖正好落在线的终点。
- 反向箭头用 `marker-start`；双向就两个都加。
- `orient="auto"` 让箭头自动跟随线的方向。

## 3. 连线类型 = 逻辑语义（务必与原图一致）

| 原图样式 | SVG 写法 | 常见含义 |
| --- | --- | --- |
| 实线 | `stroke-dasharray` 不设 | 已实现 / 数据主流程 |
| 虚线 | `stroke-dasharray="7 5"` | 预留 / 逻辑关系 / 状态回传 |
| 折线（正交） | `d="M x1 y1 H xm V y2 H x2"` | 走线避让、总线 |
| 颜色 | `stroke` 按图例分类 | 不同通道/子系统 |

**颜色要按原图图例分组**（如 Linux=蓝、Android=绿、MCU=橙），并在图例区复述。

## 4. 层级与遮挡

- SVG 连线层与节点谁在上，用 `z-index` 控制。一般：容器背景 < 连线 < 节点盒子。
- 若箭头被盒子压住，或线穿过文字，调整 `z-index` 或让线绕行（正交折线）。
- 盒子间留白，避免边框相接看不清。

## 5. 常见元素配方

- **括号补充说明**：盒子内 `<span class="sub">(说明)</span>`，小字灰色。
- **图标**：用 emoji（🔌🗄️⚖️🖥️📦☁️）零依赖；需要更专业可引 Font Awesome CDN。
- **目录树/代码**：`white-space:pre` + 等宽字体，直接贴文本，保留 `├─ └─` 缩进。
- **分组**：`.dashed-group`（预留/逻辑域）或 `.solid-group`（物理实体），标题用浮动 `.group-title`。
- **图例**：底部 `.legend`，用 `border-top:3px solid/dashed <color>` 画色样。

## 6. 交付前自检

用 `scripts/render_html.py diagram.html` 渲染成 PNG，与原图**并排对照**：
文字有无错漏、箭头方向、虚实线、颜色分组、有无遮挡/溢出。
无法渲染时，让用户在本地浏览器打开核对。
