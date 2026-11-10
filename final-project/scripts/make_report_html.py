#!/usr/bin/env python3
"""Convert report/report.md into a print-ready A4 HTML report.

Single source of truth: the Markdown is authoritative; this script only adds
typography and pagination. Pure standard library. The resulting HTML is opened
by the locally installed Microsoft Word to export report.docx and report.pdf.

Usage:  python scripts/make_report_html.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "report" / "report.md"
DST = ROOT / "report" / "report.html"

CSS = """
@page { size: A4; margin: 19mm 17mm 17mm 17mm; }
body { font-family: Calibri, "Segoe UI", Arial, sans-serif; font-size: 10.3pt;
       line-height: 1.40; color: #1f2937; }
h1 { font-size: 21pt; color: #0f2b5b; margin: 0 0 14pt 0; line-height: 1.2; }
h2 { font-size: 13.5pt; color: #0f2b5b; margin: 17pt 0 7pt 0;
     border-bottom: 0.75pt solid #93c5fd; padding-bottom: 3pt; page-break-after: avoid; }
h3 { font-size: 11pt; color: #1e3a8a; margin: 11pt 0 4pt 0; page-break-after: avoid; }
p { margin: 6pt 0; text-align: justify; }
strong { color: #111827; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 10pt 0;
        font-size: 8.4pt; page-break-inside: avoid; }
th, td { border: 0.5pt solid #cbd5e1; padding: 3.5pt 4.5pt; vertical-align: top; }
th { background: #eaf1fb; font-weight: 600; color: #0f2b5b; }
tr { page-break-inside: avoid; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background: #f1f5f9; padding: 0 2pt; }
pre { font-family: Consolas, "Courier New", monospace; font-size: 8.7pt;
      background: #f6f8fb; border: 0.5pt solid #d7dee9; padding: 8pt 10pt;
      white-space: pre-wrap; margin: 8pt 0; page-break-inside: avoid; }
blockquote { border-left: 3pt solid #2563eb; background: #f3f7fd;
             margin: 9pt 0; padding: 7pt 11pt; }
blockquote p { margin: 2pt 0; }
ul, ol { margin: 6pt 0 8pt 0; padding-left: 20pt; }
li { margin: 2.5pt 0; }
hr { border: 0; border-top: 0.75pt solid #dbe3ee; margin: 14pt 0; }
.cover { page-break-after: always; text-align: center; padding-top: 45mm; }
.cover h1 { font-size: 25pt; }
.cover p { text-align: center; }
.cover blockquote { text-align: left; margin-top: 22mm; }
.footer { font-size: 8pt; color: #6b7280; text-align: center; margin-top: 14pt; }
"""


def inline(text: str) -> str:
    """Bold, inline code and italics. Code spans are protected before emphasis."""
    esc = html.escape(text, quote=False)
    protected = []

    def stash(match):
        protected.append(match.group(0))
        return f"\x00{len(protected) - 1}\x00"

    esc = re.sub(r"`(.+?)`", stash, esc)
    esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
    esc = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", esc)
    for idx, original in enumerate(protected):
        esc = esc.replace(f"\x00{idx}\x00", f"<code>{original[1:-1]}</code>")
    return esc


def is_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{2,}", line)) and "|" in line


def table_html(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) < 2:
        return ""
    head = rows[0]
    body = rows[2:] if is_separator(lines[1]) else rows[1:]
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out += [f"<td>{inline(c)}</td>" for c in row]
        out.append("</tr>")
    out += ["</tbody></table>"]
    return "\n".join(out)


def convert(md: str) -> str:
    lines = md.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append("<pre>" + html.escape("\n".join(buf)) + "</pre>")
            continue
        if stripped == "---":
            blocks.append("<hr>")
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            blocks.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if stripped.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append("<blockquote><p>" + inline(" ".join(buf)) + "</p></blockquote>")
            continue
        if stripped.startswith("|"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            blocks.append(table_html(buf))
            continue
        if re.match(r"^-\s+", stripped):
            buf = []
            while i < len(lines) and re.match(r"^-\s+", lines[i].strip()):
                buf.append(re.sub(r"^-\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", stripped):
            buf = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ol>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,3}\s|>\s|\||```|---$|-\s|\d+\.\s)", lines[i].strip()
        ):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            blocks.append("<p>" + inline(" ".join(buf)) + "</p>")
        else:
            i += 1

    # Everything before the first horizontal rule becomes the cover page.
    if "<hr>" in blocks:
        cut = blocks.index("<hr>")
        cover = "\n".join(blocks[:cut])
        rest = "\n".join(blocks[cut + 1:])
        body = f'<div class="cover">\n{cover}\n<p class="footer">HKUST IEDA &middot; Finance with AI Agents &middot; Final Project &middot; 10 November 2026</p>\n</div>\n{rest}'
    else:
        body = "\n".join(blocks)
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Loan Offer Compass - Final Project Report</title>\n"
        f"<style>\n{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def main() -> int:
    if not SRC.is_file():
        print(f"INPUT ERROR: missing {SRC}", file=__import__("sys").stderr)
        return 2
    DST.write_text(convert(SRC.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Wrote {DST} ({DST.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
