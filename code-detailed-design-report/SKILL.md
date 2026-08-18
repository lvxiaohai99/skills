---
name: code-detailed-design-report
description: >-
  Generates a Chinese software detailed-design report from specified source
  code: Word (.docx) strictly following a user-specified template, and a
  parallel Markdown with mermaid architecture, sequence, and flow diagrams.
  Use when the user asks for 详细设计报告, 详细设计, 按模板写设计文档, 根据代码生成设计文档,
  SDD, mermaid 详设, 架构图/时序图/流程图, or to fill xxx软件详细设计报告_xxx模块;
  whenever a design template and a code module/path are given together.
---

# 按代码生成详细设计报告

根据**指定代码**写详细设计，**同时**输出：

1. `.docx` — 版式严格遵守用户指定的 Word 模板
2. `.md` — 同一套章节与事实；架构图、时序图、流程图一律 **mermaid**

用户只说「只要 Word」或「只要 Markdown」时才省略另一种。内容只写代码里有的东西，不要编接口、状态机或模块名。

概要设计请用 `code-overview-design-report`，不要用本技能硬塞函数级详设骨架去写 HLD。

`$SKILL_DIR` = 本 skill 根目录。写 Word 时同时读取并遵循 Cursor 的 **docx** 技能（校验、转 PDF、目视截图）。Markdown 图约定见 [references/markdown-mermaid.md](references/markdown-mermaid.md)。

## 输入

从用户消息收集，缺一就问，不要猜模板路径：

| 项 | 说明 |
|----|------|
| 代码范围 | 目录、包名或「按 OTA/某模块实现」；可附架构 md |
| 模板 | `.docx` / `.dotx` 路径，用户指定哪个用哪个 |
| 模块显示名 | 用于封面与第 2 章标题，如 `OTA`、`DVR` |
| 软件名/版本 | 默认软件名取仓库/架构文档；版本默认 `V1.0.0` |
| 输出路径 | 默认仓库根：`<软件名>软件详细设计报告_<模块>模块_<版本>.docx` 与同名 `.md` |

作者/审核/审批未给则留空，只填发布日期（当天）。

## 工作流

```
Task Progress:
- [ ] 1. 解析模板结构
- [ ] 2. 阅读架构文档，核对模块对外名称
- [ ] 3. 阅读指定代码（入口/状态机/接口/协议/文件）
- [ ] 4. 把模板章节映射到代码事实，列出单元与复杂函数
- [ ] 5. 先写 mermaid（边界/静态/时序/流程），再生成 Markdown 详设
- [ ] 6. 由同一套 mermaid 出 PNG，克隆模板生成 docx
- [ ] 7. XSD 校验 + PDF 目视；抽查 md 中 mermaid 可解析
```

### 1. 解析模板

```bash
python "$SKILL_DIR/scripts/inspect_template.py" \
  "<模板.docx>" -o /tmp/sdd_template.json
```

读 JSON：标题层级、表格表头、分页位置、是否有 TOC 域、【模板说明】原文（那是规则，不是正文）。

若模板文件名或「模板说明」匹配中信科 V1.0.2，再读 [references/citc-sdd-v1.0.2.md](references/citc-sdd-v1.0.2.md)，按该骨架填，不要另起章节名。

其他模板：用 inspect 得到的 **Heading 文字** 当骨架；同样删除【模板说明】【示例】。

生成注意点见 [references/docx-ooxml.md](references/docx-ooxml.md)。

### 2. 名称与架构对齐

先读仓库根 `readme.md` / `architecture.md` / 用户点名的架构说明书。边界图里的本模块名、外部模块名必须与架构文档**字面一致**。架构没有的名字不要画成外部模块。

### 3. 从代码抽设计事实

只读用户指定范围内的源码与其直接依赖（协议头文件、daemon、打包脚本）。记录：

- 模块职责与升级/运行模型（A/B、两阶段、主从等）
- 单元划分（按包/职责，一般 5–8 个，对应 2.3 三级标题）
- 对外接口（被 UI/系统/邻模块调用的）与对内接口
- 复杂函数（分支多、协议状态机、跨系统编排）— 这些要画流程图
- 全局/成员变量、关键源文件
- 包格式、端口、魔数、错误码等以代码常量为准

禁止：把模板示例（如 `Fcw::Arithmetic`、V2X）写进交付稿；禁止写代码里标注 TODO 却当成已实现。

### 4. 章节映射

模板有输入/输出 → 按边界图每个外部模块写数据方向。  
模板有单元划分 → 开篇一句「X模块分为N个单元：…」。  
模板要求圈复杂度>7 画流程 → 只给真正复杂的函数上四级标题+图，简单单元用文字。  
模板有 7 行函数表 → 用 `ReportBuilder.func_spec`。

### 5. 先 Markdown + mermaid，再 Word 插图

**先写 `.md`**（与 Word 章节标题一致），图全部用 mermaid 围栏，规范见 [references/markdown-mermaid.md](references/markdown-mermaid.md)。

最低图集（缺一不可，除非该章在模板中不存在）：

- 边界/架构图：`flowchart` + 红黄灰 `classDef`
- 静态结构图：按代码分层的 `flowchart`
- 主路径时序图：`sequenceDiagram`（开机确认等第二路径若代码存在则再画一张）
- 每个 2.3 复杂函数一张 `flowchart`（判定必须有是/否）

把每个图另存 `/tmp/sdd_<模块>/fig_*.mmd`，再渲 PNG 给 Word：

```bash
# 优先 mermaid-cli，保证 Word 插图与 md 同源
command -v mmdc && mmdc -i fig_boundary.mmd -o fig_boundary.png -b white -s 2
```

无 `mmdc` 时用 PIL 按**同一节点和边**重画（不得增删模块）。中文字体 `NotoSansCJK` 或系统宋体。

Markdown 用构建器，不要手拼 YAML/围栏：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$SKILL_DIR") / "scripts"))
from sdd_markdown import MarkdownBuilder

m = MarkdownBuilder(output_md)
m.front_matter(title="…软件详细设计报告_…模块", version="V1.0.0",
               date="YYYY-MM-DD", source_code=["…"], template="…V1.0.2.docx")
m.h("概要", 1)
m.caption("图2-1 …模块边界关系图")
m.mermaid("""flowchart TB
  classDef module fill:#F4CCCC,stroke:#C00000,stroke-width:2px
  ...
""")
m.save()
```

抽图并做语法抽查：

```bash
python "$SKILL_DIR/scripts/extract_mermaid.py" \
  "<output.md>" -o /tmp/sdd_<模块> --render
```

`--render` 在有 `mmdc` 时把每个 `.mmd` 转成 PNG，供 Word 插入。

### 6. 生成 docx

用本技能的构建器，不要从空白文档重做页眉页脚：

```python
import sys
sys.path.insert(0, str(Path("$SKILL_DIR") / "scripts"))
from sdd_docx import ReportBuilder

b = ReportBuilder(template, output)
b.open()
b.cover(title="…软件详细设计报告_…模块", version="V1.0.0", release_date="YYYY-MM-DD")
b.revision_page([["YYYY-MM-DD", "V1.0.0", "", "全部", "根据代码实现首次编制"]])
b.toc_page("目 录", [("1  概要", 4, 1), ...])  # 页码先估，转 PDF 后再改
b.heading("概要", 1)
# ...
b.save()
```

`sdd_docx.py` 已处理：清空 body 保留 sectPr、宋体、Table Grid 边框顺序、函数键值表、封面作者表、点线目录。Agent 只写内容脚本（可放 `/tmp/sdd_<模块>/make_docx.py`）。

目录条目过多会在下一页留下一行空白：把 toc 行距压到 1.0（构建器默认已压）。转 PDF 后若仍溢出，减少四级目录条目或再减段距。

### 7. 校验

```bash
python <docx-skill>/scripts/office/validate.py "<output.docx>"
python <docx-skill>/scripts/office/soffice.py --headless --convert-to pdf --outdir /tmp/sdd_<模块> "<output.docx>"
pdftotext -layout /tmp/sdd_<模块>/*.pdf - | head
pdftoppm -jpeg -r 100 /tmp/sdd_<模块>/*.pdf /tmp/sdd_<模块>/page
```

对照模板看：封面、修订页、目录是否一页、标题自动编号、表线、页眉页脚、图题。XSD 失败先改 `tblBorders`/`shd` 插入位置（构建器已做，不要手改乱序）。

正文里不得出现「【模板说明】」「【示例】」「xxx模块」占位符。

Markdown 抽查：每个 \`\`\`mermaid 块 ID 为英文、中文只在引号标签内；flowchart 判定有「是/否」。

## 交付

同时给出 `.docx` 与 `.md` 路径（或按用户要求只给一种）、覆盖的代码范围、模板版本。编写者栏留空时提醒补署。不要主动 git commit。
