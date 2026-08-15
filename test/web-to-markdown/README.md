# web-to-markdown — 怎么测

1. 把要抓的链接写进 `inputs/urls.txt`（已有公众号 + 两篇 CSDN）。
2. 在 Cursor 里用 `prompts.md` 里的话术让 AI 跑。
3. 结果应出现在 `outputs/`：每篇文章一个文件夹，里面有 `raw.md`、`article.md`、`images/`、`preview.html`。

## 本地只测脚本（不走模型精修）

```bash
bash /home/ubuntu/learn_claud/new_project/skills/web-to-markdown/scripts/run.sh \
  -f /home/ubuntu/learn_claud/new_project/skills/test/web-to-markdown/inputs/urls.txt \
  -d /home/ubuntu/learn_claud/new_project/skills/test/web-to-markdown/outputs
```

看 `outputs/manifest.json` 是否成功；再按 `polish_guide.md` 写出 `article.md`。

## 最近一次自测（2026-08-15）

| # | 链接类型 | 结果 |
|---|----------|------|
| 1 | 公众号 | 成功，正文有，原文无图 |
| 2 | CSDN RK3576 AB | 成功，42 图 / 20 代码块，配图齐全 |
| 3 | CSDN RK3566 AB | 成功，18 代码块，表格保留 |

`manifest.json`：成功 3 / 共 3。`outputs/` 默认不提交。
