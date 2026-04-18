#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
from io import StringIO
import hashlib
import html
import importlib
import importlib.util
import inspect
import json
import os
import random
import subprocess
import statistics
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass, fields
from numbers import Number
from pathlib import Path
import fnmatch
from types import ModuleType
from typing import Any, Callable, Iterable, Iterator

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
BenchmarkNoteAnnotation = dict[str, JSONValue]
BenchmarkNoteItem = str | BenchmarkNoteAnnotation
KeyValue = tuple[str, JSONValue]
Mapper = Callable[[Iterable[str]], Iterator[KeyValue]]
Reducer = Callable[[str, list[JSONValue]], JSONValue]
BenchmarkGenerator = Callable[..., list[str]]
BenchmarkNoteHook = Callable[..., list[BenchmarkNoteItem] | tuple[BenchmarkNoteItem, ...] | None]


def write_text_output(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


PLUGIN_INSPECTION_FIELDNAMES = [
    "name",
    "plugin",
    "plugin_repo_commit",
    "module_doc_summary",
    "mapper",
    "mapper_signature",
    "mapper_doc_summary",
    "mapper_source_line",
    "mapper_source_anchor",
    "mapper_source_url",
    "mapper_source_commit_url",
    "reducer",
    "reducer_signature",
    "reducer_doc_summary",
    "reducer_source_line",
    "reducer_source_anchor",
    "reducer_source_url",
    "reducer_source_commit_url",
    "combiner",
    "combiner_signature",
    "combiner_doc_summary",
    "combiner_source_line",
    "combiner_source_anchor",
    "combiner_source_url",
    "combiner_source_commit_url",
    "benchmark_generator",
    "benchmark_generator_signature",
    "benchmark_generator_doc_summary",
    "benchmark_generator_source_line",
    "benchmark_generator_source_anchor",
    "benchmark_generator_source_url",
    "benchmark_generator_source_commit_url",
    "benchmark_note_hook",
    "benchmark_note_hook_signature",
    "benchmark_note_hook_doc_summary",
    "benchmark_note_hook_source_line",
    "benchmark_note_hook_source_anchor",
    "benchmark_note_hook_source_url",
    "benchmark_note_hook_source_commit_url",
    "available_dataset_families",
]

PLUGIN_INSPECTION_DIFF_FIELDS = [
    "name",
    "plugin",
    "plugin_repo_commit",
    "module_doc_summary",
    "mapper",
    "mapper_signature",
    "mapper_doc_summary",
    "mapper_source_line",
    "mapper_source_anchor",
    "mapper_source_url",
    "mapper_source_commit_url",
    "mapper_source_excerpt",
    "reducer",
    "reducer_signature",
    "reducer_doc_summary",
    "reducer_source_line",
    "reducer_source_anchor",
    "reducer_source_url",
    "reducer_source_commit_url",
    "reducer_source_excerpt",
    "combiner",
    "combiner_signature",
    "combiner_doc_summary",
    "combiner_source_line",
    "combiner_source_anchor",
    "combiner_source_url",
    "combiner_source_commit_url",
    "combiner_source_excerpt",
    "benchmark_generator",
    "benchmark_generator_signature",
    "benchmark_generator_doc_summary",
    "benchmark_generator_source_line",
    "benchmark_generator_source_anchor",
    "benchmark_generator_source_url",
    "benchmark_generator_source_commit_url",
    "benchmark_generator_source_excerpt",
    "benchmark_note_hook",
    "benchmark_note_hook_signature",
    "benchmark_note_hook_doc_summary",
    "benchmark_note_hook_source_line",
    "benchmark_note_hook_source_anchor",
    "benchmark_note_hook_source_url",
    "benchmark_note_hook_source_commit_url",
    "benchmark_note_hook_source_excerpt",
    "available_dataset_families",
]

PLUGIN_RELEASE_DIFF_FIELDS = [
    "plugin",
    "module_doc_summary",
    "mapper",
    "mapper_signature",
    "mapper_doc_summary",
    "reducer",
    "reducer_signature",
    "reducer_doc_summary",
    "combiner",
    "combiner_signature",
    "combiner_doc_summary",
    "benchmark_generator",
    "benchmark_generator_signature",
    "benchmark_generator_doc_summary",
    "benchmark_note_hook",
    "benchmark_note_hook_signature",
    "benchmark_note_hook_doc_summary",
    "available_dataset_families",
]

PLUGIN_RELEASE_HOOK_FIELDS = [
    ("Mapper", "mapper", "mapper_signature"),
    ("Reducer", "reducer", "reducer_signature"),
    ("Combiner", "combiner", "combiner_signature"),
    ("Benchmark generator", "benchmark_generator", "benchmark_generator_signature"),
    ("Benchmark note hook", "benchmark_note_hook", "benchmark_note_hook_signature"),
]


@dataclass(slots=True)
class PluginInspection:
    name: str
    plugin: str
    plugin_repo_commit: str | None
    module_doc_summary: str | None
    mapper: str
    mapper_signature: str | None
    mapper_doc_summary: str | None
    mapper_source_line: int | None
    mapper_source_anchor: str | None
    mapper_source_url: str | None
    mapper_source_commit_url: str | None
    mapper_source_excerpt: str | None
    reducer: str
    reducer_signature: str | None
    reducer_doc_summary: str | None
    reducer_source_line: int | None
    reducer_source_anchor: str | None
    reducer_source_url: str | None
    reducer_source_commit_url: str | None
    reducer_source_excerpt: str | None
    combiner: str | None
    combiner_signature: str | None
    combiner_doc_summary: str | None
    combiner_source_line: int | None
    combiner_source_anchor: str | None
    combiner_source_url: str | None
    combiner_source_commit_url: str | None
    combiner_source_excerpt: str | None
    benchmark_generator: str | None
    benchmark_generator_signature: str | None
    benchmark_generator_doc_summary: str | None
    benchmark_generator_source_line: int | None
    benchmark_generator_source_anchor: str | None
    benchmark_generator_source_url: str | None
    benchmark_generator_source_commit_url: str | None
    benchmark_generator_source_excerpt: str | None
    benchmark_note_hook: str | None
    benchmark_note_hook_signature: str | None
    benchmark_note_hook_doc_summary: str | None
    benchmark_note_hook_source_line: int | None
    benchmark_note_hook_source_anchor: str | None
    benchmark_note_hook_source_url: str | None
    benchmark_note_hook_source_commit_url: str | None
    benchmark_note_hook_source_excerpt: str | None
    available_dataset_families: list[str] | None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "plugin": self.plugin,
            "plugin_repo_commit": self.plugin_repo_commit,
            "module_doc_summary": self.module_doc_summary,
            "mapper": self.mapper,
            "mapper_signature": self.mapper_signature,
            "mapper_doc_summary": self.mapper_doc_summary,
            "mapper_source_line": self.mapper_source_line,
            "mapper_source_anchor": self.mapper_source_anchor,
            "mapper_source_url": self.mapper_source_url,
            "mapper_source_commit_url": self.mapper_source_commit_url,
            "mapper_source_excerpt": self.mapper_source_excerpt,
            "reducer": self.reducer,
            "reducer_signature": self.reducer_signature,
            "reducer_doc_summary": self.reducer_doc_summary,
            "reducer_source_line": self.reducer_source_line,
            "reducer_source_anchor": self.reducer_source_anchor,
            "reducer_source_url": self.reducer_source_url,
            "reducer_source_commit_url": self.reducer_source_commit_url,
            "reducer_source_excerpt": self.reducer_source_excerpt,
            "combiner": self.combiner,
            "combiner_signature": self.combiner_signature,
            "combiner_doc_summary": self.combiner_doc_summary,
            "combiner_source_line": self.combiner_source_line,
            "combiner_source_anchor": self.combiner_source_anchor,
            "combiner_source_url": self.combiner_source_url,
            "combiner_source_commit_url": self.combiner_source_commit_url,
            "combiner_source_excerpt": self.combiner_source_excerpt,
            "benchmark_generator": self.benchmark_generator,
            "benchmark_generator_signature": self.benchmark_generator_signature,
            "benchmark_generator_doc_summary": self.benchmark_generator_doc_summary,
            "benchmark_generator_source_line": self.benchmark_generator_source_line,
            "benchmark_generator_source_anchor": self.benchmark_generator_source_anchor,
            "benchmark_generator_source_url": self.benchmark_generator_source_url,
            "benchmark_generator_source_commit_url": self.benchmark_generator_source_commit_url,
            "benchmark_generator_source_excerpt": self.benchmark_generator_source_excerpt,
            "benchmark_note_hook": self.benchmark_note_hook,
            "benchmark_note_hook_signature": self.benchmark_note_hook_signature,
            "benchmark_note_hook_doc_summary": self.benchmark_note_hook_doc_summary,
            "benchmark_note_hook_source_line": self.benchmark_note_hook_source_line,
            "benchmark_note_hook_source_anchor": self.benchmark_note_hook_source_anchor,
            "benchmark_note_hook_source_url": self.benchmark_note_hook_source_url,
            "benchmark_note_hook_source_commit_url": self.benchmark_note_hook_source_commit_url,
            "benchmark_note_hook_source_excerpt": self.benchmark_note_hook_source_excerpt,
            "available_dataset_families": self.available_dataset_families,
        }

    def csv_row(self) -> dict[str, object]:
        row = {field: self.as_dict().get(field) for field in PLUGIN_INSPECTION_FIELDNAMES}
        row["available_dataset_families"] = (
            ",".join(self.available_dataset_families) if self.available_dataset_families else None
        )
        return row

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def to_csv(self) -> str:
        return render_plugin_inspections_csv([self])


@dataclass(slots=True)
class PluginInspectionDiff:
    previous_plugin: str
    current_plugin: str
    changed_fields: list[str]
    changes: dict[str, dict[str, object | None]]

    def as_dict(self) -> dict[str, object]:
        return {
            "previous_plugin": self.previous_plugin,
            "current_plugin": self.current_plugin,
            "changed_fields": self.changed_fields,
            "changes": self.changes,
        }


@dataclass(slots=True)
class PluginInspectionBatch:
    plugins: list[PluginInspection]
    diffs: list[PluginInspectionDiff] | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "plugin_count": len(self.plugins),
            "plugins": [plugin.as_dict() for plugin in self.plugins],
        }
        if self.diffs is not None:
            payload["diffs"] = [diff.as_dict() for diff in self.diffs]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def to_csv(self) -> str:
        return render_plugin_inspections_csv(self.plugins)

    def to_markdown(self, *, page_links: dict[str, str] | None = None) -> str:
        lines = [
            "# Mini MapReduce plugin inspection",
            "",
            f"- Plugin count: `{len(self.plugins)}`",
            f"- Diff count: `{len(self.diffs or [])}`",
            "",
            "## Catalog quick links",
            "",
        ]
        for plugin in self.plugins:
            anchor = plugin_anchor_id(plugin)
            link_target = page_links.get(plugin.name) if page_links else f"#{anchor}"
            badges = " · ".join(f"`{badge}`" for badge in plugin_catalog_badges(plugin))
            dataset_families = ", ".join(plugin.available_dataset_families) if plugin.available_dataset_families else "-"
            lines.append(
                f"- [`{plugin.name}`]({link_target}) — {plugin.module_doc_summary or '-'} ({badges}; families: `{dataset_families}`)"
            )
        lines.extend([
            "",
            "## Plugin summary",
            "",
            "| Name | Plugin | Commit | Summary | Mapper | Reducer | Combiner | Benchmark generator | Benchmark note hook | Dataset families |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for plugin in self.plugins:
            dataset_families = ", ".join(plugin.available_dataset_families) if plugin.available_dataset_families else "-"
            mapper_meta = [f"`{plugin.mapper_signature or '-'}`"]
            if plugin.mapper_source_line is not None:
                mapper_meta.append(f"line {plugin.mapper_source_line}")
            if plugin.mapper_source_anchor:
                mapper_meta.append(plugin.mapper_source_anchor)
            if plugin.mapper_source_url:
                mapper_meta.append(f"[github]({plugin.mapper_source_url})")
            if plugin.mapper_source_commit_url:
                mapper_meta.append(f"[commit]({plugin.mapper_source_commit_url})")
            if plugin.mapper_doc_summary:
                mapper_meta.append(plugin.mapper_doc_summary)
            mapper_cell = f"`{plugin.mapper}`<br><small>{'<br>'.join(mapper_meta)}</small>"
            reducer_meta = [f"`{plugin.reducer_signature or '-'}`"]
            if plugin.reducer_source_line is not None:
                reducer_meta.append(f"line {plugin.reducer_source_line}")
            if plugin.reducer_source_anchor:
                reducer_meta.append(plugin.reducer_source_anchor)
            if plugin.reducer_source_url:
                reducer_meta.append(f"[github]({plugin.reducer_source_url})")
            if plugin.reducer_source_commit_url:
                reducer_meta.append(f"[commit]({plugin.reducer_source_commit_url})")
            if plugin.reducer_doc_summary:
                reducer_meta.append(plugin.reducer_doc_summary)
            reducer_cell = f"`{plugin.reducer}`<br><small>{'<br>'.join(reducer_meta)}</small>"
            combiner_name = plugin.combiner or '-'
            combiner_cell = "-"
            if plugin.combiner:
                combiner_meta = [f"`{plugin.combiner_signature or '-'}`"]
                if plugin.combiner_source_line is not None:
                    combiner_meta.append(f"line {plugin.combiner_source_line}")
                if plugin.combiner_source_anchor:
                    combiner_meta.append(plugin.combiner_source_anchor)
                if plugin.combiner_source_url:
                    combiner_meta.append(f"[github]({plugin.combiner_source_url})")
                if plugin.combiner_source_commit_url:
                    combiner_meta.append(f"[commit]({plugin.combiner_source_commit_url})")
                if plugin.combiner_doc_summary:
                    combiner_meta.append(plugin.combiner_doc_summary)
                combiner_cell = f"`{combiner_name}`<br><small>{'<br>'.join(combiner_meta)}</small>"
            benchmark_name = plugin.benchmark_generator or '-'
            benchmark_cell = "-"
            if plugin.benchmark_generator:
                benchmark_meta = [f"`{plugin.benchmark_generator_signature or '-'}`"]
                if plugin.benchmark_generator_source_line is not None:
                    benchmark_meta.append(f"line {plugin.benchmark_generator_source_line}")
                if plugin.benchmark_generator_source_anchor:
                    benchmark_meta.append(plugin.benchmark_generator_source_anchor)
                if plugin.benchmark_generator_source_url:
                    benchmark_meta.append(f"[github]({plugin.benchmark_generator_source_url})")
                if plugin.benchmark_generator_source_commit_url:
                    benchmark_meta.append(f"[commit]({plugin.benchmark_generator_source_commit_url})")
                if plugin.benchmark_generator_doc_summary:
                    benchmark_meta.append(plugin.benchmark_generator_doc_summary)
                benchmark_cell = f"`{benchmark_name}`<br><small>{'<br>'.join(benchmark_meta)}</small>"
            benchmark_note_name = plugin.benchmark_note_hook or '-'
            benchmark_note_cell = "-"
            if plugin.benchmark_note_hook:
                benchmark_note_meta = [f"`{plugin.benchmark_note_hook_signature or '-'}`"]
                if plugin.benchmark_note_hook_source_line is not None:
                    benchmark_note_meta.append(f"line {plugin.benchmark_note_hook_source_line}")
                if plugin.benchmark_note_hook_source_anchor:
                    benchmark_note_meta.append(plugin.benchmark_note_hook_source_anchor)
                if plugin.benchmark_note_hook_source_url:
                    benchmark_note_meta.append(f"[github]({plugin.benchmark_note_hook_source_url})")
                if plugin.benchmark_note_hook_source_commit_url:
                    benchmark_note_meta.append(f"[commit]({plugin.benchmark_note_hook_source_commit_url})")
                if plugin.benchmark_note_hook_doc_summary:
                    benchmark_note_meta.append(plugin.benchmark_note_hook_doc_summary)
                benchmark_note_cell = f"`{benchmark_note_name}`<br><small>{'<br>'.join(benchmark_note_meta)}</small>"
            commit_cell = f"`{plugin.plugin_repo_commit[:12]}`" if plugin.plugin_repo_commit else "-"
            lines.append(
                f"| `{plugin.name}` | `{plugin_display_path(plugin.plugin)}` | {commit_cell} | {plugin.module_doc_summary or '-'} | {mapper_cell} | {reducer_cell} | {combiner_cell} | {benchmark_cell} | {benchmark_note_cell} | `{dataset_families}` |"
            )
        lines.extend(["", "## Hook source excerpts", ""])
        for plugin in self.plugins:
            lines.append(f"### <a id=\"{plugin_anchor_id(plugin)}\"></a>`{plugin.name}`")
            lines.append("")
            if plugin.plugin_repo_commit:
                lines.append(f"- Repository commit: `{plugin.plugin_repo_commit}`")
            hook_sections = [
                ("Mapper", plugin.mapper, plugin.mapper_source_anchor, plugin.mapper_source_url, plugin.mapper_source_commit_url, plugin.mapper_source_excerpt),
                ("Reducer", plugin.reducer, plugin.reducer_source_anchor, plugin.reducer_source_url, plugin.reducer_source_commit_url, plugin.reducer_source_excerpt),
                ("Combiner", plugin.combiner, plugin.combiner_source_anchor, plugin.combiner_source_url, plugin.combiner_source_commit_url, plugin.combiner_source_excerpt),
                ("Benchmark generator", plugin.benchmark_generator, plugin.benchmark_generator_source_anchor, plugin.benchmark_generator_source_url, plugin.benchmark_generator_source_commit_url, plugin.benchmark_generator_source_excerpt),
                ("Benchmark note hook", plugin.benchmark_note_hook, plugin.benchmark_note_hook_source_anchor, plugin.benchmark_note_hook_source_url, plugin.benchmark_note_hook_source_commit_url, plugin.benchmark_note_hook_source_excerpt),
            ]
            for label, hook_name, source_anchor, source_url, source_commit_url, excerpt in hook_sections:
                if not hook_name or not excerpt:
                    continue
                lines.append(f"#### {label}: `{hook_name}`")
                if source_anchor:
                    lines.append(f"- Source anchor: `{source_anchor}`")
                if source_url:
                    lines.append(f"- GitHub source: <{source_url}>")
                if source_commit_url:
                    lines.append(f"- GitHub source (commit pinned): <{source_commit_url}>")
                lines.extend(["", "```python", excerpt, "```", ""])
        if self.diffs:
            lines.extend(["", "## Adjacent diffs", ""])
            for index, diff in enumerate(self.diffs, start=1):
                lines.append(
                    f"### Diff {index}: `{plugin_display_path(diff.previous_plugin)}` → `{plugin_display_path(diff.current_plugin)}`"
                )
                if not diff.changed_fields:
                    lines.append("- No contract changes detected.")
                    lines.append("")
                    continue
                lines.append(f"- Changed fields: `{', '.join(diff.changed_fields)}`")
                lines.append("")
                lines.append("| Field | Previous | Current |")
                lines.append("| --- | --- | --- |")
                for field in diff.changed_fields:
                    change = diff.changes[field]
                    previous_value = change["previous"]
                    current_value = change["current"]
                    if field == "plugin":
                        previous_value = plugin_display_path(str(previous_value)) if previous_value is not None else None
                        current_value = plugin_display_path(str(current_value)) if current_value is not None else None
                    previous = json.dumps(previous_value, sort_keys=True)
                    current = json.dumps(current_value, sort_keys=True)
                    lines.append(f"| `{field}` | `{previous}` | `{current}` |")
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def to_html(self, *, page_links: dict[str, str] | None = None) -> str:
        def esc(value: object) -> str:
            return html.escape(str(value), quote=True)

        quick_link_cards = []
        plugin_rows = []
        for plugin in self.plugins:
            anchor = plugin_anchor_id(plugin)
            card_href = page_links.get(plugin.name) if page_links else f"#{anchor}"
            dataset_families = ", ".join(plugin.available_dataset_families) if plugin.available_dataset_families else "-"
            badges_html = "".join(f"<span class=\"badge\">{esc(badge)}</span>" for badge in plugin_catalog_badges(plugin))
            quick_link_cards.append(
                "<li>"
                f"<a href=\"{esc(card_href)}\"><strong><code>{esc(plugin.name)}</code></strong></a>"
                f"<p>{esc(plugin.module_doc_summary or '-')}</p>"
                f"<p><small>{badges_html} <span class=\"badge\">families: {esc(dataset_families)}</span></small></p>"
                "</li>"
            )
            plugin_rows.append(
                "<tr>"
                f"<td><a href=\"#{esc(anchor)}\"><code>{esc(plugin.name)}</code></a></td>"
                f"<td><code>{esc(plugin_display_path(plugin.plugin))}</code></td>"
                f"<td><code>{esc(plugin.plugin_repo_commit[:12] if plugin.plugin_repo_commit else '-')}</code></td>"
                f"<td>{esc(plugin.module_doc_summary or '-')}</td>"
                f"<td>{_render_hook_html(plugin.mapper, plugin.mapper_signature, plugin.mapper_doc_summary, plugin.mapper_source_line, plugin.mapper_source_anchor, plugin.mapper_source_url, plugin.mapper_source_commit_url)}</td>"
                f"<td>{_render_hook_html(plugin.reducer, plugin.reducer_signature, plugin.reducer_doc_summary, plugin.reducer_source_line, plugin.reducer_source_anchor, plugin.reducer_source_url, plugin.reducer_source_commit_url)}</td>"
                f"<td>{_render_hook_html(plugin.combiner, plugin.combiner_signature, plugin.combiner_doc_summary, plugin.combiner_source_line, plugin.combiner_source_anchor, plugin.combiner_source_url, plugin.combiner_source_commit_url)}</td>"
                f"<td>{_render_hook_html(plugin.benchmark_generator, plugin.benchmark_generator_signature, plugin.benchmark_generator_doc_summary, plugin.benchmark_generator_source_line, plugin.benchmark_generator_source_anchor, plugin.benchmark_generator_source_url, plugin.benchmark_generator_source_commit_url)}</td>"
                f"<td>{_render_hook_html(plugin.benchmark_note_hook, plugin.benchmark_note_hook_signature, plugin.benchmark_note_hook_doc_summary, plugin.benchmark_note_hook_source_line, plugin.benchmark_note_hook_source_anchor, plugin.benchmark_note_hook_source_url, plugin.benchmark_note_hook_source_commit_url)}</td>"
                f"<td><code>{esc(dataset_families)}</code></td>"
                "</tr>"
            )

        source_sections = []
        for plugin in self.plugins:
            hook_blocks = []
            for label, hook_name, source_anchor, source_url, source_commit_url, excerpt in [
                ("Mapper", plugin.mapper, plugin.mapper_source_anchor, plugin.mapper_source_url, plugin.mapper_source_commit_url, plugin.mapper_source_excerpt),
                ("Reducer", plugin.reducer, plugin.reducer_source_anchor, plugin.reducer_source_url, plugin.reducer_source_commit_url, plugin.reducer_source_excerpt),
                ("Combiner", plugin.combiner, plugin.combiner_source_anchor, plugin.combiner_source_url, plugin.combiner_source_commit_url, plugin.combiner_source_excerpt),
                ("Benchmark generator", plugin.benchmark_generator, plugin.benchmark_generator_source_anchor, plugin.benchmark_generator_source_url, plugin.benchmark_generator_source_commit_url, plugin.benchmark_generator_source_excerpt),
                ("Benchmark note hook", plugin.benchmark_note_hook, plugin.benchmark_note_hook_source_anchor, plugin.benchmark_note_hook_source_url, plugin.benchmark_note_hook_source_commit_url, plugin.benchmark_note_hook_source_excerpt),
            ]:
                if not hook_name or not excerpt:
                    continue
                anchor_html = f"<p><strong>Source anchor:</strong> <code>{esc(source_anchor)}</code></p>" if source_anchor else ""
                source_url_html = (
                    f"<p><strong>GitHub source:</strong> <a href=\"{esc(source_url)}\">{esc(source_url)}</a></p>"
                    if source_url
                    else ""
                )
                source_commit_url_html = (
                    f"<p><strong>GitHub source (commit pinned):</strong> <a href=\"{esc(source_commit_url)}\">{esc(source_commit_url)}</a></p>"
                    if source_commit_url
                    else ""
                )
                hook_blocks.append(
                    f"<article><h3>{esc(label)}: <code>{esc(hook_name)}</code></h3>{anchor_html}{source_url_html}{source_commit_url_html}<pre><code>{esc(excerpt)}</code></pre></article>"
                )
            repo_commit_html = f"<p><strong>Repository commit:</strong> <code>{esc(plugin.plugin_repo_commit)}</code></p>" if plugin.plugin_repo_commit else ""
            source_sections.append(
                f"<section id=\"{esc(plugin_anchor_id(plugin))}\"><h2>Hook source excerpts: <code>{esc(plugin.name)}</code></h2>{repo_commit_html}{''.join(hook_blocks)}</section>"
            )

        diff_sections = []
        for index, diff in enumerate(self.diffs or [], start=1):
            previous_plugin = plugin_display_path(diff.previous_plugin)
            current_plugin = plugin_display_path(diff.current_plugin)
            if not diff.changed_fields:
                diff_sections.append(
                    f"<section><h2>Diff {index}: <code>{esc(previous_plugin)}</code> → <code>{esc(current_plugin)}</code></h2><p>No contract changes detected.</p></section>"
                )
                continue
            diff_rows = []
            for field in diff.changed_fields:
                change = diff.changes[field]
                previous_value = change["previous"]
                current_value = change["current"]
                if field == "plugin":
                    previous_value = plugin_display_path(str(previous_value)) if previous_value is not None else None
                    current_value = plugin_display_path(str(current_value)) if current_value is not None else None
                diff_rows.append(
                    "<tr>"
                    f"<td><code>{esc(field)}</code></td>"
                    f"<td><code>{esc(json.dumps(previous_value, sort_keys=True))}</code></td>"
                    f"<td><code>{esc(json.dumps(current_value, sort_keys=True))}</code></td>"
                    "</tr>"
                )
            diff_sections.append(
                "<section>"
                f"<h2>Diff {index}: <code>{esc(previous_plugin)}</code> → <code>{esc(current_plugin)}</code></h2>"
                f"<p><strong>Changed fields:</strong> <code>{esc(', '.join(diff.changed_fields))}</code></p>"
                "<table><thead><tr><th>Field</th><th>Previous</th><th>Current</th></tr></thead>"
                f"<tbody>{''.join(diff_rows)}</tbody></table>"
                "</section>"
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini MapReduce plugin inspection</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1200px; padding: 0 1rem 3rem; line-height: 1.5; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid rgba(148, 163, 184, 0.35); padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }}
    thead th {{ background: rgba(148, 163, 184, 0.14); }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1rem 0 2rem; }}
    .meta li {{ list-style: none; padding: 0.75rem 0.9rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.75rem; }}
    .catalog-links {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.9rem; padding: 0; }}
    .catalog-links li {{ list-style: none; padding: 0.9rem 1rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.85rem; background: rgba(148, 163, 184, 0.08); }}
    .catalog-links p {{ margin: 0.45rem 0; }}
    .badge {{ display: inline-block; margin: 0.15rem 0.3rem 0.15rem 0; padding: 0.15rem 0.45rem; border-radius: 999px; border: 1px solid rgba(148, 163, 184, 0.35); background: rgba(59, 130, 246, 0.10); }}
    section {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Mini MapReduce plugin inspection</h1>
  <ul class="meta">
    <li><strong>Plugin count</strong><br><code>{esc(len(self.plugins))}</code></li>
    <li><strong>Diff count</strong><br><code>{esc(len(self.diffs or []))}</code></li>
  </ul>
  <section>
    <h2>Catalog quick links</h2>
    <ul class="catalog-links">{''.join(quick_link_cards)}</ul>
  </section>
  <section>
    <h2>Plugin summary</h2>
    <table>
      <thead><tr><th>Name</th><th>Plugin</th><th>Commit</th><th>Summary</th><th>Mapper</th><th>Reducer</th><th>Combiner</th><th>Benchmark generator</th><th>Benchmark note hook</th><th>Dataset families</th></tr></thead>
      <tbody>{''.join(plugin_rows)}</tbody>
    </table>
  </section>
  {''.join(source_sections)}
  {''.join(diff_sections)}
</body>
</html>
"""


@dataclass(slots=True)
class PluginReleaseEntry:
    name: str
    plugin: str
    module_doc_summary: str | None
    available_dataset_families: list[str] | None
    plugin_repo_commit: str | None

    @classmethod
    def from_plugin(cls, plugin: PluginInspection) -> "PluginReleaseEntry":
        return cls(
            name=plugin.name,
            plugin=plugin_display_path(plugin.plugin),
            module_doc_summary=plugin.module_doc_summary,
            available_dataset_families=list(plugin.available_dataset_families) if plugin.available_dataset_families else None,
            plugin_repo_commit=plugin.plugin_repo_commit,
        )

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "plugin": self.plugin,
            "module_doc_summary": self.module_doc_summary,
            "available_dataset_families": list(self.available_dataset_families) if self.available_dataset_families else None,
            "plugin_repo_commit": self.plugin_repo_commit,
        }


@dataclass(slots=True)
class PluginReleaseChange:
    name: str
    before: PluginReleaseEntry
    after: PluginReleaseEntry
    changed_fields: list[str]
    changes: dict[str, dict[str, object | None]]
    added_dataset_families: list[str]
    removed_dataset_families: list[str]
    added_hooks: list[str]
    removed_hooks: list[str]
    changed_hooks: list[str]

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "before": self.before.as_dict(),
            "after": self.after.as_dict(),
            "changed_fields": list(self.changed_fields),
            "changes": self.changes,
            "added_dataset_families": list(self.added_dataset_families),
            "removed_dataset_families": list(self.removed_dataset_families),
            "added_hooks": list(self.added_hooks),
            "removed_hooks": list(self.removed_hooks),
            "changed_hooks": list(self.changed_hooks),
        }


@dataclass(slots=True)
class PluginReleaseComparison:
    before_label: str
    after_label: str
    before_plugin_count: int
    after_plugin_count: int
    before_commits: list[str]
    after_commits: list[str]
    added_plugins: list[PluginReleaseEntry]
    removed_plugins: list[PluginReleaseEntry]
    changed_plugins: list[PluginReleaseChange]
    unchanged_plugins: list[str]

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "before_label": self.before_label,
            "after_label": self.after_label,
            "before_plugin_count": self.before_plugin_count,
            "after_plugin_count": self.after_plugin_count,
            "before_commits": list(self.before_commits),
            "after_commits": list(self.after_commits),
            "added_plugins": [entry.as_dict() for entry in self.added_plugins],
            "removed_plugins": [entry.as_dict() for entry in self.removed_plugins],
            "changed_plugins": [change.as_dict() for change in self.changed_plugins],
            "unchanged_plugins": list(self.unchanged_plugins),
            "summary": {
                "added": len(self.added_plugins),
                "removed": len(self.removed_plugins),
                "changed": len(self.changed_plugins),
                "unchanged": len(self.unchanged_plugins),
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# Mini MapReduce plugin release comparison",
            "",
            f"- Before snapshot: `{self.before_label}` (`{self.before_plugin_count}` plugins; commits: `{', '.join(self.before_commits) if self.before_commits else '-'}`)",
            f"- After snapshot: `{self.after_label}` (`{self.after_plugin_count}` plugins; commits: `{', '.join(self.after_commits) if self.after_commits else '-'}`)",
            f"- Summary: `{len(self.added_plugins)}` added · `{len(self.removed_plugins)}` removed · `{len(self.changed_plugins)}` changed · `{len(self.unchanged_plugins)}` unchanged",
            "",
        ]

        def render_entries(title: str, entries: list[PluginReleaseEntry], empty_message: str) -> None:
            lines.extend([f"## {title}", ""])
            if not entries:
                lines.append(f"- {empty_message}")
                lines.append("")
                return
            lines.extend([
                "| Plugin | Summary | Dataset families | Commit |",
                "| --- | --- | --- | --- |",
            ])
            for entry in entries:
                dataset_families = ", ".join(entry.available_dataset_families) if entry.available_dataset_families else "-"
                commit = f"`{entry.plugin_repo_commit[:12]}`" if entry.plugin_repo_commit else "-"
                lines.append(
                    f"| `{entry.name}`<br><small>`{plugin_display_path(entry.plugin)}`</small> | {entry.module_doc_summary or '-'} | `{dataset_families}` | {commit} |"
                )
            lines.append("")

        render_entries("Added plugins", self.added_plugins, "No plugins were added between these snapshots.")
        render_entries("Removed plugins", self.removed_plugins, "No plugins were removed between these snapshots.")

        lines.extend(["## Changed plugins", ""])
        if self.changed_plugins:
            lines.extend([
                "| Plugin | Hook delta | Dataset-family delta | Changed fields |",
                "| --- | --- | --- | --- |",
            ])
            for change in self.changed_plugins:
                hook_bits = []
                if change.added_hooks:
                    hook_bits.append(f"+ {', '.join(change.added_hooks)}")
                if change.removed_hooks:
                    hook_bits.append(f"- {', '.join(change.removed_hooks)}")
                if change.changed_hooks:
                    hook_bits.append(f"~ {', '.join(change.changed_hooks)}")
                dataset_bits = []
                if change.added_dataset_families:
                    dataset_bits.append(f"+ {', '.join(change.added_dataset_families)}")
                if change.removed_dataset_families:
                    dataset_bits.append(f"- {', '.join(change.removed_dataset_families)}")
                hook_delta = "<br>".join(hook_bits) if hook_bits else "-"
                dataset_delta = "<br>".join(dataset_bits) if dataset_bits else "-"
                lines.append(
                    f"| `{change.name}` | {hook_delta} | {dataset_delta} | `{', '.join(change.changed_fields)}` |"
                )
            lines.append("")
            for change in self.changed_plugins:
                lines.append(f"### `{change.name}`")
                lines.append("")
                lines.append(f"- Before: `{plugin_display_path(change.before.plugin)}`")
                lines.append(f"- After: `{plugin_display_path(change.after.plugin)}`")
                if change.added_hooks:
                    lines.append(f"- Added hooks: `{', '.join(change.added_hooks)}`")
                if change.removed_hooks:
                    lines.append(f"- Removed hooks: `{', '.join(change.removed_hooks)}`")
                if change.changed_hooks:
                    lines.append(f"- Changed hooks: `{', '.join(change.changed_hooks)}`")
                if change.added_dataset_families or change.removed_dataset_families:
                    lines.append(
                        f"- Dataset-family delta: `+ {', '.join(change.added_dataset_families) if change.added_dataset_families else '-'}` / `- {', '.join(change.removed_dataset_families) if change.removed_dataset_families else '-'}`"
                    )
                lines.extend(["", "| Field | Before | After |", "| --- | --- | --- |"])
                for field in change.changed_fields:
                    field_change = change.changes[field]
                    before_value = field_change["before"]
                    after_value = field_change["after"]
                    if field == "plugin":
                        before_rendered = json.dumps(plugin_display_path(str(before_value)), sort_keys=True) if before_value is not None else "null"
                        after_rendered = json.dumps(plugin_display_path(str(after_value)), sort_keys=True) if after_value is not None else "null"
                    else:
                        before_rendered = json.dumps(before_value, sort_keys=True)
                        after_rendered = json.dumps(after_value, sort_keys=True)
                    lines.append(f"| `{field}` | `{before_rendered}` | `{after_rendered}` |")
                lines.append("")
        else:
            lines.append("- No shared plugins changed contract between these snapshots.")
            lines.append("")

        lines.extend([
            "## Unchanged plugins",
            "",
            f"- `{', '.join(self.unchanged_plugins)}`" if self.unchanged_plugins else "- No unchanged shared plugins between these snapshots.",
            "",
        ])
        return "\n".join(lines).rstrip() + "\n"

    def to_html(self) -> str:
        def esc(value: object) -> str:
            return html.escape(str(value), quote=True)

        def entries_table(entries: list[PluginReleaseEntry], empty_message: str) -> str:
            if not entries:
                return f"<p>{esc(empty_message)}</p>"
            rows = []
            for entry in entries:
                dataset_families = ", ".join(entry.available_dataset_families) if entry.available_dataset_families else "-"
                commit = entry.plugin_repo_commit[:12] if entry.plugin_repo_commit else "-"
                rows.append(
                    "<tr>"
                    f"<td><code>{esc(entry.name)}</code><br><small><code>{esc(plugin_display_path(entry.plugin))}</code></small></td>"
                    f"<td>{esc(entry.module_doc_summary or '-')}</td>"
                    f"<td><code>{esc(dataset_families)}</code></td>"
                    f"<td><code>{esc(commit)}</code></td>"
                    "</tr>"
                )
            return "<table><thead><tr><th>Plugin</th><th>Summary</th><th>Dataset families</th><th>Commit</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

        changed_rows = []
        changed_sections = []
        for change in self.changed_plugins:
            hook_bits = []
            if change.added_hooks:
                hook_bits.append(f"+ {', '.join(change.added_hooks)}")
            if change.removed_hooks:
                hook_bits.append(f"- {', '.join(change.removed_hooks)}")
            if change.changed_hooks:
                hook_bits.append(f"~ {', '.join(change.changed_hooks)}")
            dataset_bits = []
            if change.added_dataset_families:
                dataset_bits.append(f"+ {', '.join(change.added_dataset_families)}")
            if change.removed_dataset_families:
                dataset_bits.append(f"- {', '.join(change.removed_dataset_families)}")
            changed_rows.append(
                "<tr>"
                f"<td><code>{esc(change.name)}</code></td>"
                f"<td>{esc(' | '.join(hook_bits) if hook_bits else '-')}</td>"
                f"<td>{esc(' | '.join(dataset_bits) if dataset_bits else '-')}</td>"
                f"<td><code>{esc(', '.join(change.changed_fields))}</code></td>"
                "</tr>"
            )
            diff_rows = []
            for field in change.changed_fields:
                field_change = change.changes[field]
                before_value = field_change["before"]
                after_value = field_change["after"]
                if field == "plugin":
                    before_value = plugin_display_path(str(before_value)) if before_value is not None else None
                    after_value = plugin_display_path(str(after_value)) if after_value is not None else None
                diff_rows.append(
                    "<tr>"
                    f"<td><code>{esc(field)}</code></td>"
                    f"<td><code>{esc(json.dumps(before_value, sort_keys=True))}</code></td>"
                    f"<td><code>{esc(json.dumps(after_value, sort_keys=True))}</code></td>"
                    "</tr>"
                )
            details = [
                f"<p><strong>Before:</strong> <code>{esc(plugin_display_path(change.before.plugin))}</code></p>",
                f"<p><strong>After:</strong> <code>{esc(plugin_display_path(change.after.plugin))}</code></p>",
            ]
            if change.added_hooks:
                details.append(f"<p><strong>Added hooks:</strong> <code>{esc(', '.join(change.added_hooks))}</code></p>")
            if change.removed_hooks:
                details.append(f"<p><strong>Removed hooks:</strong> <code>{esc(', '.join(change.removed_hooks))}</code></p>")
            if change.changed_hooks:
                details.append(f"<p><strong>Changed hooks:</strong> <code>{esc(', '.join(change.changed_hooks))}</code></p>")
            if change.added_dataset_families or change.removed_dataset_families:
                details.append(
                    f"<p><strong>Dataset-family delta:</strong> + <code>{esc(', '.join(change.added_dataset_families) if change.added_dataset_families else '-')}</code> / - <code>{esc(', '.join(change.removed_dataset_families) if change.removed_dataset_families else '-')}</code></p>"
                )
            changed_sections.append(
                "<section>"
                f"<h3><code>{esc(change.name)}</code></h3>"
                f"{''.join(details)}"
                "<table><thead><tr><th>Field</th><th>Before</th><th>After</th></tr></thead>"
                f"<tbody>{''.join(diff_rows)}</tbody></table>"
                "</section>"
            )

        unchanged_html = f"<p><code>{esc(', '.join(self.unchanged_plugins))}</code></p>" if self.unchanged_plugins else "<p>No unchanged shared plugins between these snapshots.</p>"

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini MapReduce plugin release comparison</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1180px; padding: 0 1rem 3rem; line-height: 1.5; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid rgba(148, 163, 184, 0.35); padding: 0.55rem 0.7rem; text-align: left; vertical-align: top; }}
    thead th {{ background: rgba(148, 163, 184, 0.14); }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.8rem; padding: 0; }}
    .meta li {{ list-style: none; padding: 0.85rem 0.95rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.9rem; }}
    section {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Mini MapReduce plugin release comparison</h1>
  <ul class="meta">
    <li><strong>Before snapshot</strong><br><code>{esc(self.before_label)}</code><br><small>{esc(str(self.before_plugin_count))} plugins</small></li>
    <li><strong>After snapshot</strong><br><code>{esc(self.after_label)}</code><br><small>{esc(str(self.after_plugin_count))} plugins</small></li>
    <li><strong>Added / removed</strong><br><code>{esc(f"{len(self.added_plugins)} / {len(self.removed_plugins)}")}</code></li>
    <li><strong>Changed / unchanged</strong><br><code>{esc(f"{len(self.changed_plugins)} / {len(self.unchanged_plugins)}")}</code></li>
  </ul>
  <p><strong>Before commits:</strong> <code>{esc(', '.join(self.before_commits) if self.before_commits else '-')}</code><br>
     <strong>After commits:</strong> <code>{esc(', '.join(self.after_commits) if self.after_commits else '-')}</code></p>
  <section>
    <h2>Added plugins</h2>
    {entries_table(self.added_plugins, 'No plugins were added between these snapshots.')}
  </section>
  <section>
    <h2>Removed plugins</h2>
    {entries_table(self.removed_plugins, 'No plugins were removed between these snapshots.')}
  </section>
  <section>
    <h2>Changed plugins</h2>
    {'<table><thead><tr><th>Plugin</th><th>Hook delta</th><th>Dataset-family delta</th><th>Changed fields</th></tr></thead><tbody>' + ''.join(changed_rows) + '</tbody></table>' if changed_rows else '<p>No shared plugins changed contract between these snapshots.</p>'}
    {''.join(changed_sections)}
  </section>
  <section>
    <h2>Unchanged plugins</h2>
    {unchanged_html}
  </section>
</body>
</html>'''


def plugin_inspection_from_payload(payload: dict[str, object]) -> PluginInspection:
    if not isinstance(payload, dict):
        raise ValueError("plugin inspection payload must be an object")
    values: dict[str, object | None] = {}
    for field in fields(PluginInspection):
        value = payload.get(field.name)
        if field.name == "available_dataset_families" and value is not None:
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("available_dataset_families must be a list of strings when present")
            value = list(value)
        elif field.name.endswith("_source_line") and value is not None:
            value = int(value)
        values[field.name] = value
    for required in ("name", "plugin", "mapper", "reducer"):
        if not values.get(required):
            raise ValueError(f"plugin inspection payload missing required field: {required}")
    return PluginInspection(**values)


def load_plugin_inspection_snapshot(path: str | Path) -> PluginInspectionBatch:
    snapshot_path = Path(path)
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"plugin inspection snapshot must be a JSON object: {snapshot_path}")
    if "plugins" in payload:
        plugins_payload = payload.get("plugins")
        if not isinstance(plugins_payload, list) or not plugins_payload:
            raise ValueError(f"plugin inspection snapshot must include a non-empty plugins list: {snapshot_path}")
        plugins = [plugin_inspection_from_payload(item) for item in plugins_payload]
    else:
        plugins = [plugin_inspection_from_payload(payload)]
    return PluginInspectionBatch(plugins=plugins)


def _index_plugins_by_name(plugins: list[PluginInspection], label: str) -> dict[str, PluginInspection]:
    indexed: dict[str, PluginInspection] = {}
    duplicates: list[str] = []
    for plugin in plugins:
        if plugin.name in indexed:
            duplicates.append(plugin.name)
            continue
        indexed[plugin.name] = plugin
    if duplicates:
        duplicate_names = ", ".join(sorted(set(duplicates)))
        raise ValueError(f"duplicate plugin names in {label} snapshot: {duplicate_names}")
    return indexed


def compare_plugin_release_snapshots(
    before_snapshot: PluginInspectionBatch,
    after_snapshot: PluginInspectionBatch,
    *,
    before_label: str | None = None,
    after_label: str | None = None,
) -> PluginReleaseComparison:
    before_by_name = _index_plugins_by_name(before_snapshot.plugins, before_label or "before")
    after_by_name = _index_plugins_by_name(after_snapshot.plugins, after_label or "after")
    before_commits = sorted({plugin.plugin_repo_commit for plugin in before_snapshot.plugins if plugin.plugin_repo_commit})
    after_commits = sorted({plugin.plugin_repo_commit for plugin in after_snapshot.plugins if plugin.plugin_repo_commit})

    added_plugins: list[PluginReleaseEntry] = []
    removed_plugins: list[PluginReleaseEntry] = []
    changed_plugins: list[PluginReleaseChange] = []
    unchanged_plugins: list[str] = []

    for name in sorted(set(before_by_name) | set(after_by_name)):
        before = before_by_name.get(name)
        after = after_by_name.get(name)
        if before is None and after is not None:
            added_plugins.append(PluginReleaseEntry.from_plugin(after))
            continue
        if after is None and before is not None:
            removed_plugins.append(PluginReleaseEntry.from_plugin(before))
            continue
        assert before is not None and after is not None
        before_payload = before.as_dict()
        after_payload = after.as_dict()
        before_payload["plugin"] = plugin_display_path(str(before_payload["plugin"]))
        after_payload["plugin"] = plugin_display_path(str(after_payload["plugin"]))
        changes: dict[str, dict[str, object | None]] = {}
        for field in PLUGIN_RELEASE_DIFF_FIELDS:
            if before_payload[field] != after_payload[field]:
                changes[field] = {
                    "before": before_payload[field],
                    "after": after_payload[field],
                }
        if not changes:
            unchanged_plugins.append(name)
            continue
        before_families = set(before.available_dataset_families or [])
        after_families = set(after.available_dataset_families or [])
        added_hooks: list[str] = []
        removed_hooks: list[str] = []
        changed_hooks: list[str] = []
        for label, name_field, signature_field in PLUGIN_RELEASE_HOOK_FIELDS:
            before_name = getattr(before, name_field)
            after_name = getattr(after, name_field)
            before_signature = getattr(before, signature_field)
            after_signature = getattr(after, signature_field)
            if before_name and not after_name:
                removed_hooks.append(label)
            elif after_name and not before_name:
                added_hooks.append(label)
            elif before_name != after_name or before_signature != after_signature:
                changed_hooks.append(label)
        changed_plugins.append(
            PluginReleaseChange(
                name=name,
                before=PluginReleaseEntry.from_plugin(before),
                after=PluginReleaseEntry.from_plugin(after),
                changed_fields=sorted(changes),
                changes=changes,
                added_dataset_families=sorted(after_families - before_families),
                removed_dataset_families=sorted(before_families - after_families),
                added_hooks=added_hooks,
                removed_hooks=removed_hooks,
                changed_hooks=changed_hooks,
            )
        )

    return PluginReleaseComparison(
        before_label=before_label or "before",
        after_label=after_label or "after",
        before_plugin_count=len(before_snapshot.plugins),
        after_plugin_count=len(after_snapshot.plugins),
        before_commits=before_commits,
        after_commits=after_commits,
        added_plugins=added_plugins,
        removed_plugins=removed_plugins,
        changed_plugins=changed_plugins,
        unchanged_plugins=unchanged_plugins,
    )


def plugin_anchor_id(plugin: PluginInspection) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in plugin.name.lower()).strip("-")
    return slug or "plugin"


def plugin_catalog_badges(plugin: PluginInspection) -> list[str]:
    hook_count = 2 + int(bool(plugin.combiner)) + int(bool(plugin.benchmark_generator)) + int(bool(plugin.benchmark_note_hook))
    badges = [f"{hook_count} hooks"]
    if plugin.available_dataset_families:
        badges.append(f"{len(plugin.available_dataset_families)} dataset families")
    else:
        badges.append("no dataset families")
    if plugin.plugin_repo_commit:
        badges.append("commit pinned")
    if plugin.mapper_source_url and plugin.reducer_source_url:
        badges.append("github linked")
    return badges


def plugin_display_path(plugin_ref: str) -> str:
    plugin_path = Path(plugin_ref)
    try:
        resolved = plugin_path.resolve(strict=False)
    except OSError:
        return plugin_ref
    repo = _github_repo_blob_base(resolved)
    if repo is not None:
        _, root = repo
        try:
            return resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return plugin_ref


def plugin_hook_rows(plugin: PluginInspection) -> list[dict[str, object | None]]:
    return [
        {
            "label": "Mapper",
            "name": plugin.mapper,
            "signature": plugin.mapper_signature,
            "doc_summary": plugin.mapper_doc_summary,
            "source_line": plugin.mapper_source_line,
            "source_anchor": plugin.mapper_source_anchor,
            "source_url": plugin.mapper_source_url,
            "source_commit_url": plugin.mapper_source_commit_url,
            "source_excerpt": plugin.mapper_source_excerpt,
        },
        {
            "label": "Reducer",
            "name": plugin.reducer,
            "signature": plugin.reducer_signature,
            "doc_summary": plugin.reducer_doc_summary,
            "source_line": plugin.reducer_source_line,
            "source_anchor": plugin.reducer_source_anchor,
            "source_url": plugin.reducer_source_url,
            "source_commit_url": plugin.reducer_source_commit_url,
            "source_excerpt": plugin.reducer_source_excerpt,
        },
        {
            "label": "Combiner",
            "name": plugin.combiner,
            "signature": plugin.combiner_signature,
            "doc_summary": plugin.combiner_doc_summary,
            "source_line": plugin.combiner_source_line,
            "source_anchor": plugin.combiner_source_anchor,
            "source_url": plugin.combiner_source_url,
            "source_commit_url": plugin.combiner_source_commit_url,
            "source_excerpt": plugin.combiner_source_excerpt,
        },
        {
            "label": "Benchmark generator",
            "name": plugin.benchmark_generator,
            "signature": plugin.benchmark_generator_signature,
            "doc_summary": plugin.benchmark_generator_doc_summary,
            "source_line": plugin.benchmark_generator_source_line,
            "source_anchor": plugin.benchmark_generator_source_anchor,
            "source_url": plugin.benchmark_generator_source_url,
            "source_commit_url": plugin.benchmark_generator_source_commit_url,
            "source_excerpt": plugin.benchmark_generator_source_excerpt,
        },
        {
            "label": "Benchmark note hook",
            "name": plugin.benchmark_note_hook,
            "signature": plugin.benchmark_note_hook_signature,
            "doc_summary": plugin.benchmark_note_hook_doc_summary,
            "source_line": plugin.benchmark_note_hook_source_line,
            "source_anchor": plugin.benchmark_note_hook_source_anchor,
            "source_url": plugin.benchmark_note_hook_source_url,
            "source_commit_url": plugin.benchmark_note_hook_source_commit_url,
            "source_excerpt": plugin.benchmark_note_hook_source_excerpt,
        },
    ]


def plugin_doc_basename(plugin: PluginInspection, suffix: str) -> str:
    return f"{plugin_anchor_id(plugin)}{suffix}"


def build_plugin_page_links(
    plugins: list[PluginInspection],
    *,
    docs_dir: Path,
    output_parent: Path,
    suffix: str,
) -> dict[str, str]:
    links: dict[str, str] = {}
    for plugin in plugins:
        doc_path = docs_dir / plugin_doc_basename(plugin, suffix)
        links[plugin.name] = Path(os.path.relpath(doc_path, start=output_parent)).as_posix()
    return links


def render_plugin_doc_markdown(
    plugin: PluginInspection,
    *,
    catalog_link: str | None = None,
    html_page_link: str | None = None,
) -> str:
    dataset_families = ", ".join(plugin.available_dataset_families) if plugin.available_dataset_families else "-"
    badges = " · ".join(f"`{badge}`" for badge in plugin_catalog_badges(plugin))
    lines = [
        f"# Mini MapReduce plugin doc: `{plugin.name}`",
        "",
        "## Snapshot",
        "",
        f"- Plugin path: `{plugin_display_path(plugin.plugin)}`",
        f"- Summary: {plugin.module_doc_summary or '-'}",
        f"- Dataset families: `{dataset_families}`",
        f"- Catalog badges: {badges}",
    ]
    if plugin.plugin_repo_commit:
        lines.append(f"- Repository commit: `{plugin.plugin_repo_commit}`")
    if catalog_link:
        lines.append(f"- Catalog index: [plugin catalog]({catalog_link})")
    if html_page_link:
        lines.append(f"- Alternate format: [HTML]({html_page_link})")
    lines.extend([
        "",
        "## Hook summary",
        "",
        "| Hook | Export | Signature | Details | Source |",
        "| --- | --- | --- | --- | --- |",
    ])
    for hook in plugin_hook_rows(plugin):
        if not hook["name"]:
            continue
        details: list[str] = []
        if hook["doc_summary"]:
            details.append(str(hook["doc_summary"]))
        if hook["source_line"] is not None:
            details.append(f"line {hook['source_line']}")
        if hook["source_anchor"]:
            details.append(f"anchor `{hook['source_anchor']}`")
        source_bits: list[str] = []
        if hook["source_url"]:
            source_bits.append(f"[github]({hook['source_url']})")
        if hook["source_commit_url"]:
            source_bits.append(f"[commit]({hook['source_commit_url']})")
        lines.append(
            f"| {hook['label']} | `{hook['name']}` | `{hook['signature'] or '-'}` | {'<br>'.join(details) or '-'} | {'<br>'.join(source_bits) or '-'} |"
        )
    lines.extend(["", "## Hook source excerpts", ""])
    for hook in plugin_hook_rows(plugin):
        if not hook["name"] or not hook["source_excerpt"]:
            continue
        lines.append(f"### {hook['label']}: `{hook['name']}`")
        lines.append("")
        if hook["doc_summary"]:
            lines.append(f"- Summary: {hook['doc_summary']}")
        if hook["source_line"] is not None:
            lines.append(f"- Source line: `{hook['source_line']}`")
        if hook["source_anchor"]:
            lines.append(f"- Source anchor: `{hook['source_anchor']}`")
        if hook["source_url"]:
            lines.append(f"- GitHub source: <{hook['source_url']}>")
        if hook["source_commit_url"]:
            lines.append(f"- GitHub source (commit pinned): <{hook['source_commit_url']}>")
        lines.extend(["", "```python", str(hook["source_excerpt"]), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_plugin_doc_html(
    plugin: PluginInspection,
    *,
    catalog_link: str | None = None,
    markdown_page_link: str | None = None,
) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    dataset_families = ", ".join(plugin.available_dataset_families) if plugin.available_dataset_families else "-"
    badge_html = "".join(f"<span class=\"badge\">{esc(badge)}</span>" for badge in plugin_catalog_badges(plugin))
    summary_items = [
        f"<li><strong>Plugin path</strong><br><code>{esc(plugin_display_path(plugin.plugin))}</code></li>",
        f"<li><strong>Summary</strong><br>{esc(plugin.module_doc_summary or '-')}</li>",
        f"<li><strong>Dataset families</strong><br><code>{esc(dataset_families)}</code></li>",
        f"<li><strong>Catalog badges</strong><br>{badge_html}</li>",
    ]
    if plugin.plugin_repo_commit:
        summary_items.append(f"<li><strong>Repository commit</strong><br><code>{esc(plugin.plugin_repo_commit)}</code></li>")
    if catalog_link:
        summary_items.append(f"<li><strong>Catalog index</strong><br><a href=\"{esc(catalog_link)}\">plugin catalog</a></li>")
    if markdown_page_link:
        summary_items.append(f"<li><strong>Alternate format</strong><br><a href=\"{esc(markdown_page_link)}\">Markdown</a></li>")

    hook_rows = []
    hook_sections = []
    for hook in plugin_hook_rows(plugin):
        if not hook["name"]:
            continue
        details: list[str] = []
        if hook["doc_summary"]:
            details.append(esc(hook["doc_summary"]))
        if hook["source_line"] is not None:
            details.append(f"line {esc(hook['source_line'])}")
        if hook["source_anchor"]:
            details.append(f"anchor <code>{esc(hook['source_anchor'])}</code>")
        source_bits: list[str] = []
        if hook["source_url"]:
            source_bits.append(f'<a href="{esc(hook["source_url"])}">github</a>')
        if hook["source_commit_url"]:
            source_bits.append(f'<a href="{esc(hook["source_commit_url"])}">commit</a>')
        hook_rows.append(
            "<tr>"
            f"<td>{esc(hook['label'])}</td>"
            f"<td><code>{esc(hook['name'])}</code></td>"
            f"<td><code>{esc(hook['signature'] or '-')}</code></td>"
            f"<td>{'<br>'.join(details) or '-'}</td>"
            f"<td>{'<br>'.join(source_bits) or '-'}</td>"
            "</tr>"
        )
        if not hook["source_excerpt"]:
            continue
        hook_meta = []
        if hook["doc_summary"]:
            hook_meta.append(f"<p><strong>Summary:</strong> {esc(hook['doc_summary'])}</p>")
        if hook["source_line"] is not None:
            hook_meta.append(f"<p><strong>Source line:</strong> <code>{esc(hook['source_line'])}</code></p>")
        if hook["source_anchor"]:
            hook_meta.append(f"<p><strong>Source anchor:</strong> <code>{esc(hook['source_anchor'])}</code></p>")
        if hook["source_url"]:
            hook_meta.append(f"<p><strong>GitHub source:</strong> <a href=\"{esc(hook['source_url'])}\">{esc(hook['source_url'])}</a></p>")
        if hook["source_commit_url"]:
            hook_meta.append(f"<p><strong>GitHub source (commit pinned):</strong> <a href=\"{esc(hook['source_commit_url'])}\">{esc(hook['source_commit_url'])}</a></p>")
        hook_sections.append(
            f"<article><h2>{esc(hook['label'])}: <code>{esc(hook['name'])}</code></h2>{''.join(hook_meta)}<pre><code>{esc(hook['source_excerpt'])}</code></pre></article>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Mini MapReduce plugin doc — {esc(plugin.name)}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1080px; padding: 0 1rem 3rem; line-height: 1.5; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid rgba(148, 163, 184, 0.35); padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }}
    thead th {{ background: rgba(148, 163, 184, 0.14); }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; padding: 0; }}
    .meta li {{ list-style: none; padding: 0.8rem 0.95rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.8rem; }}
    .badge {{ display: inline-block; margin: 0.15rem 0.3rem 0.15rem 0; padding: 0.15rem 0.45rem; border-radius: 999px; border: 1px solid rgba(148, 163, 184, 0.35); background: rgba(59, 130, 246, 0.10); }}
    article {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Mini MapReduce plugin doc: <code>{esc(plugin.name)}</code></h1>
  <ul class=\"meta\">{''.join(summary_items)}</ul>
  <section>
    <h2>Hook summary</h2>
    <table>
      <thead><tr><th>Hook</th><th>Export</th><th>Signature</th><th>Details</th><th>Source</th></tr></thead>
      <tbody>{''.join(hook_rows)}</tbody>
    </table>
  </section>
  <section>
    <h2>Hook source excerpts</h2>
    {''.join(hook_sections)}
  </section>
</body>
</html>
"""


def write_plugin_doc_pages(
    plugins: list[PluginInspection],
    *,
    docs_dir: Path,
    catalog_markdown_path: Path | None = None,
    catalog_html_path: Path | None = None,
) -> list[Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for plugin in plugins:
        markdown_path = docs_dir / plugin_doc_basename(plugin, ".md")
        html_path = docs_dir / plugin_doc_basename(plugin, ".html")
        markdown_catalog_link = (
            Path(os.path.relpath(catalog_markdown_path, start=markdown_path.parent)).as_posix()
            if catalog_markdown_path
            else None
        )
        html_catalog_link = (
            Path(os.path.relpath(catalog_html_path, start=html_path.parent)).as_posix()
            if catalog_html_path
            else None
        )
        markdown_path.write_text(
            render_plugin_doc_markdown(
                plugin,
                catalog_link=markdown_catalog_link,
                html_page_link=html_path.name,
            ),
            encoding="utf-8",
        )
        html_path.write_text(
            render_plugin_doc_html(
                plugin,
                catalog_link=html_catalog_link,
                markdown_page_link=markdown_path.name,
            ),
            encoding="utf-8",
        )
        written.extend([markdown_path, html_path])
    return written


def discover_plugin_refs(search_root: Path | None = None, *, pattern: str = "plugins_*.py") -> list[str]:
    root = (search_root or Path(__file__).resolve().parent).resolve()
    if not root.exists():
        raise ValueError(f"plugin search root does not exist: {root}")
    matches = sorted(path for path in root.rglob("*.py") if fnmatch.fnmatch(path.name, pattern))
    if not matches:
        raise ValueError(f"no plugins matched pattern {pattern!r} under {root}")
    return [str(path) for path in matches]


def render_plugin_inspections_csv(plugins: list[PluginInspection]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=PLUGIN_INSPECTION_FIELDNAMES)
    writer.writeheader()
    writer.writerows(plugin.csv_row() for plugin in plugins)
    return buffer.getvalue()


def is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
    return False


def normalize_json_value(value: Any, *, context: str) -> JSONValue:
    if not is_json_value(value):
        raise ValueError(f"{context} must return JSON-serializable values")
    return value


def order_output(output: dict[str, JSONValue]) -> dict[str, JSONValue]:
    if all(isinstance(value, Number) and not isinstance(value, bool) for value in output.values()):
        return dict(sorted(output.items(), key=lambda item: (-float(item[1]), item[0])))
    return dict(sorted(output.items()))


def summarize_benchmark_note_annotation(annotation: BenchmarkNoteAnnotation) -> str:
    return f"{annotation['title']}: {annotation['detail']}"


def render_benchmark_note_annotation_markdown(annotation: BenchmarkNoteAnnotation) -> list[str]:
    lines = [f"### {annotation['title']}", f"- Detail: {annotation['detail']}"]
    severity = annotation.get("severity")
    if severity:
        lines.append(f"- Severity: `{severity}`")
    hotspot_keys = annotation.get("hotspot_keys")
    if isinstance(hotspot_keys, list) and hotspot_keys:
        lines.append(f"- Hotspot keys: `{', '.join(str(item) for item in hotspot_keys)}`")
    takeaway = annotation.get("takeaway")
    if takeaway:
        lines.append(f"- Takeaway: {takeaway}")
    return lines


def render_benchmark_note_annotation_html(annotation: BenchmarkNoteAnnotation) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    def severity_class(value: object) -> str:
        slug = "".join(char.lower() if str(char).isalnum() else "-" for char in str(value)).strip("-")
        return slug or "custom"

    severity = annotation.get("severity")
    hotspot_keys = annotation.get("hotspot_keys")
    takeaway = annotation.get("takeaway")
    severity_html = (
        f"<p><span class='annotation-pill annotation-pill-{severity_class(severity)}'>{esc(severity)}</span></p>"
        if severity
        else ""
    )
    hotspot_html = ""
    if isinstance(hotspot_keys, list) and hotspot_keys:
        hotspot_html = (
            "<p><strong>Hotspot keys</strong><br>"
            + " ".join(f"<code>{esc(item)}</code>" for item in hotspot_keys)
            + "</p>"
        )
    takeaway_html = f"<p><strong>Takeaway</strong><br>{esc(takeaway)}</p>" if takeaway else ""
    return (
        "<article class='annotation-card'>"
        f"<h3>{esc(annotation['title'])}</h3>"
        f"{severity_html}"
        f"<p><strong>Detail</strong><br>{esc(annotation['detail'])}</p>"
        f"{hotspot_html}"
        f"{takeaway_html}"
        "</article>"
    )


def render_annotation_view_markdown(annotation_view: dict[str, JSONValue]) -> list[str]:
    lines = ["### Annotation view", ""]
    lines.append(f"- Total structured annotations: `{annotation_view['total_annotations']}`")
    lines.append(f"- Matched annotations after filtering: `{annotation_view['matched_annotations']}`")
    lines.append(f"- Rendered annotation cards: `{annotation_view['rendered_annotations']}`")
    severity_filter = annotation_view.get("severity_filter")
    if isinstance(severity_filter, list) and severity_filter:
        lines.append(f"- Severity filter: `{', '.join(str(item) for item in severity_filter)}`")
    limit = annotation_view.get("limit")
    if limit is not None:
        lines.append(f"- Annotation limit: `{limit}`")
    overflow = annotation_view.get("overflow")
    if overflow:
        lines.append(f"- Overflow mode: `{overflow}`")
    hidden_by_severity = annotation_view.get("hidden_by_severity")
    if isinstance(hidden_by_severity, int) and hidden_by_severity:
        lines.append(f"- Hidden by severity filter: `{hidden_by_severity}`")
    hidden_by_limit = annotation_view.get("hidden_by_limit")
    if isinstance(hidden_by_limit, int) and hidden_by_limit:
        lines.append(f"- Hidden by annotation limit: `{hidden_by_limit}`")
    if annotation_view.get("overflow_summary_emitted"):
        lines.append("- Overflow summary card emitted: `true`")
    return lines


def render_annotation_view_html(annotation_view: dict[str, JSONValue]) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    items = [
        f"<li><strong>Total structured annotations</strong><br><code>{esc(annotation_view['total_annotations'])}</code></li>",
        f"<li><strong>Matched after filtering</strong><br><code>{esc(annotation_view['matched_annotations'])}</code></li>",
        f"<li><strong>Rendered annotation cards</strong><br><code>{esc(annotation_view['rendered_annotations'])}</code></li>",
    ]
    severity_filter = annotation_view.get("severity_filter")
    if isinstance(severity_filter, list) and severity_filter:
        items.append(
            f"<li><strong>Severity filter</strong><br><code>{esc(', '.join(str(item) for item in severity_filter))}</code></li>"
        )
    limit = annotation_view.get("limit")
    if limit is not None:
        items.append(f"<li><strong>Annotation limit</strong><br><code>{esc(limit)}</code></li>")
    overflow = annotation_view.get("overflow")
    if overflow:
        items.append(f"<li><strong>Overflow mode</strong><br><code>{esc(overflow)}</code></li>")
    hidden_by_severity = annotation_view.get("hidden_by_severity")
    if isinstance(hidden_by_severity, int) and hidden_by_severity:
        items.append(f"<li><strong>Hidden by severity filter</strong><br><code>{esc(hidden_by_severity)}</code></li>")
    hidden_by_limit = annotation_view.get("hidden_by_limit")
    if isinstance(hidden_by_limit, int) and hidden_by_limit:
        items.append(f"<li><strong>Hidden by annotation limit</strong><br><code>{esc(hidden_by_limit)}</code></li>")
    if annotation_view.get("overflow_summary_emitted"):
        items.append("<li><strong>Overflow summary card emitted</strong><br><code>true</code></li>")
    return f"<div class='annotation-view'><h3>Annotation view</h3><ul class='meta'>{''.join(items)}</ul></div>"


@dataclass(frozen=True, slots=True)
class BenchmarkAnnotationPreset:
    name: str
    description: str
    annotation_severities: list[str] | None = None
    annotation_limit: int | None = None
    annotation_overflow: str = "drop"

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "description": self.description,
            "annotation_severities": list(self.annotation_severities) if self.annotation_severities else None,
            "annotation_limit": self.annotation_limit,
            "annotation_overflow": self.annotation_overflow if self.annotation_limit is not None else None,
        }


ANNOTATION_BATCH_PRESETS: dict[str, BenchmarkAnnotationPreset] = {
    "full": BenchmarkAnnotationPreset(
        name="full",
        description="Full annotation view with every structured reviewer callout rendered.",
    ),
    "portfolio-tight": BenchmarkAnnotationPreset(
        name="portfolio-tight",
        description="Filtered annotation view for portfolio screenshots: keep risk/watch callouts, show one card, and collapse the rest into a summary.",
        annotation_severities=["risk", "watch"],
        annotation_limit=1,
        annotation_overflow="summary",
    ),
}
DEFAULT_ANNOTATION_BATCH_PRESET_NAMES = ("full", "portfolio-tight")


@dataclass(slots=True)
class JobResult:
    job: str
    inputs: list[str]
    shard_count: int
    map_records: int
    unique_keys: int
    output: dict[str, JSONValue]
    reducers: int
    reducer_stats: list[dict[str, int]]
    plugin: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "job": self.job,
                "plugin": self.plugin,
                "inputs": self.inputs,
                "shard_count": self.shard_count,
                "map_records": self.map_records,
                "unique_keys": self.unique_keys,
                "reducers": self.reducers,
                "reducer_stats": self.reducer_stats,
                "output": self.output,
            },
            indent=2,
            sort_keys=True,
        )


@dataclass(slots=True)
class BenchmarkResult:
    job: str
    scenario: str
    dataset_family: str
    seed: int
    total_records: int
    unique_keys: int
    shard_size: int
    reducers: list[int]
    timings_ms: list[dict[str, int | float]]
    heatmap_rows: list[dict[str, int | str]]
    plugin: str | None = None
    available_dataset_families: list[str] | None = None
    benchmark_notes: list[str] | None = None
    benchmark_note_annotations: list[BenchmarkNoteAnnotation] | None = None
    annotation_view: dict[str, JSONValue] | None = None
    plugin_mapper: str | None = None
    plugin_reducer: str | None = None
    plugin_combiner: str | None = None
    plugin_benchmark_generator: str | None = None
    plugin_benchmark_note_hook: str | None = None

    def to_json(self) -> str:
        payload = {
            "job": self.job,
            "plugin": self.plugin,
            "scenario": self.scenario,
            "dataset_family": self.dataset_family,
            "seed": self.seed,
            "total_records": self.total_records,
            "unique_keys": self.unique_keys,
            "shard_size": self.shard_size,
            "reducers": self.reducers,
            "timings_ms": self.timings_ms,
            "heatmap_rows": self.heatmap_rows,
            "available_dataset_families": self.available_dataset_families,
            "benchmark_notes": self.benchmark_notes,
            "benchmark_note_annotations": self.benchmark_note_annotations,
            "plugin_mapper": self.plugin_mapper,
            "plugin_reducer": self.plugin_reducer,
            "plugin_combiner": self.plugin_combiner,
            "plugin_benchmark_generator": self.plugin_benchmark_generator,
            "plugin_benchmark_note_hook": self.plugin_benchmark_note_hook,
        }
        if self.annotation_view is not None:
            payload["annotation_view"] = self.annotation_view
        return json.dumps(payload, indent=2, sort_keys=True)

    def to_csv(self) -> str:
        fieldnames = [
            "job",
            "plugin",
            "scenario",
            "dataset_family",
            "available_dataset_families",
            "plugin_mapper",
            "plugin_reducer",
            "plugin_combiner",
            "plugin_benchmark_generator",
            "plugin_benchmark_note_hook",
            "seed",
            "total_records",
            "shard_size",
            "reducers",
            "elapsed_ms",
            "shards",
            "map_records",
            "unique_keys",
            "max_reducer_records",
            "skew_ratio",
        ]
        rows: list[dict[str, object]] = []
        for timing in self.timings_ms:
            row = {
                "job": self.job,
                "plugin": self.plugin,
                "scenario": self.scenario,
                "dataset_family": self.dataset_family,
                "available_dataset_families": ",".join(self.available_dataset_families) if self.available_dataset_families else None,
                "plugin_mapper": self.plugin_mapper,
                "plugin_reducer": self.plugin_reducer,
                "plugin_combiner": self.plugin_combiner,
                "plugin_benchmark_generator": self.plugin_benchmark_generator,
                "plugin_benchmark_note_hook": self.plugin_benchmark_note_hook,
                "seed": self.seed,
                "total_records": self.total_records,
                "shard_size": self.shard_size,
                **timing,
            }
            rows.append(row)

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

    def heatmap_to_csv(self) -> str:
        fieldnames = [
            "job",
            "plugin",
            "scenario",
            "dataset_family",
            "seed",
            "reducers",
            "shard_index",
            "reducer",
            "records",
            "unique_keys",
        ]
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {name: row.get(name) for name in fieldnames}
            for row in self.heatmap_rows
        )
        return buffer.getvalue()

    def _timing_svg(self) -> str:
        width = 680
        height = 240
        margin_left = 56
        margin_right = 24
        margin_top = 24
        margin_bottom = 48
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        max_elapsed = max((float(row["elapsed_ms"]) for row in self.timings_ms), default=0.0)
        scale = chart_height / max_elapsed if max_elapsed else 0.0
        bar_count = max(len(self.timings_ms), 1)
        slot_width = chart_width / bar_count
        bar_width = max(24.0, slot_width * 0.55)
        bars: list[str] = []
        labels: list[str] = []
        y_ticks: list[str] = []
        for tick in range(5):
            tick_value = (max_elapsed / 4) * tick if max_elapsed else float(tick)
            y = margin_top + chart_height - (tick_value * scale if max_elapsed else 0.0)
            y_ticks.append(
                f"<line x1='{margin_left}' y1='{y:.2f}' x2='{width - margin_right}' y2='{y:.2f}' stroke='rgba(148, 163, 184, 0.28)' stroke-dasharray='4 4' />"
                f"<text x='{margin_left - 8}' y='{y + 4:.2f}' text-anchor='end' font-size='11' fill='#475569'>{tick_value:.2f}</text>"
            )
        for index, timing in enumerate(self.timings_ms):
            elapsed = float(timing["elapsed_ms"])
            bar_height = elapsed * scale if max_elapsed else 0.0
            x = margin_left + (slot_width * index) + ((slot_width - bar_width) / 2)
            y = margin_top + chart_height - bar_height
            label_x = x + (bar_width / 2)
            bars.append(
                f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_width:.2f}' height='{bar_height:.2f}' rx='10' fill='#2563eb' />"
                f"<text x='{label_x:.2f}' y='{y - 8:.2f}' text-anchor='middle' font-size='11' fill='#0f172a'>{elapsed:.3f} ms</text>"
            )
            labels.append(
                f"<text x='{label_x:.2f}' y='{height - 20:.2f}' text-anchor='middle' font-size='11' fill='#475569'>r{timing['reducers']}</text>"
            )
        return (
            f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Elapsed benchmark timing by reducer count'>"
            f"<title>Elapsed benchmark timing by reducer count</title>"
            f"<rect x='0' y='0' width='{width}' height='{height}' rx='16' fill='rgba(248, 250, 252, 0.92)' />"
            f"{''.join(y_ticks)}"
            f"<line x1='{margin_left}' y1='{margin_top + chart_height:.2f}' x2='{width - margin_right}' y2='{margin_top + chart_height:.2f}' stroke='#94a3b8' />"
            f"{''.join(bars)}"
            f"{''.join(labels)}"
            "</svg>"
        )

    def _reducer_load_svg(self, reducer_count: int, totals: dict[int, int]) -> str:
        width = 680
        height = 220
        margin_left = 56
        margin_right = 24
        margin_top = 24
        margin_bottom = 48
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        max_total = max(totals.values(), default=0)
        scale = chart_height / max_total if max_total else 0.0
        bar_count = max(reducer_count, 1)
        slot_width = chart_width / bar_count
        bar_width = max(24.0, slot_width * 0.55)
        bars: list[str] = []
        labels: list[str] = []
        y_ticks: list[str] = []
        for tick in range(5):
            tick_value = (max_total / 4) * tick if max_total else float(tick)
            y = margin_top + chart_height - (tick_value * scale if max_total else 0.0)
            y_ticks.append(
                f"<line x1='{margin_left}' y1='{y:.2f}' x2='{width - margin_right}' y2='{y:.2f}' stroke='rgba(148, 163, 184, 0.28)' stroke-dasharray='4 4' />"
                f"<text x='{margin_left - 8}' y='{y + 4:.2f}' text-anchor='end' font-size='11' fill='#475569'>{tick_value:.1f}</text>"
            )
        for reducer in range(reducer_count):
            total = totals.get(reducer, 0)
            bar_height = total * scale if max_total else 0.0
            x = margin_left + (slot_width * reducer) + ((slot_width - bar_width) / 2)
            y = margin_top + chart_height - bar_height
            label_x = x + (bar_width / 2)
            bars.append(
                f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_width:.2f}' height='{bar_height:.2f}' rx='10' fill='#0f766e' />"
                f"<text x='{label_x:.2f}' y='{y - 8:.2f}' text-anchor='middle' font-size='11' fill='#0f172a'>{total}</text>"
            )
            labels.append(
                f"<text x='{label_x:.2f}' y='{height - 20:.2f}' text-anchor='middle' font-size='11' fill='#475569'>r{reducer}</text>"
            )
        return (
            f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Reducer load totals for {reducer_count} reducers'>"
            f"<title>Reducer load totals for {reducer_count} reducers</title>"
            f"<rect x='0' y='0' width='{width}' height='{height}' rx='16' fill='rgba(248, 250, 252, 0.92)' />"
            f"{''.join(y_ticks)}"
            f"<line x1='{margin_left}' y1='{margin_top + chart_height:.2f}' x2='{width - margin_right}' y2='{margin_top + chart_height:.2f}' stroke='#94a3b8' />"
            f"{''.join(bars)}"
            f"{''.join(labels)}"
            "</svg>"
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Mini MapReduce benchmark report ({self.job}: {self.scenario})",
            "",
            f"- Job: `{self.job}`",
            f"- Plugin: `{self.plugin or 'builtin'}`",
            f"- Dataset family: `{self.dataset_family}`",
            f"- Seed: `{self.seed}`",
            f"- Total records: `{self.total_records}`",
            f"- Shard size: `{self.shard_size}`",
            f"- Reducer counts: `{', '.join(str(value) for value in self.reducers)}`",
        ]
        if self.available_dataset_families:
            lines.append(f"- Available dataset families: `{', '.join(self.available_dataset_families)}`")
        if self.benchmark_notes:
            lines.append("")
            lines.append("## Dataset notes")
            lines.append("")
            lines.extend(f"- {note}" for note in self.benchmark_notes)
        if self.benchmark_note_annotations or (self.annotation_view and int(self.annotation_view.get("total_annotations", 0)) > 0):
            lines.append("")
            lines.append("## Structured benchmark annotations")
            lines.append("")
            if self.annotation_view:
                lines.extend(render_annotation_view_markdown(self.annotation_view))
                lines.append("")
            if self.benchmark_note_annotations:
                for annotation in self.benchmark_note_annotations:
                    lines.extend(render_benchmark_note_annotation_markdown(annotation))
                    lines.append("")
            else:
                lines.append("- No structured annotations matched the current view.")
                lines.append("")
            if lines[-1] == "":
                lines.pop()
        lines.extend([
            "",
            "## Timing summary",
            "",
            "| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for timing in self.timings_ms:
            lines.append(
                "| {reducers} | {elapsed_ms} | {shards} | {map_records} | {unique_keys} | {max_reducer_records} | {skew_ratio} |".format(**timing)
            )

        lines.extend(["", "## Heatmap highlights", ""])
        for reducer_count in self.reducers:
            rows = [row for row in self.heatmap_rows if row["reducers"] == reducer_count]
            if not rows:
                continue
            max_records = max(int(row["records"]) for row in rows)
            shard_count = max(int(row["shard_index"]) for row in rows) + 1
            per_reducer_totals = {reducer: 0 for reducer in range(reducer_count)}
            for row in rows:
                per_reducer_totals[int(row["reducer"])] += int(row["records"])
            hottest = max(rows, key=lambda row: (int(row["records"]), -int(row["shard_index"]), -int(row["reducer"])))
            coldest = min(rows, key=lambda row: (int(row["records"]), int(row["shard_index"]), int(row["reducer"])))
            total_values = list(per_reducer_totals.values())
            average = sum(total_values) / len(total_values) if total_values else 0
            stddev = statistics.pstdev(total_values) if len(total_values) > 1 else 0.0

            lines.append(f"### Reducers = {reducer_count}")
            lines.append(
                f"- Hottest cell: shard `{hottest['shard_index']}` → reducer `{hottest['reducer']}` with `{hottest['records']}` records across `{hottest['unique_keys']}` keys"
            )
            lines.append(
                f"- Coldest cell: shard `{coldest['shard_index']}` → reducer `{coldest['reducer']}` with `{coldest['records']}` records across `{coldest['unique_keys']}` keys"
            )
            lines.append(f"- Reducer load stddev: `{stddev:.3f}` records (mean `{average:.3f}`)")
            lines.append(
                f"- Total records per reducer: {', '.join(f'r{reducer}={per_reducer_totals[reducer]}' for reducer in range(reducer_count))}"
            )
            lines.append("")
            lines.append("| Shard | " + " | ".join(f"r{reducer}" for reducer in range(reducer_count)) + " |")
            lines.append("| --- | " + " | ".join("---:" for _ in range(reducer_count)) + " |")
            rows_by_shard = {index: {reducer: 0 for reducer in range(reducer_count)} for index in range(shard_count)}
            for row in rows:
                rows_by_shard[int(row["shard_index"])][int(row["reducer"])] = int(row["records"])
            for shard_index in range(shard_count):
                rendered_cells = []
                for reducer in range(reducer_count):
                    value = rows_by_shard[shard_index][reducer]
                    if max_records:
                        bar = "█" * max(1, round((value / max_records) * 8)) if value else "·"
                    else:
                        bar = "·"
                    rendered_cells.append(f"{value} {bar}")
                lines.append(f"| {shard_index} | " + " | ".join(rendered_cells) + " |")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def to_html(self) -> str:
        def esc(value: object) -> str:
            return html.escape(str(value), quote=True)

        timing_rows = "".join(
            "<tr>"
            f"<td>{esc(timing['reducers'])}</td>"
            f"<td>{esc(timing['elapsed_ms'])}</td>"
            f"<td>{esc(timing['shards'])}</td>"
            f"<td>{esc(timing['map_records'])}</td>"
            f"<td>{esc(timing['unique_keys'])}</td>"
            f"<td>{esc(timing['max_reducer_records'])}</td>"
            f"<td>{esc(timing['skew_ratio'])}</td>"
            "</tr>"
            for timing in self.timings_ms
        )

        timing_chart = self._timing_svg()
        section_parts = []
        for reducer_count in self.reducers:
            rows = [row for row in self.heatmap_rows if row["reducers"] == reducer_count]
            if not rows:
                continue
            max_records = max(int(row["records"]) for row in rows)
            shard_count = max(int(row["shard_index"]) for row in rows) + 1
            per_reducer_totals = {reducer: 0 for reducer in range(reducer_count)}
            for row in rows:
                per_reducer_totals[int(row["reducer"])] += int(row["records"])
            hottest = max(rows, key=lambda row: (int(row["records"]), -int(row["shard_index"]), -int(row["reducer"])))
            coldest = min(rows, key=lambda row: (int(row["records"]), int(row["shard_index"]), int(row["reducer"])))
            total_values = list(per_reducer_totals.values())
            average = sum(total_values) / len(total_values) if total_values else 0
            stddev = statistics.pstdev(total_values) if len(total_values) > 1 else 0.0

            header_cells = "".join(f"<th>r{reducer}</th>" for reducer in range(reducer_count))
            rows_by_shard = {index: {reducer: 0 for reducer in range(reducer_count)} for index in range(shard_count)}
            for row in rows:
                rows_by_shard[int(row["shard_index"])][int(row["reducer"])] = int(row["records"])

            heatmap_rows = []
            for shard_index in range(shard_count):
                rendered_cells = []
                for reducer in range(reducer_count):
                    value = rows_by_shard[shard_index][reducer]
                    ratio = (value / max_records) if max_records else 0
                    alpha = 0.15 + (ratio * 0.75 if value else 0)
                    style = f"background: rgba(37, 99, 235, {alpha:.3f});" if value else "background: rgba(148, 163, 184, 0.12);"
                    rendered_cells.append(f"<td style='{style}'>{value}</td>")
                heatmap_rows.append(f"<tr><th>s{shard_index}</th>{''.join(rendered_cells)}</tr>")

            reducer_load_chart = self._reducer_load_svg(reducer_count, per_reducer_totals)
            section_parts.append(
                ""
                f"<section><h2>Reducers = {esc(reducer_count)}</h2>"
                f"<ul><li><strong>Hottest cell:</strong> shard <code>{esc(hottest['shard_index'])}</code> → reducer <code>{esc(hottest['reducer'])}</code> with <code>{esc(hottest['records'])}</code> records across <code>{esc(hottest['unique_keys'])}</code> keys</li>"
                f"<li><strong>Coldest cell:</strong> shard <code>{esc(coldest['shard_index'])}</code> → reducer <code>{esc(coldest['reducer'])}</code> with <code>{esc(coldest['records'])}</code> records across <code>{esc(coldest['unique_keys'])}</code> keys</li>"
                f"<li><strong>Reducer load stddev:</strong> <code>{stddev:.3f}</code> records (mean <code>{average:.3f}</code>)</li>"
                f"<li><strong>Total records per reducer:</strong> {esc(', '.join(f'r{reducer}={per_reducer_totals[reducer]}' for reducer in range(reducer_count)))}</li></ul>"
                f"<div class='chart-card'><h3>Reducer load chart</h3>{reducer_load_chart}</div>"
                f"<table><thead><tr><th>Shard</th>{header_cells}</tr></thead><tbody>{''.join(heatmap_rows)}</tbody></table></section>"
            )

        annotation_html = ""
        if self.benchmark_note_annotations or (self.annotation_view and int(self.annotation_view.get("total_annotations", 0)) > 0):
            annotation_view_html = render_annotation_view_html(self.annotation_view) if self.annotation_view else ""
            annotation_cards_html = (
                f"<div class='annotation-grid'>{''.join(render_benchmark_note_annotation_html(annotation) for annotation in self.benchmark_note_annotations)}</div>"
                if self.benchmark_note_annotations
                else "<p>No structured annotations matched the current view.</p>"
            )
            annotation_html = (
                "<h2>Structured benchmark annotations</h2>"
                f"{annotation_view_html}"
                f"{annotation_cards_html}"
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini MapReduce benchmark report ({esc(self.job)}: {esc(self.scenario)})</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1100px; padding: 0 1rem 3rem; line-height: 1.5; }}
    h1, h2 {{ line-height: 1.2; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid rgba(148, 163, 184, 0.35); padding: 0.5rem 0.65rem; text-align: right; }}
    th:first-child, td:first-child {{ text-align: left; }}
    thead th {{ background: rgba(148, 163, 184, 0.14); }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1rem 0 2rem; }}
    .meta li {{ list-style: none; padding: 0.75rem 0.9rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.75rem; }}
    .chart-card {{ margin: 1rem 0 1.5rem; padding: 1rem; border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1rem; background: rgba(255, 255, 255, 0.45); }}
    .chart-card h3 {{ margin-top: 0; margin-bottom: 0.75rem; }}
    .annotation-view {{ margin: 1rem 0 1.25rem; }}
    .annotation-view h3 {{ margin-bottom: 0.75rem; }}
    .annotation-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1rem 0 2rem; }}
    .annotation-card {{ padding: 1rem; border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 1rem; background: rgba(239, 246, 255, 0.52); }}
    .annotation-card h3 {{ margin-top: 0; margin-bottom: 0.75rem; }}
    .annotation-card p {{ margin: 0.55rem 0; }}
    .annotation-pill {{ display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}
    .annotation-pill-info {{ background: rgba(37, 99, 235, 0.14); color: #1d4ed8; }}
    .annotation-pill-watch {{ background: rgba(245, 158, 11, 0.18); color: #b45309; }}
    .annotation-pill-risk {{ background: rgba(220, 38, 38, 0.14); color: #b91c1c; }}
    .annotation-pill-custom {{ background: rgba(71, 85, 105, 0.14); color: #334155; }}
    svg {{ width: 100%; height: auto; display: block; }}
    ul.summary {{ padding-left: 1.2rem; }}
  </style>
</head>
<body>
  <h1>Mini MapReduce benchmark report ({esc(self.job)}: {esc(self.scenario)})</h1>
  <ul class="meta">
    <li><strong>Job</strong><br><code>{esc(self.job)}</code></li>
    <li><strong>Plugin</strong><br><code>{esc(self.plugin or 'builtin')}</code></li>
    <li><strong>Dataset family</strong><br><code>{esc(self.dataset_family)}</code></li>
    <li><strong>Seed</strong><br><code>{esc(self.seed)}</code></li>
    <li><strong>Total records</strong><br><code>{esc(self.total_records)}</code></li>
    <li><strong>Shard size</strong><br><code>{esc(self.shard_size)}</code></li>
    <li><strong>Reducer counts</strong><br><code>{esc(', '.join(str(value) for value in self.reducers))}</code></li>
    {f"<li><strong>Available dataset families</strong><br><code>{esc(', '.join(self.available_dataset_families))}</code></li>" if self.available_dataset_families else ""}
  </ul>
  {f"<h2>Dataset notes</h2><ul class='summary'>{''.join(f'<li>{esc(note)}</li>' for note in self.benchmark_notes)}</ul>" if self.benchmark_notes else ""}
  {annotation_html}
  <h2>Timing summary</h2>
  <div class="chart-card"><h3>Elapsed timing chart</h3>{timing_chart}</div>
  <table>
    <thead>
      <tr><th>Reducers</th><th>Elapsed (ms)</th><th>Shards</th><th>Map records</th><th>Unique keys</th><th>Max reducer records</th><th>Skew ratio</th></tr>
    </thead>
    <tbody>{timing_rows}</tbody>
  </table>
  {''.join(section_parts)}
</body>
</html>
"""

    def with_annotation_view(
        self,
        *,
        benchmark_notes: list[str],
        benchmark_note_annotations: list[BenchmarkNoteAnnotation],
        annotation_view: dict[str, JSONValue] | None,
    ) -> "BenchmarkResult":
        return BenchmarkResult(
            job=self.job,
            scenario=self.scenario,
            dataset_family=self.dataset_family,
            seed=self.seed,
            total_records=self.total_records,
            unique_keys=self.unique_keys,
            shard_size=self.shard_size,
            reducers=list(self.reducers),
            timings_ms=[dict(row) for row in self.timings_ms],
            heatmap_rows=[dict(row) for row in self.heatmap_rows],
            plugin=self.plugin,
            available_dataset_families=list(self.available_dataset_families) if self.available_dataset_families else None,
            benchmark_notes=list(benchmark_notes) or None,
            benchmark_note_annotations=[dict(item) for item in benchmark_note_annotations] or None,
            annotation_view=dict(annotation_view) if annotation_view is not None else None,
            plugin_mapper=self.plugin_mapper,
            plugin_reducer=self.plugin_reducer,
            plugin_combiner=self.plugin_combiner,
            plugin_benchmark_generator=self.plugin_benchmark_generator,
            plugin_benchmark_note_hook=self.plugin_benchmark_note_hook,
        )


@dataclass(slots=True)
class BenchmarkPresetArtifact:
    name: str
    description: str
    annotation_severities: list[str] | None
    annotation_limit: int | None
    annotation_overflow: str | None
    annotation_view: dict[str, JSONValue] | None
    json_path: str
    report_path: str
    html_path: str

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "description": self.description,
            "annotation_severities": list(self.annotation_severities) if self.annotation_severities else None,
            "annotation_limit": self.annotation_limit,
            "annotation_overflow": self.annotation_overflow,
            "annotation_view": dict(self.annotation_view) if self.annotation_view is not None else None,
            "artifacts": {
                "json": self.json_path,
                "report": self.report_path,
                "html": self.html_path,
            },
        }


@dataclass(slots=True)
class BenchmarkPresetBatch:
    output_dir: str
    prefix: str
    shared_csv_path: str
    shared_heatmap_path: str
    presets: list[BenchmarkPresetArtifact]

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "output_dir": self.output_dir,
            "prefix": self.prefix,
            "shared_artifacts": {
                "csv": self.shared_csv_path,
                "heatmap_csv": self.shared_heatmap_path,
            },
            "presets": [preset.as_dict() for preset in self.presets],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)


@dataclass(slots=True)
class PluginJob:
    name: str
    mapper: Mapper
    combiner: Reducer
    reducer: Reducer
    path: Path
    benchmark_generator: BenchmarkGenerator | None = None
    benchmark_note_hook: BenchmarkNoteHook | None = None
    dataset_families: list[str] | None = None


def normalize_dataset_families(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("plugin BENCHMARK_DATASET_FAMILIES must be a non-empty list/tuple of strings")
    families: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("plugin BENCHMARK_DATASET_FAMILIES must only contain non-empty strings")
        families.append(item)
    return families


BUILTIN_JOBS = ("wordcount", "json-group-count")


BUILTIN_JOB_BENCHMARK_NOTES: dict[tuple[str, str, str], list[BenchmarkNoteItem]] = {
    ("wordcount", "balanced", "default"): [
        "The default balanced corpus rotates evenly across 24 generic keys, so reducer hot spots should stay mild unless the partitioner itself clusters hashes.",
        "If one reducer still pulls ahead here, that usually reflects hash-bucket variance rather than an intentionally dominant vocabulary term.",
    ],
    ("wordcount", "balanced", "news"): [
        "The news family spreads traffic across desk and beat labels, which makes it a cleaner proxy for editorial-topic fan-out than the generic default keys.",
        "Balanced runs here should keep topic counts close, so timing changes are easier to attribute to reducer count than to vocabulary skew.",
    ],
    ("wordcount", "balanced", "logs"): [
        "The log-shaped balanced corpus cycles through service and level pairs, so every reducer should see a similar mix of info/warn/error/debug tokens.",
        "This family is useful when you want interview-ready examples that resemble observability pipelines without injecting a dominant error burst.",
    ],
    ("wordcount", "skewed", "default"): [
        "The skewed default corpus intentionally repeats `hot-key` far more often than the warm/cold tail, so the hottest reducer cells should usually reflect that synthetic hotspot.",
        "Use this family to show how a single dominant token can stretch one reducer even when the aggregate output is still correct.",
    ],
    ("wordcount", "skewed", "news"): [
        "`breaking-news` is the dominant topic in this family, with smaller desk/beat tails behind it, so one reducer often absorbs most of the urgency spike.",
        "That makes the report feel closer to a real newsroom burst where one story label suddenly dwarfs the rest of the taxonomy.",
    ],
    ("wordcount", "skewed", "logs"): [
        "`checkout:error` is deliberately overrepresented here, with warn/info tokens filling the long tail, so the hottest cells simulate incident-driven log skew.",
        "This is the most portfolio-friendly built-in family for discussing hot services, noisy alerts, and why aggregate counts alone hide reducer pain.",
    ],
    ("json-group-count", "balanced", "default"): [
        "The default JSON family cycles evenly across `ok`, `error`, `retry`, and `queued`, so status counts should stay close across shards.",
        "When a reducer dominates in this balanced case, it usually points to partition spread rather than a single status overwhelming the stream.",
    ],
    ("json-group-count", "balanced", "incidents"): [
        "Incident statuses rotate through `detected`, `triaged`, `mitigated`, and `resolved`, giving you a realistic but intentionally even operations workflow.",
        "This family is useful for showing that the same pipeline can model incident state machines without built-in skew.",
    ],
    ("json-group-count", "balanced", "deployments"): [
        "Deployment states cycle evenly across `queued`, `running`, `passed`, and `rolled_back`, which makes it a stable release-pipeline baseline.",
        "Balanced deployment runs help separate partitioning effects from the more dramatic release-train hotspots in the skewed family.",
    ],
    ("json-group-count", "skewed", "default"): [
        "`ok` dominates the default skewed event stream, with `retry` and `error` forming the secondary tail, so one reducer often carries most of the healthy-traffic volume.",
        "That pattern is handy for explaining why even mostly-good telemetry can still create reducer imbalance when one label wins by a large margin.",
    ],
    ("json-group-count", "skewed", "incidents"): [
        "`triaged` is intentionally the hottest status in this incident family, which mirrors backlogs where many alerts stall in the same operational state.",
        "If the hottest reducer aligns with a heavy triage bucket, the chart gives you a concrete story about response bottlenecks instead of abstract skew math.",
    ],
    ("json-group-count", "skewed", "deployments"): [
        "`running` and `queued` dominate this deployment family, so the hottest reducers resemble a congested release train with many in-flight changes and a smaller rollback tail.",
        "This family is useful for talking about CI/CD hotspots where transient active states outnumber terminal states by a wide margin.",
    ],
}


def normalize_benchmark_note_annotation(
    item: BenchmarkNoteAnnotation,
    *,
    source: str,
    index: int,
) -> BenchmarkNoteAnnotation:
    if not is_json_value(item):
        raise ValueError(f"{source} item {index} must be a JSON-serializable annotation object")
    title = item.get("title")
    detail = item.get("detail", item.get("summary"))
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{source} item {index} must include a non-empty string title")
    if not isinstance(detail, str) or not detail.strip():
        raise ValueError(f"{source} item {index} must include a non-empty string detail")

    normalized: BenchmarkNoteAnnotation = {
        "title": title.strip(),
        "detail": detail.strip(),
    }

    severity = item.get("severity")
    if severity is not None:
        if not isinstance(severity, str) or not severity.strip():
            raise ValueError(f"{source} item {index} severity must be a non-empty string when provided")
        normalized["severity"] = severity.strip().lower()

    hotspot_keys = item.get("hotspot_keys")
    if hotspot_keys is not None:
        if not isinstance(hotspot_keys, (list, tuple)) or not hotspot_keys or not all(isinstance(key, str) and key.strip() for key in hotspot_keys):
            raise ValueError(f"{source} item {index} hotspot_keys must be a non-empty list/tuple of strings when provided")
        normalized["hotspot_keys"] = [key.strip() for key in hotspot_keys]

    takeaway = item.get("takeaway")
    if takeaway is not None:
        if not isinstance(takeaway, str) or not takeaway.strip():
            raise ValueError(f"{source} item {index} takeaway must be a non-empty string when provided")
        normalized["takeaway"] = takeaway.strip()

    for key, value in item.items():
        if key in {"title", "detail", "summary", "severity", "hotspot_keys", "takeaway"}:
            continue
        normalized[key] = normalize_json_value(value, context=f"{source} item {index} field {key!r}")
    return normalized


def normalize_benchmark_note_items(
    note_values: list[BenchmarkNoteItem] | tuple[BenchmarkNoteItem, ...],
    *,
    source: str,
) -> tuple[list[str], list[BenchmarkNoteAnnotation]]:
    notes: list[str] = []
    annotations: list[BenchmarkNoteAnnotation] = []
    for index, item in enumerate(note_values):
        if isinstance(item, str) and item.strip():
            notes.append(item.strip())
            continue
        if isinstance(item, dict):
            annotation = normalize_benchmark_note_annotation(item, source=source, index=index)
            annotations.append(annotation)
            notes.append(summarize_benchmark_note_annotation(annotation))
            continue
        raise ValueError(f"{source} must contain only non-empty strings or annotation objects")
    return notes, annotations


def normalize_annotation_severities(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("annotation severity filters must be non-empty strings")
        severity = item.strip().lower()
        if severity in seen:
            continue
        seen.add(severity)
        normalized.append(severity)
    return normalized


def build_annotation_overflow_summary(
    hidden_annotations: list[BenchmarkNoteAnnotation],
    *,
    limit: int,
) -> BenchmarkNoteAnnotation:
    hidden_titles = [str(annotation["title"]) for annotation in hidden_annotations[:5]]
    hidden_severities = sorted(
        {
            str(annotation["severity"])
            for annotation in hidden_annotations
            if isinstance(annotation.get("severity"), str) and str(annotation["severity"]).strip()
        }
    )
    detail = (
        f"Collapsed {len(hidden_annotations)} additional structured reviewer callout(s) after the first {limit} visible annotation(s)."
    )
    if hidden_titles:
        suffix = " …" if len(hidden_annotations) > len(hidden_titles) else ""
        detail += f" Hidden titles: {', '.join(hidden_titles)}{suffix}."
    return {
        "title": "Collapsed reviewer callouts",
        "detail": detail,
        "severity": "info",
        "collapsed_count": len(hidden_annotations),
        "collapsed_titles": hidden_titles,
        "collapsed_severities": hidden_severities,
        "takeaway": "Raise --annotation-limit or narrow --annotation-severity when you want the full set of reviewer callouts.",
    }


def apply_benchmark_annotation_view(
    note_values: list[BenchmarkNoteItem] | tuple[BenchmarkNoteItem, ...],
    *,
    source: str,
    annotation_severities: list[str] | None = None,
    annotation_limit: int | None = None,
    annotation_overflow: str = "drop",
) -> tuple[list[str], list[BenchmarkNoteAnnotation], dict[str, JSONValue] | None]:
    if annotation_limit is not None and annotation_limit <= 0:
        raise ValueError("annotation_limit must be positive when provided")
    if annotation_overflow not in {"drop", "summary"}:
        raise ValueError("annotation_overflow must be one of: drop, summary")

    normalized_severities = normalize_annotation_severities(annotation_severities)
    selected_items: list[BenchmarkNoteItem] = []
    hidden_annotations: list[BenchmarkNoteAnnotation] = []
    total_annotations = 0
    matched_annotations = 0
    hidden_by_severity = 0
    hidden_by_limit = 0

    for index, item in enumerate(note_values):
        if isinstance(item, str):
            if not item.strip():
                raise ValueError(f"{source} must contain only non-empty strings or annotation objects")
            selected_items.append(item.strip())
            continue
        if not isinstance(item, dict):
            raise ValueError(f"{source} must contain only non-empty strings or annotation objects")

        annotation = normalize_benchmark_note_annotation(item, source=source, index=index)
        total_annotations += 1
        severity = annotation.get("severity")
        if normalized_severities and severity not in normalized_severities:
            hidden_by_severity += 1
            continue

        matched_annotations += 1
        if annotation_limit is not None and matched_annotations > annotation_limit:
            hidden_by_limit += 1
            hidden_annotations.append(annotation)
            continue
        selected_items.append(annotation)

    overflow_summary_emitted = False
    if hidden_annotations and annotation_limit is not None and annotation_overflow == "summary":
        selected_items.append(build_annotation_overflow_summary(hidden_annotations, limit=annotation_limit))
        overflow_summary_emitted = True

    notes, annotations = normalize_benchmark_note_items(selected_items, source=source)
    annotation_view: dict[str, JSONValue] | None = None
    if normalized_severities is not None or annotation_limit is not None:
        annotation_view = {
            "severity_filter": normalized_severities,
            "limit": annotation_limit,
            "overflow": annotation_overflow if annotation_limit is not None else None,
            "total_annotations": total_annotations,
            "matched_annotations": matched_annotations,
            "rendered_annotations": len(annotations),
            "hidden_by_severity": hidden_by_severity,
            "hidden_by_limit": hidden_by_limit,
            "overflow_summary_emitted": overflow_summary_emitted,
        }
    return notes, annotations, annotation_view


def call_benchmark_note_hook(
    hook: BenchmarkNoteHook,
    *,
    scenario: str,
    dataset_family: str,
    records: int,
    seed: int,
) -> list[BenchmarkNoteItem]:
    signature = inspect.signature(hook)
    positional_params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    has_varargs = any(parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in signature.parameters.values())
    if not positional_params and not has_varargs:
        raise ValueError("plugin benchmark_notes must accept at least a scenario parameter")
    if not has_varargs and len(positional_params) > 4:
        raise ValueError("plugin benchmark_notes supports at most 4 positional parameters")
    required_keyword_only = [
        parameter.name
        for parameter in signature.parameters.values()
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY and parameter.default is inspect._empty
    ]
    if required_keyword_only:
        raise ValueError("plugin benchmark_notes cannot require keyword-only parameters")
    args = [scenario, dataset_family, records, seed]
    note_values = hook(*args if has_varargs else args[: len(positional_params)])
    if note_values is None:
        return []
    if not isinstance(note_values, (list, tuple)):
        raise ValueError("plugin benchmark_notes must return a list/tuple of non-empty strings or annotation objects")
    normalize_benchmark_note_items(note_values, source="plugin benchmark_notes")
    return list(note_values)


def benchmark_note_items_for(
    job: str,
    scenario: str,
    dataset_family: str,
    *,
    records: int,
    seed: int,
    plugin: PluginJob | None = None,
) -> list[BenchmarkNoteItem]:
    note_items = list(BUILTIN_JOB_BENCHMARK_NOTES.get((job, scenario, dataset_family), []))
    if job == "plugin" and plugin is not None and plugin.benchmark_note_hook is not None:
        note_items.extend(
            call_benchmark_note_hook(
                plugin.benchmark_note_hook,
                scenario=scenario,
                dataset_family=dataset_family,
                records=records,
                seed=seed,
            )
        )
    return note_items


def benchmark_notes_for(
    job: str,
    scenario: str,
    dataset_family: str,
    *,
    records: int,
    seed: int,
    plugin: PluginJob | None = None,
    annotation_severities: list[str] | None = None,
    annotation_limit: int | None = None,
    annotation_overflow: str = "drop",
) -> tuple[list[str], list[BenchmarkNoteAnnotation], dict[str, JSONValue] | None]:
    return apply_benchmark_annotation_view(
        benchmark_note_items_for(
            job,
            scenario,
            dataset_family,
            records=records,
            seed=seed,
            plugin=plugin,
        ),
        source="benchmark notes",
        annotation_severities=annotation_severities,
        annotation_limit=annotation_limit,
        annotation_overflow=annotation_overflow,
    )


def resolve_annotation_batch_presets(names: list[str] | None = None) -> list[BenchmarkAnnotationPreset]:
    selected_names = names or list(DEFAULT_ANNOTATION_BATCH_PRESET_NAMES)
    resolved: list[BenchmarkAnnotationPreset] = []
    seen: set[str] = set()
    for name in selected_names:
        if name in seen:
            continue
        if name not in ANNOTATION_BATCH_PRESETS:
            raise ValueError(
                f"unsupported annotation batch preset: {name} (supported: {', '.join(sorted(ANNOTATION_BATCH_PRESETS))})"
            )
        seen.add(name)
        resolved.append(ANNOTATION_BATCH_PRESETS[name])
    return resolved


def slugify_filename(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "benchmark"


def default_annotation_batch_prefix(result: BenchmarkResult) -> str:
    return slugify_filename(f"{result.job}-{result.scenario}-{result.dataset_family}-annotation-batch")


def build_benchmark_preset_batch(
    base_result: BenchmarkResult,
    *,
    note_items: list[BenchmarkNoteItem],
    output_dir: Path,
    prefix: str | None = None,
    preset_names: list[str] | None = None,
) -> BenchmarkPresetBatch:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_presets = resolve_annotation_batch_presets(preset_names)
    prefix_slug = slugify_filename(prefix or default_annotation_batch_prefix(base_result))
    shared_csv_path = output_dir / f"{prefix_slug}-shared.csv"
    shared_heatmap_path = output_dir / f"{prefix_slug}-shared-heatmap.csv"
    shared_csv_path.write_text(base_result.to_csv(), encoding="utf-8")
    shared_heatmap_path.write_text(base_result.heatmap_to_csv(), encoding="utf-8")

    preset_artifacts: list[BenchmarkPresetArtifact] = []
    for preset in resolved_presets:
        notes, annotations, annotation_view = apply_benchmark_annotation_view(
            note_items,
            source="benchmark notes",
            annotation_severities=preset.annotation_severities,
            annotation_limit=preset.annotation_limit,
            annotation_overflow=preset.annotation_overflow,
        )
        preset_result = base_result.with_annotation_view(
            benchmark_notes=notes,
            benchmark_note_annotations=annotations,
            annotation_view=annotation_view,
        )
        json_path = output_dir / f"{prefix_slug}-{preset.name}.json"
        report_path = output_dir / f"{prefix_slug}-{preset.name}.md"
        html_path = output_dir / f"{prefix_slug}-{preset.name}.html"
        json_path.write_text(preset_result.to_json() + "\n", encoding="utf-8")
        report_path.write_text(preset_result.to_markdown(), encoding="utf-8")
        html_path.write_text(preset_result.to_html(), encoding="utf-8")
        preset_artifacts.append(
            BenchmarkPresetArtifact(
                name=preset.name,
                description=preset.description,
                annotation_severities=list(preset.annotation_severities) if preset.annotation_severities else None,
                annotation_limit=preset.annotation_limit,
                annotation_overflow=preset.annotation_overflow if preset.annotation_limit is not None else None,
                annotation_view=dict(annotation_view) if annotation_view is not None else None,
                json_path=json_path.name,
                report_path=report_path.name,
                html_path=html_path.name,
            )
        )

    return BenchmarkPresetBatch(
        output_dir=".",
        prefix=prefix_slug,
        shared_csv_path=shared_csv_path.name,
        shared_heatmap_path=shared_heatmap_path.name,
        presets=preset_artifacts,
    )

@dataclass(slots=True)
class DocsArtifactLinks:
    markdown_path: str | None = None
    html_path: str | None = None
    json_path: str | None = None
    csv_path: str | None = None
    heatmap_csv_path: str | None = None

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "markdown": self.markdown_path,
            "html": self.html_path,
            "json": self.json_path,
            "csv": self.csv_path,
            "heatmap_csv": self.heatmap_csv_path,
        }

    def labeled_paths(self) -> list[tuple[str, str]]:
        labeled: list[tuple[str, str]] = []
        for label, value in [
            ("Markdown", self.markdown_path),
            ("HTML", self.html_path),
            ("JSON", self.json_path),
            ("CSV", self.csv_path),
            ("Heatmap CSV", self.heatmap_csv_path),
        ]:
            if value:
                labeled.append((label, value))
        return labeled


@dataclass(slots=True)
class DocsArtifactEntry:
    slug: str
    title: str
    description: str
    links: DocsArtifactLinks

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "links": self.links.as_dict(),
        }


@dataclass(slots=True)
class DocsAnnotationBatchPreset:
    name: str
    description: str
    annotation_severities: list[str] | None
    annotation_limit: int | None
    annotation_overflow: str | None
    links: DocsArtifactLinks

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "name": self.name,
            "description": self.description,
            "annotation_severities": list(self.annotation_severities) if self.annotation_severities else None,
            "annotation_limit": self.annotation_limit,
            "annotation_overflow": self.annotation_overflow,
            "links": self.links.as_dict(),
        }


@dataclass(slots=True)
class DocsAnnotationBatch:
    slug: str
    title: str
    manifest_path: str
    shared_csv_path: str | None
    shared_heatmap_path: str | None
    presets: list[DocsAnnotationBatchPreset]

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "slug": self.slug,
            "title": self.title,
            "manifest": self.manifest_path,
            "shared_artifacts": {
                "csv": self.shared_csv_path,
                "heatmap_csv": self.shared_heatmap_path,
            },
            "presets": [preset.as_dict() for preset in self.presets],
        }


@dataclass(slots=True)
class MiniMapReduceDocsIndex:
    artifacts_root: str
    plugin_catalog: DocsArtifactLinks | None
    plugin_pages: list[DocsArtifactEntry]
    inspection_diffs: list[DocsArtifactEntry]
    release_comparisons: list[DocsArtifactEntry]
    benchmark_reports: list[DocsArtifactEntry]
    annotation_batches: list[DocsAnnotationBatch]

    def as_dict(self) -> dict[str, JSONValue]:
        return {
            "artifacts_root": self.artifacts_root,
            "plugin_catalog": self.plugin_catalog.as_dict() if self.plugin_catalog else None,
            "plugin_pages": [entry.as_dict() for entry in self.plugin_pages],
            "inspection_diffs": [entry.as_dict() for entry in self.inspection_diffs],
            "release_comparisons": [entry.as_dict() for entry in self.release_comparisons],
            "benchmark_reports": [entry.as_dict() for entry in self.benchmark_reports],
            "annotation_batches": [batch.as_dict() for batch in self.annotation_batches],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# Mini MapReduce docs index",
            "",
            "A lightweight landing page for the committed Mini MapReduce artifacts so reviewers can jump from the top-level project README into plugin catalogs, dedicated plugin docs, inspection diffs, benchmark reports, and annotation-batch presets without hunting through the repo tree.",
            "",
            "## Browser-first links",
            "",
        ]
        browser_links: list[tuple[str, str]] = []
        if self.plugin_catalog and self.plugin_catalog.html_path:
            browser_links.append(("Plugin catalog HTML", self.plugin_catalog.html_path))
        browser_links.extend((f"Inspection diff HTML — {entry.title}", entry.links.html_path) for entry in self.inspection_diffs if entry.links.html_path)
        browser_links.extend((f"Release comparison HTML — {entry.title}", entry.links.html_path) for entry in self.release_comparisons if entry.links.html_path)
        browser_links.extend((f"Benchmark report HTML — {entry.title}", entry.links.html_path) for entry in self.benchmark_reports if entry.links.html_path)
        browser_links.extend(
            (
                f"Annotation batch HTML — {batch.title} / {preset.name}",
                preset.links.html_path,
            )
            for batch in self.annotation_batches
            for preset in batch.presets
            if preset.links.html_path
        )
        if browser_links:
            for label, target in browser_links:
                lines.append(f"- [{label}]({target})")
        else:
            lines.append("- No HTML artifacts discovered yet.")

        lines.extend(["", "## Plugin catalog", ""])
        if self.plugin_catalog and self.plugin_catalog.labeled_paths():
            lines.append("- " + " · ".join(f"[{label}]({path})" for label, path in self.plugin_catalog.labeled_paths()))
        else:
            lines.append("- Plugin catalog artifacts have not been generated yet.")

        lines.extend(["", "## Plugin pages", ""])
        if self.plugin_pages:
            lines.extend([
                "| Plugin page | Description | Links |",
                "| --- | --- | --- |",
            ])
            for entry in self.plugin_pages:
                links = " · ".join(f"[{label}]({path})" for label, path in entry.links.labeled_paths()) or "-"
                lines.append(f"| `{entry.slug}` | {entry.description} | {links} |")
        else:
            lines.append("- No dedicated plugin pages discovered yet.")

        lines.extend(["", "## Inspection diffs", ""])
        if self.inspection_diffs:
            lines.extend([
                "| Diff bundle | Description | Links |",
                "| --- | --- | --- |",
            ])
            for entry in self.inspection_diffs:
                links = " · ".join(f"[{label}]({path})" for label, path in entry.links.labeled_paths()) or "-"
                lines.append(f"| {entry.title} | {entry.description} | {links} |")
        else:
            lines.append("- No inspection diff bundles discovered yet.")

        lines.extend(["", "## Release comparisons", ""])
        if self.release_comparisons:
            lines.extend([
                "| Release bundle | Description | Links |",
                "| --- | --- | --- |",
            ])
            for entry in self.release_comparisons:
                links = " · ".join(f"[{label}]({path})" for label, path in entry.links.labeled_paths()) or "-"
                lines.append(f"| {entry.title} | {entry.description} | {links} |")
        else:
            lines.append("- No release-comparison bundles discovered yet.")

        lines.extend(["", "## Benchmark reports", ""])
        if self.benchmark_reports:
            lines.extend([
                "| Report bundle | Description | Links |",
                "| --- | --- | --- |",
            ])
            for entry in self.benchmark_reports:
                links = " · ".join(f"[{label}]({path})" for label, path in entry.links.labeled_paths()) or "-"
                lines.append(f"| {entry.title} | {entry.description} | {links} |")
        else:
            lines.append("- No benchmark report bundles discovered yet.")

        lines.extend(["", "## Annotation batch manifests", ""])
        if self.annotation_batches:
            for batch in self.annotation_batches:
                lines.append(f"### {batch.title}")
                lines.append("")
                lines.append(f"- Manifest: [JSON]({batch.manifest_path})")
                shared_bits = []
                if batch.shared_csv_path:
                    shared_bits.append(f"[Shared CSV]({batch.shared_csv_path})")
                if batch.shared_heatmap_path:
                    shared_bits.append(f"[Shared heatmap CSV]({batch.shared_heatmap_path})")
                lines.append(f"- Shared artifacts: {' · '.join(shared_bits) if shared_bits else '-'}")
                lines.append("")
                lines.extend([
                    "| Preset | Filter summary | Links |",
                    "| --- | --- | --- |",
                ])
                for preset in batch.presets:
                    filters: list[str] = []
                    if preset.annotation_severities:
                        filters.append(f"severity={', '.join(preset.annotation_severities)}")
                    if preset.annotation_limit is not None:
                        filters.append(f"limit={preset.annotation_limit}")
                    if preset.annotation_overflow:
                        filters.append(f"overflow={preset.annotation_overflow}")
                    link_bits = " · ".join(f"[{label}]({path})" for label, path in preset.links.labeled_paths()) or "-"
                    filter_suffix = f" <br>{'<br>'.join(filters)}" if filters else ""
                    lines.append(f"| `{preset.name}` | {preset.description}{filter_suffix} | {link_bits} |")
                lines.append("")
        else:
            lines.append("- No annotation-batch manifests discovered yet.")

        lines.extend([
            "## Suggested portfolio usage",
            "",
            "- Lead with the HTML report links when you want a browser-friendly walkthrough instead of raw terminal output.",
            "- Use the plugin catalog first when someone wants to understand the extensibility story before reading the benchmark results.",
            "- Use the inspection diff bundle when you want to compare how two plugins expose different hook contracts or dataset families.",
            "- Use the release-comparison bundle when you want to show how the plugin suite evolved across commits instead of only comparing two adjacent plugins.",
            "- Use the annotation-batch manifest when you want both the full and portfolio-tight reviewer narratives from one shared benchmark run.",
            "- Link this index from the project README so future slices stay discoverable as more artifact families are added.",
        ])
        return "\n".join(lines).rstrip() + "\n"

    def to_html(self) -> str:
        def esc(value: object) -> str:
            return html.escape(str(value), quote=True)

        def links_html(links: DocsArtifactLinks | None) -> str:
            if links is None:
                return "-"
            labeled = links.labeled_paths()
            if not labeled:
                return "-"
            return " · ".join(f'<a href="{esc(path)}">{esc(label)}</a>' for label, path in labeled)

        browser_links: list[str] = []
        if self.plugin_catalog and self.plugin_catalog.html_path:
            browser_links.append(f'<li><a href="{esc(self.plugin_catalog.html_path)}">Plugin catalog HTML</a></li>')
        browser_links.extend(
            f'<li><a href="{esc(entry.links.html_path)}">Inspection diff HTML — {esc(entry.title)}</a></li>'
            for entry in self.inspection_diffs
            if entry.links.html_path
        )
        browser_links.extend(
            f'<li><a href="{esc(entry.links.html_path)}">Release comparison HTML — {esc(entry.title)}</a></li>'
            for entry in self.release_comparisons
            if entry.links.html_path
        )
        browser_links.extend(
            f'<li><a href="{esc(entry.links.html_path)}">Benchmark report HTML — {esc(entry.title)}</a></li>'
            for entry in self.benchmark_reports
            if entry.links.html_path
        )
        browser_links.extend(
            f'<li><a href="{esc(preset.links.html_path)}">Annotation batch HTML — {esc(batch.title)} / <code>{esc(preset.name)}</code></a></li>'
            for batch in self.annotation_batches
            for preset in batch.presets
            if preset.links.html_path
        )

        plugin_page_rows = ''.join(
            "<tr>"
            f"<td><code>{esc(entry.slug)}</code></td>"
            f"<td>{esc(entry.description)}</td>"
            f"<td>{links_html(entry.links)}</td>"
            "</tr>"
            for entry in self.plugin_pages
        )
        inspection_rows = ''.join(
            "<tr>"
            f"<td>{esc(entry.title)}</td>"
            f"<td>{esc(entry.description)}</td>"
            f"<td>{links_html(entry.links)}</td>"
            "</tr>"
            for entry in self.inspection_diffs
        )
        release_comparison_rows = ''.join(
            "<tr>"
            f"<td>{esc(entry.title)}</td>"
            f"<td>{esc(entry.description)}</td>"
            f"<td>{links_html(entry.links)}</td>"
            "</tr>"
            for entry in self.release_comparisons
        )
        report_rows = ''.join(
            "<tr>"
            f"<td>{esc(entry.title)}</td>"
            f"<td>{esc(entry.description)}</td>"
            f"<td>{links_html(entry.links)}</td>"
            "</tr>"
            for entry in self.benchmark_reports
        )
        annotation_sections = []
        for batch in self.annotation_batches:
            preset_rows = []
            for preset in batch.presets:
                filters: list[str] = []
                if preset.annotation_severities:
                    filters.append(f"severity={', '.join(preset.annotation_severities)}")
                if preset.annotation_limit is not None:
                    filters.append(f"limit={preset.annotation_limit}")
                if preset.annotation_overflow:
                    filters.append(f"overflow={preset.annotation_overflow}")
                filter_html = esc(preset.description)
                if filters:
                    filter_html += "<br><small>" + esc(" · ".join(filters)) + "</small>"
                preset_rows.append(
                    "<tr>"
                    f"<td><code>{esc(preset.name)}</code></td>"
                    f"<td>{filter_html}</td>"
                    f"<td>{links_html(preset.links)}</td>"
                    "</tr>"
                )
            shared_bits = []
            if batch.shared_csv_path:
                shared_bits.append(f'<a href="{esc(batch.shared_csv_path)}">Shared CSV</a>')
            if batch.shared_heatmap_path:
                shared_bits.append(f'<a href="{esc(batch.shared_heatmap_path)}">Shared heatmap CSV</a>')
            annotation_sections.append(
                "<section>"
                f"<h3>{esc(batch.title)}</h3>"
                f"<p><strong>Manifest:</strong> <a href=\"{esc(batch.manifest_path)}\">JSON</a></p>"
                f"<p><strong>Shared artifacts:</strong> {' · '.join(shared_bits) if shared_bits else '-'}</p>"
                "<table><thead><tr><th>Preset</th><th>Filter summary</th><th>Links</th></tr></thead>"
                f"<tbody>{''.join(preset_rows)}</tbody></table>"
                "</section>"
            )

        plugin_catalog_html = links_html(self.plugin_catalog)
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini MapReduce docs index</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1180px; padding: 0 1rem 3rem; line-height: 1.5; }}
    code {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid rgba(148, 163, 184, 0.35); padding: 0.55rem 0.7rem; text-align: left; vertical-align: top; }}
    thead th {{ background: rgba(148, 163, 184, 0.14); }}
    .hero, section {{ margin-top: 2rem; }}
    .hero {{ padding: 1.2rem 1.25rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 1rem; background: rgba(148, 163, 184, 0.08); }}
    .hero ul {{ margin-bottom: 0; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.8rem; padding: 0; }}
    .meta li {{ list-style: none; padding: 0.85rem 0.95rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Mini MapReduce docs index</h1>
  <p>A lightweight landing page for the committed Mini MapReduce artifacts so reviewers can browse plugin catalogs, dedicated plugin docs, inspection diffs, benchmark reports, and annotation-batch presets from one place.</p>
  <ul class="meta">
    <li><strong>Plugin pages</strong><br><code>{esc(len(self.plugin_pages))}</code></li>
    <li><strong>Inspection diffs</strong><br><code>{esc(len(self.inspection_diffs))}</code></li>
    <li><strong>Release comparisons</strong><br><code>{esc(len(self.release_comparisons))}</code></li>
    <li><strong>Benchmark bundles</strong><br><code>{esc(len(self.benchmark_reports))}</code></li>
    <li><strong>Annotation batches</strong><br><code>{esc(len(self.annotation_batches))}</code></li>
  </ul>
  <div class="hero">
    <h2>Browser-first links</h2>
    <ul>{''.join(browser_links) if browser_links else '<li>No HTML artifacts discovered yet.</li>'}</ul>
  </div>
  <section>
    <h2>Plugin catalog</h2>
    <p>{plugin_catalog_html}</p>
  </section>
  <section>
    <h2>Plugin pages</h2>
    {'<table><thead><tr><th>Plugin page</th><th>Description</th><th>Links</th></tr></thead><tbody>' + plugin_page_rows + '</tbody></table>' if self.plugin_pages else '<p>No dedicated plugin pages discovered yet.</p>'}
  </section>
  <section>
    <h2>Inspection diffs</h2>
    {'<table><thead><tr><th>Diff bundle</th><th>Description</th><th>Links</th></tr></thead><tbody>' + inspection_rows + '</tbody></table>' if self.inspection_diffs else '<p>No inspection diff bundles discovered yet.</p>'}
  </section>
  <section>
    <h2>Release comparisons</h2>
    {'<table><thead><tr><th>Release bundle</th><th>Description</th><th>Links</th></tr></thead><tbody>' + release_comparison_rows + '</tbody></table>' if self.release_comparisons else '<p>No release-comparison bundles discovered yet.</p>'}
  </section>
  <section>
    <h2>Benchmark reports</h2>
    {'<table><thead><tr><th>Report bundle</th><th>Description</th><th>Links</th></tr></thead><tbody>' + report_rows + '</tbody></table>' if self.benchmark_reports else '<p>No benchmark report bundles discovered yet.</p>'}
  </section>
  <section>
    <h2>Annotation batch manifests</h2>
    {''.join(annotation_sections) if annotation_sections else '<p>No annotation-batch manifests discovered yet.</p>'}
  </section>
  <section>
    <h2>Suggested portfolio usage</h2>
    <ul>
      <li>Lead with the HTML report links when you want a browser-friendly walkthrough instead of raw terminal output.</li>
      <li>Use the plugin catalog first when someone wants to understand the extensibility story before reading the benchmark results.</li>
      <li>Use the inspection diff bundle when you want to compare how two plugins expose different hook contracts or dataset families.</li>
      <li>Use the release-comparison bundle when you want to show how the plugin suite evolved across commits instead of only comparing two adjacent plugins.</li>
      <li>Use the annotation-batch manifest when you want both the full and portfolio-tight reviewer narratives from one shared benchmark run.</li>
      <li>Link this index from the project README so future slices stay discoverable as more artifact families are added.</li>
    </ul>
  </section>
</body>
</html>'''


def _is_dated_slug(parts: list[str]) -> bool:
    return (
        len(parts) >= 4
        and len(parts[0]) == 4
        and len(parts[1]) == 2
        and len(parts[2]) == 2
        and all(part.isdigit() for part in parts[:3])
    )


def humanize_docs_slug(slug: str) -> str:
    parts = [part for part in slug.split('-') if part]
    date_prefix: str | None = None
    body_parts = parts
    if _is_dated_slug(parts):
        date_prefix = "-".join(parts[:3])
        body_parts = parts[3:]
    special = {"json": "JSON", "csv": "CSV", "html": "HTML", "api": "API", "iot": "IoT"}
    label = " ".join(special.get(part.lower(), part.capitalize()) for part in body_parts) or slug
    return f"{date_prefix} · {label}" if date_prefix else label


def _artifact_relpath(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _existing_relpath(root: Path, path: Path) -> str | None:
    return _artifact_relpath(root, path) if path.exists() else None


def discover_mini_mapreduce_docs_index(artifacts_root: Path) -> MiniMapReduceDocsIndex:
    root = artifacts_root.resolve()
    if not root.exists():
        raise ValueError(f"artifacts root does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"artifacts root is not a directory: {root}")

    plugin_catalog = DocsArtifactLinks(
        markdown_path=_existing_relpath(root, root / 'plugin-catalog.md'),
        html_path=_existing_relpath(root, root / 'plugin-catalog.html'),
        json_path=_existing_relpath(root, root / 'plugin-catalog.json'),
        csv_path=_existing_relpath(root, root / 'plugin-catalog.csv'),
    )
    if not plugin_catalog.labeled_paths():
        plugin_catalog = None

    plugin_pages: list[DocsArtifactEntry] = []
    plugin_pages_dir = root / 'plugin-pages'
    if plugin_pages_dir.exists() and plugin_pages_dir.is_dir():
        stems = sorted({path.stem for path in plugin_pages_dir.iterdir() if path.suffix in {'.md', '.html'}})
        for stem in stems:
            links = DocsArtifactLinks(
                markdown_path=_existing_relpath(root, plugin_pages_dir / f'{stem}.md'),
                html_path=_existing_relpath(root, plugin_pages_dir / f'{stem}.html'),
            )
            plugin_pages.append(
                DocsArtifactEntry(
                    slug=stem,
                    title=humanize_docs_slug(stem),
                    description='Dedicated plugin reference page with hook summaries and source excerpts.',
                    links=links,
                )
            )

    inspection_diff_prefixes = sorted(
        {path.stem[:-5] for path in root.iterdir() if path.is_file() and path.suffix in {'.md', '.html', '.json'} and path.stem.endswith('-diff')}
    )
    inspection_diffs: list[DocsArtifactEntry] = []
    for prefix in inspection_diff_prefixes:
        inspection_diffs.append(
            DocsArtifactEntry(
                slug=prefix,
                title=humanize_docs_slug(prefix),
                description='Adjacent plugin contract comparison bundle with publishable Markdown/HTML plus machine-readable JSON.',
                links=DocsArtifactLinks(
                    markdown_path=_existing_relpath(root, root / f'{prefix}-diff.md'),
                    html_path=_existing_relpath(root, root / f'{prefix}-diff.html'),
                    json_path=_existing_relpath(root, root / f'{prefix}-diff.json'),
                ),
            )
        )

    release_comparison_prefixes = sorted(
        {
            path.stem[:-19]
            for path in root.iterdir()
            if path.is_file() and path.suffix in {'.md', '.html', '.json'} and path.stem.endswith('-release-comparison')
        }
    )
    release_comparisons: list[DocsArtifactEntry] = []
    for prefix in release_comparison_prefixes:
        release_comparisons.append(
            DocsArtifactEntry(
                slug=prefix,
                title=humanize_docs_slug(prefix),
                description='Release-to-release plugin snapshot comparison bundle with added/removed/changed summaries.',
                links=DocsArtifactLinks(
                    markdown_path=_existing_relpath(root, root / f'{prefix}-release-comparison.md'),
                    html_path=_existing_relpath(root, root / f'{prefix}-release-comparison.html'),
                    json_path=_existing_relpath(root, root / f'{prefix}-release-comparison.json'),
                ),
            )
        )

    report_prefixes = sorted(
        {path.stem[:-7] for path in root.iterdir() if path.is_file() and path.suffix in {'.md', '.html'} and path.stem.endswith('-report')}
    )
    benchmark_reports: list[DocsArtifactEntry] = []
    for prefix in report_prefixes:
        links = DocsArtifactLinks(
            markdown_path=_existing_relpath(root, root / f'{prefix}-report.md'),
            html_path=_existing_relpath(root, root / f'{prefix}-report.html'),
            json_path=_existing_relpath(root, root / f'{prefix}-benchmark.json'),
            csv_path=_existing_relpath(root, root / f'{prefix}-benchmark.csv'),
            heatmap_csv_path=_existing_relpath(root, root / f'{prefix}-heatmap.csv'),
        )
        if not links.labeled_paths():
            continue
        benchmark_reports.append(
            DocsArtifactEntry(
                slug=prefix,
                title=humanize_docs_slug(prefix),
                description='Benchmark report bundle with browser-friendly HTML plus raw JSON/CSV companions.',
                links=links,
            )
        )

    annotation_batches: list[DocsAnnotationBatch] = []
    for manifest_path in sorted(root.glob('*-manifest.json')):
        payload = json.loads(manifest_path.read_text(encoding='utf-8'))
        prefix = str(payload.get('prefix') or manifest_path.stem.removesuffix('-manifest'))
        shared_artifacts = payload.get('shared_artifacts') if isinstance(payload.get('shared_artifacts'), dict) else {}
        presets: list[DocsAnnotationBatchPreset] = []
        for preset in payload.get('presets', []):
            artifacts = preset.get('artifacts') if isinstance(preset.get('artifacts'), dict) else {}
            presets.append(
                DocsAnnotationBatchPreset(
                    name=str(preset.get('name') or 'preset'),
                    description=str(preset.get('description') or '-'),
                    annotation_severities=list(preset.get('annotation_severities')) if isinstance(preset.get('annotation_severities'), list) else None,
                    annotation_limit=int(preset['annotation_limit']) if preset.get('annotation_limit') is not None else None,
                    annotation_overflow=str(preset.get('annotation_overflow')) if preset.get('annotation_overflow') is not None else None,
                    links=DocsArtifactLinks(
                        markdown_path=str(artifacts.get('report')) if artifacts.get('report') else None,
                        html_path=str(artifacts.get('html')) if artifacts.get('html') else None,
                        json_path=str(artifacts.get('json')) if artifacts.get('json') else None,
                    ),
                )
            )
        annotation_batches.append(
            DocsAnnotationBatch(
                slug=prefix,
                title=humanize_docs_slug(prefix),
                manifest_path=_artifact_relpath(root, manifest_path),
                shared_csv_path=str(shared_artifacts.get('csv')) if shared_artifacts.get('csv') else None,
                shared_heatmap_path=str(shared_artifacts.get('heatmap_csv')) if shared_artifacts.get('heatmap_csv') else None,
                presets=presets,
            )
        )

    return MiniMapReduceDocsIndex(
        artifacts_root='.',
        plugin_catalog=plugin_catalog,
        plugin_pages=plugin_pages,
        inspection_diffs=inspection_diffs,
        release_comparisons=release_comparisons,
        benchmark_reports=benchmark_reports,
        annotation_batches=annotation_batches,
    )


def chunked(items: list[str], size: int) -> Iterator[list[str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for index in range(0, len(items), size):
        yield items[index : index + size]


def tokenize(text: str) -> list[str]:
    cleaned = []
    for char in text.lower():
        cleaned.append(char if char.isalnum() else " ")
    return [token for token in "".join(cleaned).split() if token]


def stable_partition(key: str, reducers: int) -> int:
    if reducers <= 0:
        raise ValueError("reducers must be positive")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % reducers


def map_wordcount(lines: Iterable[str]) -> Iterator[KeyValue]:
    for line in lines:
        for token in tokenize(line):
            yield token, 1


def map_json_group_count(lines: Iterable[str], field: str) -> Iterator[KeyValue]:
    for raw in lines:
        if not raw.strip():
            continue
        record = json.loads(raw)
        value = record.get(field, "<missing>")
        if value is None:
            value = "<null>"
        yield str(value), 1


def sum_reducer(_key: str, values: list[JSONValue]) -> int:
    return sum(int(value) for value in values)


def combine(mapped: Iterable[KeyValue], combiner_fn: Reducer = sum_reducer) -> dict[str, JSONValue]:
    grouped: defaultdict[str, list[JSONValue]] = defaultdict(list)
    for key, value in mapped:
        grouped[key].append(value)
    combined: dict[str, JSONValue] = {}
    for key, values in grouped.items():
        combined[key] = normalize_json_value(combiner_fn(key, values), context="combiner")
    return combined


def build_plugin_job(module: ModuleType, origin: Path, fallback_name: str) -> PluginJob:
    mapper = getattr(module, "map_records", None)
    combiner = getattr(module, "combine_values", None)
    reducer = getattr(module, "reduce_key", None)
    name = getattr(module, "JOB_NAME", fallback_name)
    benchmark_generator = getattr(module, "benchmark_records", None)
    benchmark_note_hook = getattr(module, "benchmark_notes", None)
    dataset_families = normalize_dataset_families(getattr(module, "BENCHMARK_DATASET_FAMILIES", None))
    if not callable(mapper):
        raise ValueError("plugin must define callable map_records(lines)")
    if combiner is not None and not callable(combiner):
        raise ValueError("plugin combine_values must be callable when provided")
    if not callable(reducer):
        raise ValueError("plugin must define callable reduce_key(key, values)")
    if benchmark_generator is not None and not callable(benchmark_generator):
        raise ValueError("plugin benchmark_records must be callable when provided")
    if benchmark_note_hook is not None and not callable(benchmark_note_hook):
        raise ValueError("plugin benchmark_notes must be callable when provided")
    return PluginJob(
        name=str(name),
        mapper=mapper,
        combiner=combiner or sum_reducer,
        reducer=reducer,
        path=origin,
        benchmark_generator=benchmark_generator,
        benchmark_note_hook=benchmark_note_hook,
        dataset_families=dataset_families,
    )


def _callable_name(fn: Callable[..., Any] | None) -> str | None:
    if fn is None:
        return None
    module = getattr(fn, "__module__", None) or "<unknown>"
    if module.startswith("mini_mapreduce_plugin_"):
        source = inspect.getsourcefile(fn)
        if source:
            module = Path(source).stem
    qualname = getattr(fn, "__qualname__", getattr(fn, "__name__", fn.__class__.__name__))
    return f"{module}.{qualname}"


def _callable_signature(fn: Callable[..., Any] | None) -> str | None:
    if fn is None:
        return None
    try:
        return f"{getattr(fn, '__name__', fn.__class__.__name__)}{inspect.signature(fn)}"
    except (TypeError, ValueError):
        return None


def _doc_summary(value: object) -> str | None:
    if value is None:
        return None
    doc = inspect.getdoc(value)
    if not doc:
        return None
    return doc.strip().splitlines()[0]


def _callable_source_lines(fn: Callable[..., Any] | None) -> tuple[list[str], int] | None:
    if fn is None:
        return None
    try:
        lines, line_number = inspect.getsourcelines(fn)
    except (OSError, TypeError):
        return None
    return lines, line_number


def _callable_source_line(fn: Callable[..., Any] | None) -> int | None:
    source = _callable_source_lines(fn)
    if source is None:
        return None
    _, line_number = source
    return line_number


def _callable_source_span(fn: Callable[..., Any] | None) -> tuple[Path, int, int] | None:
    source = _callable_source_lines(fn)
    if source is None:
        return None
    lines, start_line = source
    source_file = inspect.getsourcefile(fn)
    if not source_file:
        return None
    end_line = start_line + len(lines) - 1
    return Path(source_file), start_line, end_line


def _callable_source_anchor(fn: Callable[..., Any] | None) -> str | None:
    span = _callable_source_span(fn)
    if span is None:
        return None
    source_file, start_line, end_line = span
    return f"{source_file.name}#L{start_line}-L{end_line}"


def _github_repo_blob_base(start_path: Path, *, ref: str = "BRANCH") -> tuple[str, Path] | None:
    for candidate in [start_path, *start_path.parents]:
        if not candidate.exists():
            continue
        repo_dir = candidate if candidate.is_dir() else candidate.parent
        try:
            root = subprocess.check_output(
                ["git", "-C", str(repo_dir), "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            remote = subprocess.check_output(
                ["git", "-C", root, "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            resolved_ref = subprocess.check_output(
                ["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"] if ref == "BRANCH" else ["git", "-C", root, "rev-parse", ref],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if remote.startswith("git@github.com:"):
            remote = "https://github.com/" + remote.removeprefix("git@github.com:")
        elif remote.startswith("ssh://git@github.com/"):
            remote = "https://github.com/" + remote.removeprefix("ssh://git@github.com/")
        if remote.endswith('.git'):
            remote = remote[:-4]
        if not remote.startswith("https://github.com/"):
            return None
        return f"{remote}/blob/{resolved_ref}", Path(root)
    return None


def _callable_source_url(fn: Callable[..., Any] | None, *, ref: str = "BRANCH") -> str | None:
    span = _callable_source_span(fn)
    if span is None:
        return None
    source_file, start_line, end_line = span
    repo = _github_repo_blob_base(source_file, ref=ref)
    if repo is None:
        return None
    blob_base, root = repo
    try:
        relative_path = source_file.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return f"{blob_base}/{relative_path.as_posix()}#L{start_line}-L{end_line}"


def _repo_head_commit(start_path: Path) -> str | None:
    repo = _github_repo_blob_base(start_path)
    if repo is None:
        return None
    _, root = repo
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _callable_source_excerpt(fn: Callable[..., Any] | None) -> str | None:
    source = _callable_source_lines(fn)
    if source is None:
        return None
    lines, _ = source
    return "".join(f"{line.rstrip()}\n" for line in lines).rstrip() or None


def _render_hook_html(name: str | None, signature: str | None, doc_summary: str | None, source_line: int | None, source_anchor: str | None = None, source_url: str | None = None, source_commit_url: str | None = None) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    if not name:
        return "-"
    meta = [f"<code>{esc(signature or '-')}</code>"]
    if source_line is not None:
        meta.append(f"line {esc(source_line)}")
    if source_anchor:
        meta.append(f"anchor <code>{esc(source_anchor)}</code>")
    if source_url:
        meta.append(f'<a href="{esc(source_url)}">github</a>')
    if source_commit_url:
        meta.append(f'<a href="{esc(source_commit_url)}">commit</a>')
    if doc_summary:
        meta.append(esc(doc_summary))
    return f"<code>{esc(name)}</code><br><small>{'<br>'.join(meta)}</small>"


def _module_doc_summary(module_path: Path) -> str | None:
    if not module_path.exists() or module_path.suffix != ".py":
        return None
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    doc = ast.get_docstring(tree)
    if not doc:
        return None
    return doc.strip().splitlines()[0]


def inspect_plugin(plugin_ref: str | Path) -> PluginInspection:
    plugin = load_plugin(plugin_ref)
    plugin_repo_commit = _repo_head_commit(plugin.path)
    return PluginInspection(
        name=plugin.name,
        plugin=plugin_display_path(str(plugin.path)),
        plugin_repo_commit=plugin_repo_commit,
        module_doc_summary=_module_doc_summary(plugin.path),
        mapper=_callable_name(plugin.mapper) or "<unknown>",
        mapper_signature=_callable_signature(plugin.mapper),
        mapper_doc_summary=_doc_summary(plugin.mapper),
        mapper_source_line=_callable_source_line(plugin.mapper),
        mapper_source_anchor=_callable_source_anchor(plugin.mapper),
        mapper_source_url=_callable_source_url(plugin.mapper, ref="BRANCH"),
        mapper_source_commit_url=_callable_source_url(plugin.mapper, ref=plugin_repo_commit or "HEAD"),
        mapper_source_excerpt=_callable_source_excerpt(plugin.mapper),
        reducer=_callable_name(plugin.reducer) or "<unknown>",
        reducer_signature=_callable_signature(plugin.reducer),
        reducer_doc_summary=_doc_summary(plugin.reducer),
        reducer_source_line=_callable_source_line(plugin.reducer),
        reducer_source_anchor=_callable_source_anchor(plugin.reducer),
        reducer_source_url=_callable_source_url(plugin.reducer, ref="BRANCH"),
        reducer_source_commit_url=_callable_source_url(plugin.reducer, ref=plugin_repo_commit or "HEAD"),
        reducer_source_excerpt=_callable_source_excerpt(plugin.reducer),
        combiner=_callable_name(plugin.combiner),
        combiner_signature=_callable_signature(plugin.combiner),
        combiner_doc_summary=_doc_summary(plugin.combiner),
        combiner_source_line=_callable_source_line(plugin.combiner),
        combiner_source_anchor=_callable_source_anchor(plugin.combiner),
        combiner_source_url=_callable_source_url(plugin.combiner, ref="BRANCH"),
        combiner_source_commit_url=_callable_source_url(plugin.combiner, ref=plugin_repo_commit or "HEAD"),
        combiner_source_excerpt=_callable_source_excerpt(plugin.combiner),
        benchmark_generator=_callable_name(plugin.benchmark_generator),
        benchmark_generator_signature=_callable_signature(plugin.benchmark_generator),
        benchmark_generator_doc_summary=_doc_summary(plugin.benchmark_generator),
        benchmark_generator_source_line=_callable_source_line(plugin.benchmark_generator),
        benchmark_generator_source_anchor=_callable_source_anchor(plugin.benchmark_generator),
        benchmark_generator_source_url=_callable_source_url(plugin.benchmark_generator, ref="BRANCH"),
        benchmark_generator_source_commit_url=_callable_source_url(plugin.benchmark_generator, ref=plugin_repo_commit or "HEAD"),
        benchmark_generator_source_excerpt=_callable_source_excerpt(plugin.benchmark_generator),
        benchmark_note_hook=_callable_name(plugin.benchmark_note_hook),
        benchmark_note_hook_signature=_callable_signature(plugin.benchmark_note_hook),
        benchmark_note_hook_doc_summary=_doc_summary(plugin.benchmark_note_hook),
        benchmark_note_hook_source_line=_callable_source_line(plugin.benchmark_note_hook),
        benchmark_note_hook_source_anchor=_callable_source_anchor(plugin.benchmark_note_hook),
        benchmark_note_hook_source_url=_callable_source_url(plugin.benchmark_note_hook, ref="BRANCH"),
        benchmark_note_hook_source_commit_url=_callable_source_url(plugin.benchmark_note_hook, ref=plugin_repo_commit or "HEAD"),
        benchmark_note_hook_source_excerpt=_callable_source_excerpt(plugin.benchmark_note_hook),
        available_dataset_families=list(plugin.dataset_families) if plugin.dataset_families else None,
    )


def diff_plugin_inspections(plugins: list[PluginInspection]) -> list[PluginInspectionDiff]:
    diffs: list[PluginInspectionDiff] = []
    for previous, current in zip(plugins, plugins[1:]):
        previous_payload = previous.as_dict()
        current_payload = current.as_dict()
        changes: dict[str, dict[str, object | None]] = {}
        for field in PLUGIN_INSPECTION_DIFF_FIELDS:
            if previous_payload[field] != current_payload[field]:
                changes[field] = {
                    "previous": previous_payload[field],
                    "current": current_payload[field],
                }
        diffs.append(
            PluginInspectionDiff(
                previous_plugin=previous.plugin,
                current_plugin=current.plugin,
                changed_fields=sorted(changes),
                changes=changes,
            )
        )
    return diffs


def inspect_plugins(plugin_refs: list[str | Path], *, include_diffs: bool = False) -> PluginInspectionBatch:
    if not plugin_refs:
        raise ValueError("at least one plugin is required for inspection")
    plugins = [inspect_plugin(plugin_ref) for plugin_ref in plugin_refs]
    return PluginInspectionBatch(plugins=plugins, diffs=diff_plugin_inspections(plugins) if include_diffs else None)


def load_plugin(plugin_ref: str | Path) -> PluginJob:
    plugin_text = str(plugin_ref)
    candidate_path = Path(plugin_text)
    if candidate_path.exists():
        resolved = candidate_path.resolve()
        module_name = f"mini_mapreduce_plugin_{hashlib.sha256(str(resolved).encode('utf-8')).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ValueError(f"unable to load plugin module: {plugin_text}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return build_plugin_job(module, resolved, resolved.stem)

    try:
        module = importlib.import_module(plugin_text)
    except ModuleNotFoundError as exc:
        raise ValueError(f"plugin does not exist or is not importable: {plugin_text}") from exc

    module_file = getattr(module, "__file__", None)
    origin = Path(module_file).resolve() if module_file else Path(f"<module:{plugin_text}>")
    return build_plugin_job(module, origin, plugin_text.rsplit('.', 1)[-1])


def summarize_value_records(value: JSONValue) -> int:
    if isinstance(value, Number) and not isinstance(value, bool):
        return int(value)
    return 1


def summarize_partial_by_reducer(partial: dict[str, JSONValue], reducers: int) -> list[dict[str, int]]:
    summary = [{"reducer": reducer_id, "unique_keys": 0, "records": 0} for reducer_id in range(reducers)]
    for key, value in partial.items():
        reducer_id = stable_partition(key, reducers)
        summary[reducer_id]["unique_keys"] += 1
        summary[reducer_id]["records"] += summarize_value_records(value)
    return summary


def reduce_shards(
    partials: Iterable[dict[str, JSONValue]],
    reducers: int,
    reducer_fn: Reducer = sum_reducer,
) -> tuple[dict[str, JSONValue], list[dict[str, int]]]:
    if reducers <= 0:
        raise ValueError("reducers must be positive")
    buckets: list[defaultdict[str, list[JSONValue]]] = [defaultdict(list) for _ in range(reducers)]
    for partial in partials:
        for key, value in partial.items():
            buckets[stable_partition(key, reducers)][key].append(value)

    reduced: dict[str, JSONValue] = {}
    reducer_stats: list[dict[str, int]] = []
    for reducer_id, bucket in enumerate(buckets):
        reducer_records = 0
        for key, values in bucket.items():
            reduced[key] = normalize_json_value(reducer_fn(key, list(values)), context="reducer")
            if all(isinstance(value, Number) and not isinstance(value, bool) for value in values):
                reducer_records += sum(int(value) for value in values)
            else:
                reducer_records += len(values)
        reducer_stats.append(
            {
                "reducer": reducer_id,
                "unique_keys": len(bucket),
                "records": reducer_records,
            }
        )

    return order_output(reduced), reducer_stats


def reducer_skew(reducer_stats: list[dict[str, int]]) -> float:
    records = [item["records"] for item in reducer_stats]
    if not records:
        return 0.0
    average = sum(records) / len(records)
    if average == 0:
        return 0.0
    return max(records) / average


def read_lines(inputs: list[Path]) -> list[str]:
    lines: list[str] = []
    for path in inputs:
        lines.extend(path.read_text(encoding="utf-8").splitlines())
    return lines


def execute_job(
    job: str,
    inputs: list[Path],
    shard_size: int,
    group_field: str | None = None,
    reducers: int = 1,
    plugin_path: str | None = None,
) -> JobResult:
    lines = read_lines(inputs)
    partials: list[dict[str, JSONValue]] = []
    map_records = 0
    plugin: PluginJob | None = None

    mapper: Mapper
    combiner_fn: Reducer = sum_reducer
    reducer_fn: Reducer = sum_reducer
    resolved_job_name = job
    if job == "wordcount":
        mapper = map_wordcount
    elif job == "json-group-count":
        if not group_field:
            raise ValueError("group_field is required for json-group-count")
        mapper = lambda shard: map_json_group_count(shard, group_field)
    elif job == "plugin":
        if plugin_path is None:
            raise ValueError("plugin_path is required for plugin jobs")
        plugin = load_plugin(plugin_path)
        mapper = plugin.mapper
        combiner_fn = plugin.combiner
        reducer_fn = plugin.reducer
        resolved_job_name = plugin.name
    else:
        raise ValueError(f"unsupported job: {job}")

    shards = list(chunked(lines, shard_size)) or [[]]
    for shard in shards:
        mapped = [(key, normalize_json_value(value, context="mapper")) for key, value in mapper(shard)]
        map_records += len(mapped)
        partials.append(combine(mapped, combiner_fn=combiner_fn))

    reduced, reducer_stats = reduce_shards(partials, reducers, reducer_fn=reducer_fn)
    return JobResult(
        job=resolved_job_name,
        plugin=plugin_display_path(str(plugin.path)) if plugin else None,
        inputs=[str(path) for path in inputs],
        shard_count=len(shards),
        map_records=map_records,
        unique_keys=len(reduced),
        reducers=reducers,
        reducer_stats=reducer_stats,
        output=reduced,
    )


def build_benchmark_lines(
    job: str,
    scenario: str,
    records: int,
    seed: int,
    plugin: PluginJob | None = None,
    dataset_family: str = "default",
) -> list[str]:
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    if job == "plugin" and plugin is not None and plugin.benchmark_generator is not None:
        signature = inspect.signature(plugin.benchmark_generator)
        accepts_dataset_family = len(signature.parameters) >= 4
        if plugin.dataset_families and dataset_family not in plugin.dataset_families:
            raise ValueError(
                f"unsupported dataset_family for plugin benchmark: {dataset_family} (supported: {', '.join(plugin.dataset_families)})"
            )
        if dataset_family != "default" and not accepts_dataset_family:
            raise ValueError("plugin benchmark_records does not support dataset_family")
        plugin_lines = (
            plugin.benchmark_generator(scenario, records, seed, dataset_family)
            if accepts_dataset_family
            else plugin.benchmark_generator(scenario, records, seed)
        )
        if not isinstance(plugin_lines, list) or not all(isinstance(line, str) for line in plugin_lines):
            raise ValueError("plugin benchmark_records must return a list of strings")
        if len(plugin_lines) != records:
            raise ValueError("plugin benchmark_records must return exactly records lines")
        return plugin_lines
    if job == "wordcount":
        if dataset_family not in {"default", "news", "logs"}:
            raise ValueError(f"unsupported dataset_family for wordcount benchmark: {dataset_family}")
        if scenario == "balanced":
            if dataset_family == "logs":
                services = [f"svc-{index:02d}" for index in range(12)]
                levels = ["info", "warn", "error", "debug"]
                return [f"{services[index % len(services)]} {levels[index % len(levels)]}" for index in range(records)]
            keys = [f"key-{index:02d}" for index in range(24)] if dataset_family == "default" else [f"topic-{index:02d}" for index in range(24)]
            return [f"{keys[index % len(keys)]} {keys[(index * 7) % len(keys)]}" for index in range(records)]
        if scenario == "skewed":
            if dataset_family == "logs":
                hot_keys = ["checkout:error"] * 12 + [f"service-{index}:warn" for index in range(6)] + [f"service-{index}:info" for index in range(18)]
            elif dataset_family == "news":
                hot_keys = ["breaking-news"] * 12 + [f"desk-{index}" for index in range(6)] + [f"beat-{index}" for index in range(18)]
            else:
                hot_keys = ["hot-key"] * 12 + [f"warm-{index}" for index in range(6)] + [f"cold-{index}" for index in range(18)]
            return [f"{rng.choice(hot_keys)} {rng.choice(hot_keys)}" for _ in range(records)]
    if job == "json-group-count":
        if dataset_family not in {"default", "incidents", "deployments"}:
            raise ValueError(f"unsupported dataset_family for json-group-count benchmark: {dataset_family}")
        if scenario == "balanced":
            if dataset_family == "incidents":
                statuses = ["detected", "triaged", "mitigated", "resolved"]
                services = [f"svc-{index:02d}" for index in range(6)]
                return [
                    json.dumps({"status": statuses[index % len(statuses)], "service": services[index % len(services)], "severity": ["sev1", "sev2", "sev3"][index % 3]}, sort_keys=True)
                    for index in range(records)
                ]
            if dataset_family == "deployments":
                statuses = ["queued", "running", "passed", "rolled_back"]
                teams = [f"team-{index:02d}" for index in range(6)]
                return [
                    json.dumps({"status": statuses[index % len(statuses)], "team": teams[index % len(teams)], "region": ["us-east", "eu-west", "ap-south"][index % 3]}, sort_keys=True)
                    for index in range(records)
                ]
            statuses = ["ok", "error", "retry", "queued"]
            sources = [f"ingest-{index:02d}" for index in range(6)]
            return [
                json.dumps({"status": statuses[index % len(statuses)], "source": sources[index % len(sources)]}, sort_keys=True)
                for index in range(records)
            ]
        if scenario == "skewed":
            if dataset_family == "incidents":
                statuses = ["triaged"] * 14 + ["detected"] * 6 + ["mitigated"] * 4 + ["resolved"] * 4
                services = [f"payments-{index}" for index in range(3)] + [f"edge-{index}" for index in range(5)]
                return [
                    json.dumps({"status": rng.choice(statuses), "service": rng.choice(services), "severity": rng.choice(["sev1", "sev2", "sev3"])}, sort_keys=True)
                    for _ in range(records)
                ]
            if dataset_family == "deployments":
                statuses = ["running"] * 12 + ["queued"] * 8 + ["passed"] * 4 + ["rolled_back"] * 2
                teams = ["release-core"] * 8 + [f"service-{index}" for index in range(8)]
                return [
                    json.dumps({"status": rng.choice(statuses), "team": rng.choice(teams), "region": rng.choice(["us-east", "eu-west", "ap-south"])}, sort_keys=True)
                    for _ in range(records)
                ]
            statuses = ["ok"] * 12 + ["retry"] * 8 + ["error"] * 4 + ["queued"] * 2
            sources = ["gateway"] * 8 + [f"ingest-{index}" for index in range(8)]
            return [
                json.dumps({"status": rng.choice(statuses), "source": rng.choice(sources)}, sort_keys=True)
                for _ in range(records)
            ]
    if job == "plugin":
        if scenario == "balanced":
            if dataset_family == "project-week":
                students = [f"squad-{index:02d}" for index in range(16)]
                return [f"{students[index % len(students)]},{68 + ((index * 13) % 27)}" for index in range(records)]
            students = [f"student-{index:02d}" for index in range(24)]
            return [f"{students[index % len(students)]},{70 + ((index * 11) % 31)}" for index in range(records)]
        if scenario == "skewed":
            if dataset_family == "exam-cram":
                hot_students = ["exam-cram-core"] * 14 + [f"late-night-{index}" for index in range(4)] + [f"steady-{index}" for index in range(14)]
            elif dataset_family == "project-week":
                hot_students = ["demo-day-core"] * 12 + [f"integration-{index}" for index in range(6)] + [f"feature-{index}" for index in range(18)]
            else:
                hot_students = ["capstone-lead"] * 12 + [f"frequent-{index}" for index in range(6)] + [f"rare-{index}" for index in range(18)]
            return [f"{rng.choice(hot_students)},{55 + rng.randint(0, 45)}" for _ in range(records)]
    raise ValueError(f"unsupported benchmark scenario: {scenario}")


def benchmark_job(
    job: str,
    scenario: str,
    records: int,
    shard_size: int,
    reducers: list[int],
    seed: int = 42,
    plugin_path: str | None = None,
    dataset_family: str = "default",
    group_field: str | None = None,
    annotation_severities: list[str] | None = None,
    annotation_limit: int | None = None,
    annotation_overflow: str = "drop",
) -> BenchmarkResult:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    if not reducers:
        raise ValueError("at least one reducer count is required")
    if any(count <= 0 for count in reducers):
        raise ValueError("reducers must be positive")
    if annotation_limit is not None and annotation_limit <= 0:
        raise ValueError("annotation_limit must be positive")

    benchmark_plugin: PluginJob | None = None
    resolved_group_field = group_field or "status"
    if job == "plugin":
        if plugin_path is None:
            raise ValueError("plugin_path is required for plugin benchmarks")
        benchmark_plugin = load_plugin(plugin_path)
    lines = build_benchmark_lines(job, scenario, records, seed, benchmark_plugin, dataset_family=dataset_family)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", prefix="mini-mapreduce-benchmark-", delete=False) as handle:
        handle.write("\n".join(lines) + "\n")
        input_path = Path(handle.name)

    timings: list[dict[str, int | float]] = []
    heatmap_rows: list[dict[str, int | str]] = []
    benchmark_plugin_ref = plugin_display_path(str(benchmark_plugin.path)) if benchmark_plugin else None
    benchmark_shards = list(chunked(lines, shard_size)) or [[]]
    if job == "wordcount":
        benchmark_mapper = map_wordcount
        benchmark_combiner = sum_reducer
    elif job == "json-group-count":
        benchmark_mapper = lambda shard: map_json_group_count(shard, resolved_group_field)
        benchmark_combiner = sum_reducer
    elif job == "plugin":
        assert benchmark_plugin is not None
        benchmark_mapper = benchmark_plugin.mapper
        benchmark_combiner = benchmark_plugin.combiner
    else:
        raise ValueError(f"unsupported benchmark job: {job}")

    benchmark_partials = [
        combine([(key, normalize_json_value(value, context="mapper")) for key, value in benchmark_mapper(shard)], combiner_fn=benchmark_combiner)
        for shard in benchmark_shards
    ]
    unique_keys = 0
    try:
        for reducer_count in reducers:
            started = time.perf_counter()
            result = execute_job(
                job,
                [input_path],
                shard_size=shard_size,
                reducers=reducer_count,
                plugin_path=plugin_path,
                group_field=resolved_group_field if job == "json-group-count" else group_field,
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            unique_keys = result.unique_keys
            timings.append(
                {
                    "reducers": reducer_count,
                    "elapsed_ms": elapsed_ms,
                    "shards": result.shard_count,
                    "map_records": result.map_records,
                    "unique_keys": result.unique_keys,
                    "max_reducer_records": max((item["records"] for item in result.reducer_stats), default=0),
                    "skew_ratio": round(reducer_skew(result.reducer_stats), 3),
                }
            )
            for shard_index, partial in enumerate(benchmark_partials):
                for summary in summarize_partial_by_reducer(partial, reducer_count):
                    heatmap_rows.append(
                        {
                            "job": job,
                            "plugin": benchmark_plugin_ref,
                            "scenario": scenario,
                            "dataset_family": dataset_family,
                            "seed": seed,
                            "reducers": reducer_count,
                            "shard_index": shard_index,
                            "reducer": summary["reducer"],
                            "records": summary["records"],
                            "unique_keys": summary["unique_keys"],
                        }
                    )
    finally:
        input_path.unlink(missing_ok=True)

    inspection = inspect_plugin(plugin_path) if benchmark_plugin and plugin_path is not None else None
    benchmark_notes, benchmark_note_annotations, annotation_view = benchmark_notes_for(
        job,
        scenario,
        dataset_family,
        records=records,
        seed=seed,
        plugin=benchmark_plugin,
        annotation_severities=annotation_severities,
        annotation_limit=annotation_limit,
        annotation_overflow=annotation_overflow,
    )
    return BenchmarkResult(
        job=job if job != "plugin" or benchmark_plugin is None else benchmark_plugin.name,
        plugin=benchmark_plugin_ref,
        available_dataset_families=(
            list(benchmark_plugin.dataset_families)
            if benchmark_plugin and benchmark_plugin.dataset_families
            else (["default", "news", "logs"] if job == "wordcount" else (["default", "incidents", "deployments"] if job == "json-group-count" else None))
        ),
        benchmark_notes=benchmark_notes,
        benchmark_note_annotations=benchmark_note_annotations or None,
        annotation_view=annotation_view,
        plugin_mapper=inspection.mapper if inspection else None,
        plugin_reducer=inspection.reducer if inspection else None,
        plugin_combiner=inspection.combiner if inspection else None,
        plugin_benchmark_generator=inspection.benchmark_generator if inspection else None,
        plugin_benchmark_note_hook=inspection.benchmark_note_hook if inspection else None,
        scenario=scenario,
        dataset_family=dataset_family,
        seed=seed,
        total_records=records,
        unique_keys=unique_keys,
        shard_size=shard_size,
        reducers=reducers,
        timings_ms=timings,
        heatmap_rows=heatmap_rows,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny MapReduce-style data processing lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a built-in MapReduce job")
    run_parser.add_argument("job", choices=[*BUILTIN_JOBS, "plugin"])
    run_parser.add_argument("inputs", nargs="+", help="input text or JSONL files")
    run_parser.add_argument("--shard-size", type=int, default=100, help="lines per shard")
    run_parser.add_argument("--reducers", type=int, default=1, help="number of reducer buckets to simulate")
    run_parser.add_argument("--group-field", help="JSON field to count for json-group-count")
    run_parser.add_argument("--plugin", help="plugin file path or importable Python module with map_records/reduce_key")
    run_parser.add_argument("--output", help="optional output JSON path")

    inspect_parser = subparsers.add_parser("inspect-plugin", help="inspect plugin metadata and exported hooks")
    inspect_parser.add_argument(
        "--plugin",
        required=True,
        action="append",
        help="plugin file path or importable Python module to inspect (repeat to inspect multiple plugins)",
    )
    inspect_parser.add_argument("--output", help="optional output JSON path")
    inspect_parser.add_argument("--csv-output", help="optional plugin inspection CSV output path")
    inspect_parser.add_argument("--report-output", help="optional Markdown inspection report path")
    inspect_parser.add_argument("--html-output", help="optional HTML inspection report path")
    inspect_parser.add_argument(
        "--diff",
        action="store_true",
        help="include adjacent plugin metadata diffs in the JSON inspection payload when multiple plugins are provided",
    )

    catalog_parser = subparsers.add_parser("catalog-plugins", help="discover local plugins and emit catalog artifacts")
    catalog_parser.add_argument("--root", help="directory to search for plugin files (defaults to the project directory)")
    catalog_parser.add_argument("--pattern", default="plugins_*.py", help="filename glob for plugin discovery")
    catalog_parser.add_argument("--output", help="optional output JSON path")
    catalog_parser.add_argument("--csv-output", help="optional plugin catalog CSV output path")
    catalog_parser.add_argument("--report-output", help="optional Markdown plugin catalog report path")
    catalog_parser.add_argument("--html-output", help="optional HTML plugin catalog report path")
    catalog_parser.add_argument("--docs-dir", help="optional directory for dedicated per-plugin Markdown/HTML docs pages")
    catalog_parser.add_argument(
        "--diff",
        action="store_true",
        help="include adjacent plugin metadata diffs in the JSON/report catalog payload",
    )

    docs_index_parser = subparsers.add_parser(
        "docs-index",
        help="scan committed Mini MapReduce docs artifacts and emit a landing-page index",
    )
    docs_index_parser.add_argument(
        "--artifacts-root",
        required=True,
        help="directory containing the committed docs/artifacts bundle to index",
    )
    docs_index_parser.add_argument("--output", help="optional Markdown docs index output path")
    docs_index_parser.add_argument("--html-output", help="optional HTML docs index output path")

    compare_parser = subparsers.add_parser(
        "compare-plugin-releases",
        help="compare two saved plugin inspection/catalog snapshots across releases",
    )
    compare_parser.add_argument("--before", required=True, help="earlier inspect-plugin/catalog-plugins JSON snapshot")
    compare_parser.add_argument("--after", required=True, help="later inspect-plugin/catalog-plugins JSON snapshot")
    compare_parser.add_argument("--before-label", help="optional human-friendly label for the earlier snapshot")
    compare_parser.add_argument("--after-label", help="optional human-friendly label for the later snapshot")
    compare_parser.add_argument("--output", help="optional JSON release-comparison output path")
    compare_parser.add_argument("--report-output", help="optional Markdown release-comparison output path")
    compare_parser.add_argument("--html-output", help="optional HTML release-comparison output path")

    benchmark_parser = subparsers.add_parser("benchmark", help="run a synthetic MapReduce benchmark")
    benchmark_parser.add_argument("--job", choices=["wordcount", "json-group-count", "plugin"], default="wordcount")
    benchmark_parser.add_argument("--scenario", choices=["balanced", "skewed"], default="skewed")
    benchmark_parser.add_argument("--records", type=int, default=5000, help="synthetic input line count")
    benchmark_parser.add_argument("--shard-size", type=int, default=250, help="lines per shard")
    benchmark_parser.add_argument("--reducers", type=int, nargs="+", default=[1, 2, 4, 8], help="one or more reducer counts to compare")
    benchmark_parser.add_argument("--seed", type=int, default=42, help="seed for deterministic synthetic data generation")
    benchmark_parser.add_argument("--dataset-family", default="default", help="synthetic dataset family to use for benchmark generation")
    benchmark_parser.add_argument("--group-field", default="status", help="JSON field to group for json-group-count benchmarks")
    benchmark_parser.add_argument(
        "--annotation-severity",
        dest="annotation_severities",
        nargs="+",
        action="extend",
        help="optional structured-annotation severities to keep (for example: --annotation-severity risk watch)",
    )
    benchmark_parser.add_argument("--annotation-limit", type=int, help="optional maximum number of structured annotation cards to render")
    benchmark_parser.add_argument(
        "--annotation-overflow",
        choices=["drop", "summary"],
        default="drop",
        help="how to handle structured annotations beyond --annotation-limit",
    )
    benchmark_parser.add_argument("--plugin", help="plugin file path or importable Python module for plugin benchmarks")
    benchmark_parser.add_argument("--output", help="optional output JSON path")
    benchmark_parser.add_argument("--csv-output", help="optional benchmark CSV output path")
    benchmark_parser.add_argument("--heatmap-output", help="optional shard-to-reducer heatmap CSV output path")
    benchmark_parser.add_argument("--report-output", help="optional Markdown benchmark report path")
    benchmark_parser.add_argument("--html-output", help="optional HTML benchmark report path")
    benchmark_parser.add_argument(
        "--annotation-batch-dir",
        help="optional directory that emits full and filtered annotation-view artifacts from one shared benchmark run",
    )
    benchmark_parser.add_argument(
        "--annotation-batch-prefix",
        help="optional filename prefix to use inside --annotation-batch-dir",
    )
    benchmark_parser.add_argument(
        "--annotation-batch-preset",
        action="append",
        choices=sorted(ANNOTATION_BATCH_PRESETS),
        help="annotation batch preset(s) to emit inside --annotation-batch-dir (defaults to full + portfolio-tight)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        if args.job == "json-group-count" and not args.group_field:
            parser.error("--group-field is required for json-group-count")
        if args.job == "plugin" and not args.plugin:
            parser.error("--plugin is required for plugin jobs")
        if args.reducers <= 0:
            parser.error("--reducers must be positive")
        try:
            result = execute_job(
                job=args.job,
                inputs=[Path(item) for item in args.inputs],
                shard_size=args.shard_size,
                group_field=args.group_field,
                reducers=args.reducers,
                plugin_path=args.plugin if args.plugin else None,
            )
        except ValueError as exc:
            parser.error(str(exc))
        rendered = result.to_json()
        if args.output:
            write_text_output(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0

    if args.command == "inspect-plugin":
        if args.diff and len(args.plugin) < 2:
            parser.error("--diff requires at least two --plugin values")
        try:
            result = inspect_plugins(args.plugin, include_diffs=args.diff)
        except ValueError as exc:
            parser.error(str(exc))
        rendered = result.plugins[0].to_json() if len(result.plugins) == 1 and not args.diff else result.to_json()
        if args.output:
            write_text_output(args.output, rendered + "\n")
        elif not args.csv_output and not args.report_output and not args.html_output:
            print(rendered)
        if args.csv_output:
            write_text_output(args.csv_output, result.to_csv())
        if args.report_output:
            write_text_output(args.report_output, result.to_markdown())
        if args.html_output:
            write_text_output(args.html_output, result.to_html())
        return 0

    if args.command == "catalog-plugins":
        try:
            plugin_refs = discover_plugin_refs(Path(args.root) if args.root else None, pattern=args.pattern)
            result = inspect_plugins(plugin_refs, include_diffs=args.diff)
        except ValueError as exc:
            parser.error(str(exc))
        rendered = result.to_json()
        docs_dir = Path(args.docs_dir) if args.docs_dir else None
        if args.output:
            write_text_output(args.output, rendered + "\n")
        elif not args.csv_output and not args.report_output and not args.html_output and not args.docs_dir:
            print(rendered)
        if args.csv_output:
            write_text_output(args.csv_output, result.to_csv())
        if args.report_output:
            markdown_links = (
                build_plugin_page_links(
                    result.plugins,
                    docs_dir=docs_dir,
                    output_parent=Path(args.report_output).resolve().parent,
                    suffix=".md",
                )
                if docs_dir
                else None
            )
            write_text_output(args.report_output, result.to_markdown(page_links=markdown_links))
        if args.html_output:
            html_links = (
                build_plugin_page_links(
                    result.plugins,
                    docs_dir=docs_dir,
                    output_parent=Path(args.html_output).resolve().parent,
                    suffix=".html",
                )
                if docs_dir
                else None
            )
            write_text_output(args.html_output, result.to_html(page_links=html_links))
        if docs_dir:
            write_plugin_doc_pages(
                result.plugins,
                docs_dir=docs_dir,
                catalog_markdown_path=Path(args.report_output).resolve() if args.report_output else None,
                catalog_html_path=Path(args.html_output).resolve() if args.html_output else None,
            )
        return 0

    if args.command == "docs-index":
        try:
            result = discover_mini_mapreduce_docs_index(Path(args.artifacts_root))
        except (ValueError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        rendered = result.to_json()
        if args.output:
            write_text_output(args.output, result.to_markdown())
        if args.html_output:
            write_text_output(args.html_output, result.to_html())
        if not args.output and not args.html_output:
            print(rendered)
        return 0

    if args.command == "compare-plugin-releases":
        try:
            before_snapshot = load_plugin_inspection_snapshot(args.before)
            after_snapshot = load_plugin_inspection_snapshot(args.after)
            result = compare_plugin_release_snapshots(
                before_snapshot,
                after_snapshot,
                before_label=args.before_label or Path(args.before).name,
                after_label=args.after_label or Path(args.after).name,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        rendered = result.to_json()
        if args.output:
            write_text_output(args.output, rendered + "\n")
        elif not args.report_output and not args.html_output:
            print(rendered)
        if args.report_output:
            write_text_output(args.report_output, result.to_markdown())
        if args.html_output:
            write_text_output(args.html_output, result.to_html())
        return 0

    if args.command == "benchmark":
        if args.records <= 0:
            parser.error("--records must be positive")
        if args.shard_size <= 0:
            parser.error("--shard-size must be positive")
        if any(count <= 0 for count in args.reducers):
            parser.error("--reducers values must be positive")
        if args.annotation_limit is not None and args.annotation_limit <= 0:
            parser.error("--annotation-limit must be positive")
        if args.annotation_batch_preset and not args.annotation_batch_dir:
            parser.error("--annotation-batch-preset requires --annotation-batch-dir")
        if args.job == "plugin" and not args.plugin:
            parser.error("--plugin is required for plugin benchmarks")
        try:
            result = benchmark_job(
                job=args.job,
                scenario=args.scenario,
                records=args.records,
                shard_size=args.shard_size,
                reducers=args.reducers,
                seed=args.seed,
                plugin_path=args.plugin if args.plugin else None,
                dataset_family=args.dataset_family,
                group_field=args.group_field if args.job == "json-group-count" else None,
                annotation_severities=args.annotation_severities,
                annotation_limit=args.annotation_limit,
                annotation_overflow=args.annotation_overflow,
            )
            batch_manifest: BenchmarkPresetBatch | None = None
            if args.annotation_batch_dir:
                benchmark_plugin = load_plugin(args.plugin) if args.job == "plugin" and args.plugin else None
                batch_manifest = build_benchmark_preset_batch(
                    result,
                    note_items=benchmark_note_items_for(
                        args.job,
                        args.scenario,
                        args.dataset_family,
                        records=args.records,
                        seed=args.seed,
                        plugin=benchmark_plugin,
                    ),
                    output_dir=Path(args.annotation_batch_dir),
                    prefix=args.annotation_batch_prefix,
                    preset_names=args.annotation_batch_preset,
                )
        except ValueError as exc:
            parser.error(str(exc))
        rendered = result.to_json()
        if args.output:
            write_text_output(args.output, rendered + "\n")
        elif not args.annotation_batch_dir:
            print(rendered)
        if args.csv_output:
            write_text_output(args.csv_output, result.to_csv())
        if args.heatmap_output:
            write_text_output(args.heatmap_output, result.heatmap_to_csv())
        if args.report_output:
            write_text_output(args.report_output, result.to_markdown())
        if args.html_output:
            write_text_output(args.html_output, result.to_html())
        if batch_manifest is not None:
            manifest_path = Path(args.annotation_batch_dir) / f"{batch_manifest.prefix}-manifest.json"
            write_text_output(manifest_path, batch_manifest.to_json() + "\n")
        return 0

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
