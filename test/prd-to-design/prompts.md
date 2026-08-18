# prd-to-design — 测试话术

## 1. Markdown PRD（主路径）

用 prd-to-design，根据  
`test/prd-to-design/inputs/车载诊断日志上报-PRD.md`  
先整理面向研发的功能需求表，再基于该表写概要设计。  
两份文档保存到 `test/prd-to-design/outputs/`。

## 2. 只要概要设计

用 prd-to-design，根据  
`test/prd-to-design/inputs/车载诊断日志上报-PRD.md`  
只要概要设计（仍须先产出功能需求表）。结果写到  
`test/prd-to-design/outputs/`。

## 3. 粘贴短需求（测无文件路径）

下面是一段 PRD，按 prd-to-design 拆功能需求表并写概要设计：

司机可一键把最近的诊断日志发到云端。弱网也要能传。注意隐私。协议后续再定。

## 4. 指定内置模板 ivi

用 prd-to-design，模板用 ivi（车载座舱），根据  
`test/prd-to-design/inputs/自研_G200Z平台_行车记录仪产品需求文档_v1.0.docx`  
出功能需求表和概要设计，保存到 `test/prd-to-design/outputs/`。

## 5. 指定自定义模板目录

用 prd-to-design，模板目录用  
`test/prd-to-design/templates/精简/`，  
根据 `test/prd-to-design/inputs/车载诊断日志上报-PRD.md`  
出两份文档到 `test/prd-to-design/outputs/`（文件名加后缀 `-精简` 以免覆盖主路径产物）。
