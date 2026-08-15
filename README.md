# skills

这是你自己的 **Skill 仓库**：一个 Git 仓里可以放很多个 skill，别人（或另一台电脑）可以 **只安装其中某一个**，不用把整个仓库都拷走。

远程地址：`git@github.com:lvxiaohai99/skills.git`

---

## 一句话理解

- **仓库** = 一个大抽屉（这个 Git 仓）
- **每个 skill** = 抽屉里的一个独立文件夹
- **单独安装** = 告诉工具「我只要抽屉里的那一个」，它会自动找到并装到 Cursor / Claude 里

官方安装工具是 `npx skills`（Skills CLI）。它会扫描仓库里所有带 `SKILL.md` 的文件夹，然后按名字挑选。

---

## 仓库应该怎么放

每个 skill 一个文件夹，文件夹名用小写+连字符，里面必须有 `SKILL.md`：

```text
skills/                              ← 这就是当前仓库
├── README.md                        ← 本说明书
├── test/                            ← 测试沙盒（不是 skill，勿放 SKILL.md）
│   └── <skill名>/inputs|outputs/
├── image-to-editable-diagram/       ← skill 1
│   ├── SKILL.md                     ← 必须有，且开头要写 name、description
│   ├── scripts/                     ← 可选：脚本
│   ├── references/                  ← 可选：补充文档
│   └── assets/                      ← 可选：模板、图片
├── web-to-markdown/                 ← skill 2：网页文章落地为标准 md
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
└── mihomo-proxy-setup/              ← skill 3
    └── SKILL.md
```

测 skill 请用仓库根目录的 [`test/`](./test/)（每个 skill 一个子文件夹，素材进 `inputs/`，结果进 `outputs/`）。

`SKILL.md` 开头必须长这样（`name` 最好和文件夹名一致）：

```markdown
---
name: image-to-editable-diagram
description: 把架构图、流程图转成可编辑的 PPT / Mermaid / HTML。当用户提到架构图、流程图、把截图变成可编辑文档时使用。
---

# 这里写具体步骤
```

**不要**把多个 skill 的内容写进同一个 `SKILL.md`。工具是按「一个文件夹 = 一个 skill」来识别的。

---

## 怎么单独安装某一个 skill

先确保这台电脑能访问 GitHub（你已经用 SSH：`git@github.com:lvxiaohai99/skills.git`）。

### 1）先看看仓库里有哪些 skill（不安装）

```bash
npx skills add lvxiaohai99/skills --list
```

或从本机已经 clone 下来的目录列：

```bash
npx skills add /home/ubuntu/learn_claud/new_project/skills --list
```

### 2）只安装某一个（推荐）

```bash
# 写法 A：名字写在 @ 后面
npx skills add lvxiaohai99/skills@image-to-editable-diagram

# 写法 B：用 --skill 指定
npx skills add lvxiaohai99/skills --skill image-to-editable-diagram
```

一次装两个：

```bash
npx skills add lvxiaohai99/skills --skill image-to-editable-diagram --skill web-to-markdown
```

### 3）装到哪里、给谁用

| 你想要的效果 | 命令 |
|---|---|
| 全局可用（所有项目都能用），装给 Cursor | `npx skills add lvxiaohai99/skills@名称 -g -a cursor -y` |
| 全局可用，装给 Claude Code | `npx skills add lvxiaohai99/skills@名称 -g -a claude-code -y` |
| 只给当前这个项目用 | 先 `cd` 到那个项目，再执行上面的命令，**不要**加 `-g` |
| 不想一路点确认 | 加上 `-y` |

完整例子（最常用）：

```bash
npx skills add lvxiaohai99/skills@image-to-editable-diagram -g -a cursor -y
```

装好后，Cursor 会把它放到 `~/.cursor/skills/image-to-editable-diagram/`。

### 4）仓库是私有的怎么办

`npx skills` 会走你本机已经配好的 Git 权限。你现在用的是 SSH，所以也可以直接写完整地址：

```bash
npx skills add git@github.com:lvxiaohai99/skills.git --skill image-to-editable-diagram -g -a cursor -y
```

---

## 只「拉文件」、不走安装工具

如果你只是想把某一个 skill 的文件夹下载下来（比如拷到别的目录自己改），不必装 CLI，用 Git 的 **稀疏检出（sparse-checkout）**：

```bash
git clone --filter=blob:none --sparse git@github.com:lvxiaohai99/skills.git
cd skills
git sparse-checkout set image-to-editable-diagram
```

这样本地几乎只有 `image-to-editable-diagram/` 这一个 skill，其它 skill 的文件不会下载下来。

已经 clone 过整个仓库、只想再取出某一个：

```bash
cd /home/ubuntu/learn_claud/new_project/skills
git sparse-checkout init --cone
git sparse-checkout set README.md image-to-editable-diagram
```

想恢复成「拉全部」：

```bash
git sparse-checkout disable
```

---

## 日常怎么往仓里加新 skill

1. 在仓库根目录新建文件夹，例如 `my-new-skill/`
2. 在里面写 `SKILL.md`（必须有 `name` 和 `description`）
3. 提交并推送：

```bash
cd /home/ubuntu/learn_claud/new_project/skills
git add my-new-skill
git commit -m "Add my-new-skill"
git push
```

另一台电脑只要：

```bash
npx skills add lvxiaohai99/skills@my-new-skill -g -a cursor -y
```

更新已经装过的 skill：

```bash
npx skills update
```

或再执行一次同样的 `npx skills add ...` 覆盖安装。

---

## 常用命令速查

| 我想做的事 | 命令 |
|---|---|
| 看仓库里有哪些 skill | `npx skills add lvxiaohai99/skills --list` |
| 只装一个 | `npx skills add lvxiaohai99/skills@名称 -g -a cursor -y` |
| 只装几个 | `npx skills add lvxiaohai99/skills --skill 甲 --skill 乙 -g -y` |
| 全部都装 | `npx skills add lvxiaohai99/skills --skill '*' -g -y` |
| 检查有没有更新 | `npx skills check` |
| 更新已安装的 | `npx skills update` |
| 只下载某一个文件夹 | 见上面的 `git sparse-checkout` |

`名称` 填的是 `SKILL.md` 里的 `name`，一般就等于文件夹名。

---

## 可能踩的坑

- **装不上 / 列表是空的**：每个 skill 文件夹里必须有 `SKILL.md`，且开头 YAML 里要有 `name` 和 `description`。
- **装了但 Cursor 找不到**：确认加了 `-a cursor`，并且重启过 Cursor 对话。
- **私有仓提示没权限**：先在这台机器测 `ssh -T git@github.com`，能通再用 SSH 地址安装。
- **不要把 skill 塞进 `.git/` 或乱放在深层目录**：放在仓库根目录（或统一放在一层 `skills/` 子目录）最稳，CLI 才能扫到。

---

## 怎么在本仓测试 skill

见 [`test/README.md`](./test/README.md)。一句话流程：

1. 素材放进 `test/<skill名>/inputs/`
2. 按 `test/<skill名>/prompts.md` 里的话术让 AI 跑
3. 结果看 `test/<skill名>/outputs/`（默认不提交）

## 规划与改进

已入库的 skill 见下表。下一步建议：

1. 继续把常用 skill（例如 `mihomo-proxy-setup`）各复制成独立文件夹推进来。
2. 每加一个 skill，就在本 README 的「仓库里已有的 skill」表格里补一行，并在 `test/` 下建同名测试位。
3. 不需要自己写安装脚本，`npx skills` 已经支持按名字挑选。

### 仓库里已有的 skill

| 名字 | 干什么用 | 单独安装 |
|---|---|---|
| `image-to-editable-diagram` | 把架构图/流程图/时序图等参考图转成可编辑的 HTML+SVG、Mermaid、PPTX、draw.io | `npx skills add lvxiaohai99/skills@image-to-editable-diagram -g -a cursor -y` |
| `web-to-markdown` | 把一篇或多篇网络文章（公众号、CSDN 等）抓成带图的本地 md，再整理成干净的标准文档 | `npx skills add lvxiaohai99/skills@web-to-markdown -g -a cursor -y` |
