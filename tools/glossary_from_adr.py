#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate modules/ROOT/pages/reference/glossary.adoc from FreeCAD's ADR-000 (ubiquitous language).

    python3 tools/glossary_from_adr.py [--adr ~/FreeCAD/src/Mod/CAM/Roadmap/ADR/ADR-000.md]

Every term gets an anchor from its name: "Tool Controller" -> tool-controller, so pages link
with xref:reference/glossary.adoc#tool-controller[Tool Controller]. The page is generated; edit
ADR-000 upstream, not the page.
"""
import argparse, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "modules/ROOT/pages/reference/glossary.adoc")
TERM = re.compile(r"^\*\*(.+?)\*\*(.*?):\s*$")


def slug(term):
    term = re.sub(r"\s*\(.*?\)\s*", " ", term)      # "Feed (umbrella)" -> "Feed"
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"*\1*", s)
    s = re.sub(r"(?<![A-Za-z])_(Avoid|Note)_:", r"*\1:*", s)
    s = re.sub(r"(?<![A-Za-z*_`])_([^_`]+?)_(?![A-Za-z])", r"_\1_", s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adr", default=os.path.expanduser("~/FreeCAD/src/Mod/CAM/Roadmap/ADR/ADR-000.md"))
    a = ap.parse_args()
    src = open(a.adr, encoding="utf-8").read().split("\n")
    try:
        commit = subprocess.run(["git", "-C", os.path.dirname(a.adr), "log", "-1", "--format=%h %cs", "--", a.adr],
                                capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = ""
    out = ["= Glossary", ":page-status: generated", f":page-source: src/Mod/CAM/Roadmap/ADR/ADR-000.md ({commit})",
           ":description: The CAM workbench vocabulary, generated from ADR-000, the ubiquitous-language glossary in the FreeCAD source tree.",
           "", "Generated from `src/Mod/CAM/Roadmap/ADR/ADR-000.md` in the FreeCAD source tree. Terms are used",
           "exactly as written here across this documentation; the _Avoid_ lists name words that are not used.",
           "To change a definition, change ADR-000.", ""]
    in_lang = False
    in_term = False
    for line in src:
        if line.startswith("## Language"):
            in_lang = True
            continue
        if line.startswith("## Example dialogue"):
            break
        if not in_lang:
            continue
        if line.startswith("## "):
            in_term = False
            out += ["", "== " + line[3:].strip(), ""]
            continue
        if line.startswith("### "):
            in_term = False
            out += ["", "== " + line[4:].strip(), ""]
            continue
        m = TERM.match(line)
        if m:
            term, also = m.group(1), m.group(2).strip()
            in_term = True
            out += ["", f"[[{slug(term)}]]", f"=== {term}" + (f" {inline(also)}" if also else ""), ""]
            continue
        if line.startswith("- "):
            out.append("* " + inline(line[2:]))
            continue
        out.append(inline(line))
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip() + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    anchors = re.findall(r"^\[\[(.+?)\]\]$", text, re.M)
    print(f"wrote {OUT}: {len(anchors)} terms; sample anchors: {anchors[:8]}")


if __name__ == "__main__":
    main()
