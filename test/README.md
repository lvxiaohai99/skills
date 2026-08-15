# test — Skill 测试区

这里专门用来**试各种 skill**，和正式的 skill 文件夹分开，互不影响。

> 重要：本目录**不要**放 `SKILL.md`。  
> `npx skills` 只会把「带 SKILL.md 的文件夹」当成 skill；`test/` 只是沙盒。

---

## 目录怎么用

```text
test/
├── README.md                          ← 本说明
└── <skill名字>/                       ← 每个要测的 skill 一个文件夹
    ├── README.md                      ← 这个 skill 怎么测（可选）
    ├── inputs/                        ← 放测试素材（图片、链接、样例文件）
    ├── outputs/                       ← 跑出来的结果（默认不入库）
    └── prompts.md                     ← 建议说的测试话术（可选）
```

约定：

| 文件夹 | 放什么 | 要不要提交到 Git |
|---|---|---|
| `inputs/` | 小而固定的测试素材 | 可以提交（别塞太大的文件） |
| `outputs/` | skill 生成的结果 | **默认不提交**（已在根 `.gitignore` 里忽略） |
| `prompts.md` | 你要怎么跟 AI 说才能测到点上 | 可以提交 |

---

## 怎么测一个 skill（最简单）

以已经入库的 `image-to-editable-diagram` 为例：

1. 把一张架构图/流程图丢进：
   `test/image-to-editable-diagram/inputs/`
2. 在 Cursor / Claude 里说类似：

   > 用 image-to-editable-diagram，把  
   > `test/image-to-editable-diagram/inputs/xxx.png`  
   > 转成可编辑的 PPTX，结果放到  
   > `test/image-to-editable-diagram/outputs/`

3. 打开 `outputs/` 里的文件，对照原图检查文字、连线、虚实线是否正确。

本地先装好再测：

```bash
npx skills add /home/ubuntu/learn_claud/new_project/skills@image-to-editable-diagram -g -a cursor -y
```

---

## 新增一个 skill 的测试位

仓库里每加一个 skill，就在这里同步建同名文件夹：

```bash
cd /home/ubuntu/learn_claud/new_project/skills
mkdir -p test/新skill名/{inputs,outputs}
touch test/新skill名/prompts.md
```

然后在 `prompts.md` 里写 2～3 句真实会说的测试话。

---

## 规划与改进

- 测试素材尽量小（单张图、短文链接），大文件用外链或本机路径，不要塞爆仓库。
- 测完觉得通过，再去提交正式的 skill 文件夹；`outputs/` 不用跟着提交。
- 以后若 skill 变多，可在本 README 加一张「测过没有」的小表。
