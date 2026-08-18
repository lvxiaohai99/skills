#!/usr/bin/env python3
"""Write a Markdown 详细设计 that mirrors the Word chapter skeleton.

Diagrams MUST be mermaid fences (architecture / sequence / flowchart).
Agent should generate the .md first, then render the same mermaid to PNG
for the .docx. Typical usage:

    from sdd_markdown import MarkdownBuilder
    m = MarkdownBuilder(output)
    m.front_matter(title="G200Z软件详细设计报告_OTA模块", version="V1.0.0")
    m.h("概要", 1)
    m.p("……")
    m.caption("图2-1 OTA模块边界关系图")
    m.mermaid("flowchart TB\\n  A[\"OTA模块\"] --> B[\"USB\"]")
    m.save()
"""
from __future__ import annotations

import re
from pathlib import Path


MERMAID_FENCE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


class MarkdownBuilder:
    def __init__(self, output: str | Path):
        self.output = Path(output)
        self._parts: list[str] = []

    def front_matter(
        self,
        *,
        title: str,
        version: str,
        date: str,
        source_code: list[str],
        template: str,
        extra: dict[str, str] | None = None,
    ) -> None:
        lines = [
            "---",
            f"title: {title}",
            f"version: {version}",
            f"date: {date}",
            "source_code:",
        ]
        for p in source_code:
            lines.append(f"  - {p}")
        lines.append(f"template: {template}")
        if extra:
            for k, v in extra.items():
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**版本：** {version}  ")
        lines.append(f"**发布日期：** {date}")
        lines.append("")
        self._parts.append("\n".join(lines))

    def h(self, text: str, level: int) -> None:
        if level < 1 or level > 4:
            raise ValueError("heading level must be 1–4")
        self._parts.append(f"{'#' * (level + 1)} {text}\n")

    def p(self, text: str) -> None:
        self._parts.append(f"{text.strip()}\n")

    def note(self, text: str) -> None:
        self._parts.append(f"**注：** {text.strip()}\n")

    def caption(self, text: str) -> None:
        self._parts.append(f"**{text.strip()}**\n")

    def mermaid(self, source: str) -> None:
        body = source.strip()
        if not body:
            raise ValueError("empty mermaid source")
        self._parts.append(f"```mermaid\n{body}\n```\n")

    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        esc = lambda c: str(c).replace("|", "\\|").replace("\n", "<br>")
        head = "| " + " | ".join(esc(h) for h in headers) + " |"
        sep = "| " + " | ".join("---" for _ in headers) + " |"
        body = ["| " + " | ".join(esc(c) for c in row) + " |" for row in rows]
        self._parts.append("\n".join([head, sep, *body]) + "\n")

    def kv_table(self, pairs: list[tuple[str, str]]) -> None:
        self.table(["项目", "内容"], [[k, v] for k, v in pairs])

    def func_spec(
        self,
        *,
        name: str,
        ret: str,
        params: str,
        purpose: str,
        calls: str,
        decl_file: str,
        impl_file: str,
    ) -> None:
        self.kv_table(
            [
                ("函数名", name),
                ("函数返回值", ret),
                ("参数列表", params),
                ("函数功能", purpose),
                ("调用的函数", calls),
                ("函数定义文件", decl_file),
                ("函数实现文件", impl_file),
            ]
        )

    def numbered(self, items: list[str]) -> None:
        self._parts.append(
            "\n".join(f"（{i}）{t}" for i, t in enumerate(items, 1)) + "\n"
        )

    def save(self) -> Path:
        text = "\n".join(self._parts).rstrip() + "\n"
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(text, encoding="utf-8")
        return self.output


def extract_mermaid_blocks(md_path: str | Path) -> list[str]:
    text = Path(md_path).read_text(encoding="utf-8")
    return [m.group(1).strip() for m in MERMAID_FENCE.finditer(text)]


def dump_mermaid_files(md_path: str | Path, out_dir: str | Path, prefix: str = "fig") -> list[Path]:
    """Write each mermaid fence to out_dir/fig_01.mmd … for mmdc."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, src in enumerate(extract_mermaid_blocks(md_path), 1):
        p = out / f"{prefix}_{i:02d}.mmd"
        p.write_text(src + "\n", encoding="utf-8")
        written.append(p)
    return written


_BARE_CJK_LEFT = re.compile(
    r"(^|[\s;])([A-Za-z0-9_]*[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*(-->|---|===|->>|-->>)"
)
_BARE_CJK_RIGHT = re.compile(
    r"(-->|---|===|->>|-->>)\s*([A-Za-z0-9_]*[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\b"
)


def lint_mermaid(source: str) -> list[str]:
    """Cheap checks so Chinese IDs and empty graphs fail before Word conversion."""
    issues: list[str] = []
    first = source.strip().splitlines()[0].strip() if source.strip() else ""
    kinds = ("flowchart", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram")
    if not any(first.startswith(k) or first.startswith("graph ") for k in kinds):
        issues.append(f"unknown diagram type: {first!r}")
    if _BARE_CJK_LEFT.search(source) or _BARE_CJK_RIGHT.search(source):
        issues.append("CJK used as node/edge ID; put Chinese in [\"标签\"] and keep ASCII IDs")
    if "flowchart" in first or first.startswith("graph "):
        if "{" in source and "是" not in source and "否" not in source and "|Yes|" not in source:
            if source.count("{") >= 1:
                issues.append("flowchart has decision node(s) but no 是/否 (or Yes/No) branch labels")
    return issues
