# prd-to-design — 怎么测

1. 样例 PRD 在 `inputs/车载诊断日志上报-PRD.md`。
2. 用 `prompts.md` 的话术让 AI 跑。
3. 结果应出现在 `outputs/`：
   - `车载诊断日志上报-PRD-功能需求.md`
   - `车载诊断日志上报-PRD-概要设计.md`

## 本地只测提取脚本（不写设计）

```bash
SKILL=/home/ubuntu/learn_claud/new_project/skills/prd-to-design
python3 -m venv "$SKILL/.venv"
"$SKILL/.venv/bin/pip" install -r "$SKILL/requirements.txt"

PYTHONIOENCODING=utf-8 "$SKILL/.venv/bin/python" \
  "$SKILL/scripts/extract_prd.py" \
  /home/ubuntu/learn_claud/new_project/skills/test/prd-to-design/inputs/车载诊断日志上报-PRD.md
```

通过标准：打印 `===PRD_META===`，`chars` 明显大于 200，正文含「诊断日志」以及协议未指定等待定项。

缺文件时应 stderr 报错并非 0 退出。

## 最近一次自测（2026-08-18）

| # | 用例 | 结果 |
|---|------|------|
| 1 | `extract_prd.py` → 样例 Markdown PRD | 成功，正文 chars=1390，无 warnings |
| 2 | 临时 mini.docx / .pptx / .xlsx | 正文与表格/备注可抽出；短样触发 `low_text` 符合预期 |
| 3 | 多文件、缺文件、`.py` | 多文件合并；缺文件与不支持格式均非 0 退出 |
| 4 | 按模板产出两份文档 | 见 `outputs/`（默认不入库） |

## 验收清单（端到端）

- [ ] 功能需求表含 FR / NFR / OPEN / 范围外；协议未定不能写成已定接口
- [ ] 每条 P0 有可判定的验收标准
- [ ] 概要设计按模块依赖顺序，而不是按 PRD 章节复述
- [ ] 追溯表覆盖全部 P0
- [ ] 两份 UTF-8 Markdown 都落在 `outputs/`
- [ ] 指定 `ivi` 时功能需求含「车载专项核对」
- [ ] 指定 `templates/精简/` 时成品章节与精简模板一致，而不是 default 的 12 节
