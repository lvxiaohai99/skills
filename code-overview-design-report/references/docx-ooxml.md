# 从模板克隆生成 docx 的 OOXML 注意点

生成方式：**复制模板 → 清空 body（保留 sectPr）→ 用模板样式重建正文**。这样页眉页脚、主题、标题编号、页面设置都还在。不要用 docx-js 从空白文档重做。

依赖：`python-docx`。校验用文档技能目录下的 `scripts/office/validate.py`。转 PDF 用同目录 `scripts/office/soffice.py`。

## tblPr / tcPr 子元素顺序

追加元素到末尾会 XSD 失败。用 `sdd_docx.insert_before`：

- `tblBorders` 插在 `tblLook` / `tblCaption` 之前
- `shd` 插在 `vAlign` / `hideMark` 之前
- `tcBorders` 同样插在 `shd` 之前

表头底纹用 `ShadingType` 语义的 `w:val="clear"`，不要 SOLID。

## 字体

中文 eastAsia=宋体；西文 ascii/hAnsi=Times New Roman（Heading 1 的 ascii 也是 Times New Roman）。封面标题 ascii 也用宋体以匹配模板。

## 分页

`w:br w:type="page"` 放在 run 里，不要单独的 PageBreak 对象飘在段外。封面法律声明段末分页；修订记录后再分页；目录后再分页。

## 目录

模板有 `TOC \o "1-4"` 域，LibreOffice 导出不一定刷新。用 toc 1–4 样式 + `w:ptab`（alignment=right, relativeTo=margin, leader=dot）手写目录。条目过多会把最后一行挤到下一页变成空白页——行距必须压到 1.0、段前段后 0。

## 校验与目视

```bash
python <docx-skill>/scripts/office/validate.py output.docx
python <docx-skill>/scripts/office/soffice.py --headless --convert-to pdf --outdir /tmp output.docx
pdftoppm -jpeg -r 100 output.pdf page
```

对照模板封面、修订页、目录、正文标题编号、表格边框、页眉页脚逐页看图。失败则改生成脚本，不要手工改 XML 应付。
