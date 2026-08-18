---
name: code-overview-design-report
description: >-
  Generates a Chinese software high-level design (概要设计) report from specified
  source code: Word (.docx) strictly following a user-specified template, and a
  parallel Markdown with mermaid context, architecture, dependency, and sequence
  diagrams. Use when the user asks for 概要设计报告, 概要设计, 总体设计, HLD,
  按模板写概设, 根据代码生成概要设计, 架构图/模块划分/接口概要;
  whenever an HLD template and a code module/path are given together.
  Do not use for 详细设计 (that is code-detailed-design-report) or for PRD-to-spec
  (that is prd-to-design).
---

# 按代码生成概要设计报告

根据**指定代码**写概要设计，**同时**输出：

1. `.docx` — 版式严格遵守用户指定的 Word 模板
2. `.md` — 同一套章节与事实；上下文、逻辑架构、模块依赖、主路径时序一律 **mermaid**

用户只说「只要 Word」或「只要 Markdown」时才省略另一种。内容只写代码里有的东西，不要编模块、接口或部署形态。

本技能停在**概要层**：模块职责、依赖、接口契约、数据实体、主路径、非功能落地。函数体、7 行函数表、圈复杂度流程图、类字段清单属于详细设计，交给 `code-detailed-design-report`。

`$SKILL_DIR` = 本 skill 根目录。写 Word 时同时遵循 Cursor 的 **docx** 技能。图约定见 [references/markdown-mermaid.md](references/markdown-mermaid.md)。无 Word 模板且只要 Markdown 时，用 [templates/default.md](templates/default.md)。

## 输入

缺代码范围或（要 Word 时）缺模板路径就问，不要猜：

| 项 | 说明 |
|----|------|
| 代码范围 | 目录、包名或「按某模块实现」；可附架构 md、功能需求表（只做追溯，不发明功能） |
| 模板 | `.docx` / `.dotx`；用户指定哪个用哪个。只要 md 且未给 Word → `templates/default.md` |
| 模块显示名 | 封面与章标题，如 `OTA`、`DVR` |
| 软件名/版本 | 默认取仓库/架构文档；版本默认 `V1.0.0` |
| 输出路径 | 默认：`<软件名>软件概要设计报告_<模块>模块_<版本>.docx` 与同名 `.md` |

作者/审核/审批未给则留空，只填发布日期（当天）。

从 PRD 空想架构请用 `prd-to-design`，不要用本 skill。

## 工作流

```
Task Progress:
- [ ] 1. 解析模板结构（Word 或 default.md）
- [ ] 2. 阅读架构文档 / 功能需求表，核对对外名称与 FR-ID
- [ ] 3. 阅读指定代码（入口、进程/域、模块边界、接口、存储、状态）
- [ ] 4. 按开发依赖列出模块，映射到模板章节
- [ ] 5. 先写 mermaid（上下文/架构/依赖/主时序），再生成 Markdown 概设
- [ ] 6. 由同一套 mermaid 出 PNG，克隆模板生成 docx（若需要 Word）
- [ ] 7. XSD 校验 + PDF 目视；抽查 md 中 mermaid 可解析
```

### 1. 解析模板

```bash
python "$SKILL_DIR/scripts/inspect_template.py" \
  "<模板.docx>" -o /tmp/hld_template.json
```

读 JSON：标题层级、表格表头、分页、TOC、【模板说明】。

- 文件名或说明含「概要设计」且章节接近本仓库骨架 → 再读 [references/citc-hld.md](references/citc-hld.md)，**不要另起章名**。
- 其他 Word：用 inspect 得到的 **Heading 文字** 当骨架；删除【模板说明】【示例】。
- 无 Word、只要 Markdown：Read `templates/default.md`，按该标题填。

生成注意点见 [references/docx-ooxml.md](references/docx-ooxml.md)。

### 2. 名称与需求对齐

先读仓库根 `readme.md` / `architecture.md` / 用户点名的架构或功能需求表。边界图里的本模块名、外部模块名必须与架构文档**字面一致**。有 FR-ID 则在追溯表引用；功能需求有、代码没有的标「代码未实现」，不要画成已有模块。

### 3. 从代码抽概要事实

只读用户指定范围及其直接依赖。记录：

- 运行形态：进程、Android 服务、native daemon、双域（IVI/仪表/MCU）——以代码/启动脚本为准
- 模块划分（按包/职责，一般 4–8 个），**按被依赖者在前**排开发顺序
- 对外接口（被 UI/系统/邻模块调用的）：名称、方向、关键字段、错误语义；不要抄函数实现
- 关键数据：文件格式、表/实体、命名规则、留存
- 主路径与关键异常（无盘、无信号、失败回滚等）
- 配置字、端口、魔数以代码常量为准

禁止：把详设示例（`Fcw::Arithmetic`、逐函数流程图）写进概设；禁止把 TODO 当已实现；禁止为凑篇幅引入代码里没有的中间件。

### 4. 章节映射（深度控制）

| 要写 | 不要写 |
|---|---|
| 上下文、逻辑分层、模块依赖图 | 每个 getter 的类图 |
| 接口名 + 关键字段 + 错误 | 完整 JSON/protobuf 小说、7 行函数表 |
| 实体与留存策略 | 全量 DDL、索引调优 |
| 主路径 1～2 张时序；明确状态机则一张状态图 | 圈复杂度>7 的程序流程图（那是详设 2.3） |

模板有「单元/函数详细设计」而用户明确要概设：该节写「详见详细设计」或只保留模块级文字，**不要硬填函数表**。

### 5. 先 Markdown + mermaid，再 Word 插图

**先写 `.md`**（标题与 Word 一致）。最低图集（模板没有对应章则可缺）：

- 系统上下文 / 边界：`flowchart`（红=本模块，黄=内部模块，灰=外部）
- 逻辑架构：按代码分层的 `flowchart`
- 模块依赖（开发顺序）：`flowchart TB`
- 主路径：`sequenceDiagram`；第二关键路径若代码存在再画一张
- 代码里有明确枚举状态机：一张 `stateDiagram-v2`

不要为每个函数画流程图。

```bash
command -v mmdc && mmdc -i fig_context.mmd -o fig_context.png -b white -s 2
```

无 `mmdc` 时用 PIL 按同一节点和边重画。中文字体 `NotoSansCJK` 或宋体。

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$SKILL_DIR") / "scripts"))
from sdd_markdown import MarkdownBuilder

m = MarkdownBuilder(output_md)
m.front_matter(title="…软件概要设计报告_…模块", version="V1.0.0",
               date="YYYY-MM-DD", source_code=["…"], template="…概要设计….docx")
m.h("概述", 1)
m.caption("图2-1 …模块上下文")
m.mermaid("""flowchart TB
  classDef module fill:#F4CCCC,stroke:#C00000,stroke-width:2px
  ...
""")
m.save()
```

```bash
python "$SKILL_DIR/scripts/extract_mermaid.py" \
  "<output.md>" -o /tmp/hld_<模块> --render
```

### 6. 生成 docx

克隆模板，不要从空白文档重做页眉页脚：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$SKILL_DIR") / "scripts"))
from sdd_docx import ReportBuilder

b = ReportBuilder(template, output)
b.open()
b.cover(title="…软件概要设计报告_…模块", version="V1.0.0", release_date="YYYY-MM-DD")
b.revision_page([["YYYY-MM-DD", "V1.0.0", "", "全部", "根据代码实现首次编制概要设计"]])
b.toc_page("目 录", [("1  概述", 4, 1), ...])
b.heading("概述", 1)
b.save()
```

封面标题按用户模板；若模板写「详细设计」而用户要概设，标题用「概要设计」，不要沿用详设封面字样。

### 7. 校验

```bash
python <docx-skill>/scripts/office/validate.py "<output.docx>"
python <docx-skill>/scripts/office/soffice.py --headless --convert-to pdf --outdir /tmp/hld_<模块> "<output.docx>"
pdftotext -layout /tmp/hld_<模块>/*.pdf - | head
pdftoppm -jpeg -r 100 /tmp/hld_<模块>/*.pdf /tmp/hld_<模块>/page
```

对照模板：封面、修订、目录一页、标题编号、表线、页眉页脚、图题。正文不得出现「【模板说明】」「【示例】」「xxx模块」占位符。

Markdown：mermaid ID 英文、中文只在引号标签；判定才需要「是/否」（架构图无判定不要硬加）。

## 交付

同时给出 `.docx` 与 `.md`（或按要求只给一种）、代码范围、模板、所用章节骨架。编写者栏留空时提醒补署。不要主动 git commit。

对话摘要写清：这是概要设计，详细设计请另用 `code-detailed-design-report`。
