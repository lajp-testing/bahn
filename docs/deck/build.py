"""Builds the deck: docs/deck/slides.md -> docs/deck/deck.html (one self-contained file), and with --pdf deck.pdf.

    python3 docs/deck/build.py                                              # HTML only
    nix shell nixpkgs#chromium --command python3 docs/deck/build.py --pdf   # HTML and PDF

The Markdown is a small subset, enough for slides:
  ---                      a new slide (a line with three dashes only)
  <!-- slide: name -->     a CSS class for this slide (e.g. title)
  # Claim                  the slide's title; ## and ### smaller headings
  ::: name args            opens a block <div class="name args">, closed by ':::'; blocks nest
  +++                      inside a block: the next column
  ![alt](file.svg)         an SVG, inlined so the HTML stays one file
  - item / 1. item         lists;  | a | b |  tables;  **bold**, *italic*, `code`
  <html ...>               a line starting with '<' passes through unchanged
Standard library only.
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def svg(path: str) -> str:
    text = (HERE / path).read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*>", "", text)
    # Let CSS size it: keep the viewBox, drop fixed width/height on the root element.
    return re.sub(r"<svg([^>]*?) width=\"[\d.]+\" height=\"[\d.]+\"", r"<svg\1", text, count=1)


def table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    align = []
    if len(cells) > 1 and all(re.fullmatch(r":?-+:?", c) for c in cells[1]):
        align = ["right" if c.endswith(":") and not c.startswith(":") else "center" if c.startswith(":") and c.endswith(":") else "left" for c in cells[1]]
    st = lambda i: f' style="text-align:{align[i]}"' if i < len(align) else ""
    out = ["<table><thead><tr>" + "".join(f"<th{st(i)}>{inline(c)}</th>" for i, c in enumerate(head)) + "</tr></thead><tbody>"]
    for r in body:
        out.append("<tr>" + "".join(f"<td{st(i)}>{inline(c)}</td>" for i, c in enumerate(r)) + "</tr>")
    return "\n".join(out) + "</tbody></table>"


def blocks(lines: list[str]) -> str:
    out: list[str] = []
    stack: list[str] = []
    para: list[str] = []
    lst: tuple[str, list[str]] | None = None
    tbl: list[str] = []

    def flush():
        nonlocal para, lst, tbl
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None
        if tbl:
            out.append(table(tbl))
            tbl = []

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if s.startswith(":::"):
            flush()
            name = s[3:].strip()
            if name:
                stack.append(name)
                cls = html.escape(name)
                out.append(f'<div class="{cls}"><div class="col">' if name.split()[0] == "cols" else f'<div class="{cls}">')
            elif stack:
                top = stack.pop()
                out.append("</div></div>" if top.split()[0] == "cols" else "</div>")
            continue
        if s == "+++":
            flush()
            out.append('</div><div class="col">')
            continue
        if not s:
            flush()
            continue
        if s.startswith("<"):
            flush()
            out.append(s)
            continue
        m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            flush()
            out.append(f'<figure role="img" aria-label="{html.escape(m.group(1))}">{svg(m.group(2))}</figure>')
            continue
        m = re.match(r"(#{1,3})\s+(.*)", s)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            continue
        if s.startswith("|"):
            if para or lst:
                flush()
            tbl.append(s)
            continue
        m = re.match(r"(?:[-*]|(\d+)\.)\s+(.*)", s)
        if m:
            tag = "ol" if m.group(1) else "ul"
            if para or tbl or (lst and lst[0] != tag):
                flush()
            if not lst:
                lst = (tag, [])
            lst[1].append(m.group(2))
            continue
        if lst and raw.startswith("  "):  # a list item continued on the next line
            lst[1][-1] += " " + s
            continue
        if lst or tbl:
            flush()
        para.append(s)
    flush()
    out.extend("</div></div>" if t.split()[0] == "cols" else "</div>" for t in reversed(stack))
    return "\n".join(out)


def build() -> Path:
    src = (HERE / "slides.md").read_text(encoding="utf-8")
    title = re.search(r"^title:\s*(.+)$", src, flags=re.M)
    src_body = re.sub(r"^title:.*$", "", src, count=1, flags=re.M)
    parts = re.split(r"^---\s*$", src_body, flags=re.M)
    slides = []
    for i, part in enumerate(p for p in parts if p.strip()):
        cls = ""
        m = re.search(r"<!--\s*slide:\s*([\w -]+?)\s*-->", part)
        if m:
            cls = m.group(1)
        part = re.sub(r"<!--.*?-->", "", part, flags=re.S)
        slides.append((cls, blocks(part.splitlines())))
    n = len(slides)
    body = "\n".join(
        f'<section class="slide {c}" id="s{i + 1}"><div class="inner">{b}</div><div class="num">{i + 1} / {n}</div></section>'
        for i, (c, b) in enumerate(slides))
    page = TEMPLATE.replace("{{TITLE}}", html.escape(title.group(1) if title else "Deck")).replace("{{CSS}}", (HERE / "deck.css").read_text()).replace("{{BODY}}", body)
    out = HERE / "deck.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out}: {n} slides")
    return out


def pdf(html_path: Path) -> None:
    exe = next((shutil.which(x) for x in ("chromium", "chromium-browser", "google-chrome") if shutil.which(x)), None)
    if not exe:
        sys.exit("No chromium on PATH: run inside `nix shell nixpkgs#chromium --command ...`")
    out = HERE / "deck.pdf"
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000",
                    f"--print-to-pdf={out}", html_path.as_uri() + "?print"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{out}")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>{{CSS}}</style></head>
<body>
<main id="deck">
{{BODY}}
</main>
<script>
(function () {
  const slides = [...document.querySelectorAll('.slide')];
  const printing = location.search.includes('print');
  if (printing) { document.body.classList.add('print'); return; }
  let i = Math.max(0, Math.min(slides.length - 1, (parseInt(location.hash.slice(2)) || 1) - 1));
  function fit() {
    const k = Math.min(innerWidth / 1280, innerHeight / 720);
    document.documentElement.style.setProperty('--k', k);
  }
  function show(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, j) => s.classList.toggle('on', j === i));
    history.replaceState(null, '', '#s' + (i + 1));
  }
  addEventListener('resize', fit);
  addEventListener('keydown', e => {
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) { show(i + 1); e.preventDefault(); }
    if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) { show(i - 1); e.preventDefault(); }
    if (e.key === 'Home') show(0);
    if (e.key === 'End') show(slides.length - 1);
    if (e.key === 'f') document.documentElement.requestFullscreen?.();
  });
  addEventListener('click', e => { if (!e.target.closest('a')) show(i + (e.clientX > innerWidth / 3 ? 1 : -1)); });
  addEventListener('beforeprint', () => document.body.classList.add('print'));
  addEventListener('afterprint', () => document.body.classList.remove('print'));
  fit(); show(i);
})();
</script>
</body></html>
"""

if __name__ == "__main__":
    path = build()
    if "--pdf" in sys.argv:
        pdf(path)
