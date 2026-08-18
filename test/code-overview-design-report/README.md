# code-overview-design-report — 怎么测

需要：**指定代码目录**。Word 模板可选。

- 只要 Markdown：不给 docx 模板，应套 `templates/default.md` 章节。
- 要 Word：用户提供概设 Word 模板，版式跟模板走。

不要把详设的 7 行函数表、圈复杂度流程图写进概设。

## 验收清单

- [ ] 有上下文图、架构/依赖图、主路径时序（代码确实存在时）
- [ ] 无函数级流程图、无 `func_spec` 七行表
- [ ] 模块按开发依赖排序
- [ ] 代码没有的外部系统未画进边界图
- [ ] 只要 md 时章节与 `templates/default.md` 一致
