# interview — 怎么测

1. 样例简历已在 `inputs/`（Markdown + HTML）。
2. 在 Cursor 里用 `prompts.md` 里的话术让 AI 跑。
3. 结果应出现在 `outputs/`：与简历同名的 `.md` 报告。

## 本地只测提取脚本（不走出题）

```bash
SKILL=/home/ubuntu/learn_claud/new_project/skills/interview
python3 -m venv "$SKILL/.venv"
"$SKILL/.venv/bin/pip" install -r "$SKILL/requirements.txt"

PYTHONIOENCODING=utf-8 "$SKILL/.venv/bin/python" \
  "$SKILL/scripts/extract_resume.py" \
  /home/ubuntu/learn_claud/new_project/skills/test/interview/inputs/张三-嵌入式Linux.md
```

通过标准：打印 `===RESUME_META===`，`chars` 明显大于 200，正文含「张三」「AB 分区」。

## 验收清单（端到端）

- [x] 技术栈区分熟练 / 仅提及（如 Docker/K8s/Rust 为仅提及）
- [x] 工作经历为表格，含 OTA / 启动优化等量化点
- [x] 一面、二面各 5～7 题，每题有「简历锚点」
- [x] 报告 UTF-8，文件名与简历主名一致

## 最近一次自测（2026-08-17）

| # | 用例 | 结果 |
|---|------|------|
| 1 | `extract_resume.py` → Markdown 简历 | 成功，chars=1022，无 warnings |
| 2 | `extract_resume.py` → HTML 短样 | 成功，`low_text` 警告符合预期 |
| 3 | `extract_resume.py` → CSV / 缺文件 | CSV 成功；缺文件 stderr 报错退出 |
| 4 | 端到端报告 `张三-嵌入式Linux.md` | 一面 6 + 二面 6，锚点齐全 |
| 5 | 短 HTML 联调报告 `sample-skills.md` | 成功，并标明材料不足 |
| 6 | 本机真实 PDF×2（未入库） | 能抽出正文；招聘站水印会夹杂噪声，正式用建议 Word/干净 PDF |

> 真实候选人 PDF 已加入 `.gitignore`（`test/interview/inputs/*.pdf`），只留本机联调，避免把手机号等个人信息推进仓库。
