#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy lint: mechanical checks from STYLE.md on AsciiDoc pages.

    python3 gypsy/lint.py [--json] [--manifest images/manifest.yml] PAGE.adoc [PAGE.adoc ...]

Exit 1 when any error is found. Checks:
  vocab      ADR-000 avoid-list word in prose (gypsy/vocabulary.yml)
  style      word banned by STYLE.md §2
  since      [.since] marker not in the form `[.since]#introduced in 26.3#`
  admonition imitation admonition (*_Note_*:, *NOTE*:, Note: paragraph) or TIP:/IMPORTANT:
  heading    level-2 heading outside the command-page skeleton, or out of order
  image      block image without alt text, with a width= attribute, or missing a manifest entry
  sentence   sentence over 30 words
  xref       bare <<...>> cross-page reference or a link to the published site
"""
import argparse, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKELETON = ["Description", "Usage", "Options", "Properties", "Strategies",
            "Notes and limitations", "Scripting", "Related"]
SINCE_OK = re.compile(r"\[\.since\]#introduced in \d+(?:\.\d+)?#")
SINCE_ANY = re.compile(r"\[\.since\]#[^#]*#")
IMITATION = re.compile(r"^(\*_?Note_?\*:?|\*NOTE\*:?|Note:|NOTE\s*[-–:]|\*Important Note)", re.I)
BLOCK_IMG = re.compile(r"^image::([^\[]+)\[([^\]]*)\]")
MAX_WORDS = 30

# Spans that are UI or code, exempt from vocabulary checks.
EXEMPT = [
    re.compile(r"(?:menu|btn|kbd):[^\[]*\[[^\]]*\]"),
    re.compile(r"image::?[^\[]*\[[^\]]*\]"),
    re.compile(r"xref:[^\[]*\[[^\]]*\]"),
    re.compile(r"(?:link:|https?://)\S+(?:\[[^\]]*\])?"),
    re.compile(r"`[^`]*`"),
    re.compile(r"\*[^*\n]+\*"),      # bold: property / control labels
    re.compile(r"_[^_\n]+_"),        # italic: dialog / tab names
    re.compile(r"\[\.since\]#[^#]*#"),
    re.compile(r"<<[^>]*>>"),
]


def load_vocab():
    with open(os.path.join(HERE, "vocabulary.yml"), encoding="utf-8") as fh:
        v = yaml.safe_load(fh)
    terms = []
    for t in v["terms"]:
        for pat in t.get("avoid", []):
            terms.append((t["term"], re.compile(pat, re.I)))
    style = [re.compile(p, re.I) for p in v.get("style_avoid", [])]
    ok = [re.compile(p, re.I) for p in v.get("prose_ok", [])]
    return terms, style, ok


def strip_exempt(line):
    for rx in EXEMPT:
        line = rx.sub(lambda m: " " * len(m.group(0)), line)
    return line


def lint_file(path, terms, style, ok, manifest):
    out = []
    err = lambda line, kind, msg: out.append({"file": path, "line": line, "kind": kind, "msg": msg})
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    in_code = False
    in_header = True
    is_command = any(l.startswith(":page-command:") for l in lines[:40])
    headings = []
    prose_buf = []  # (lineno, text) for sentence check
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.startswith("----") or line.startswith("...."):
            in_code = not in_code
            continue
        if in_code or line.startswith("//"):
            continue
        if in_header:
            if i > 1 and line == "":
                in_header = False
            elif line.startswith(":") or line.startswith("="):
                continue
        if line.startswith("== "):
            headings.append((i, line[3:].strip()))
            continue
        if line.startswith(("=", "[", ".", "|", "+", "--")):
            continue
        # since markers
        for m in SINCE_ANY.finditer(line):
            if not SINCE_OK.fullmatch(m.group(0)):
                err(i, "since", f"marker must be `[.since]#introduced in X.Y#`: {m.group(0)}")
        # admonitions
        if IMITATION.match(line):
            err(i, "admonition", "imitation admonition; use NOTE:/WARNING:/CAUTION:")
        if re.match(r"^(TIP|IMPORTANT):", line):
            err(i, "admonition", "TIP:/IMPORTANT: are not used; NOTE:/WARNING:/CAUTION: only")
        # block images
        m = BLOCK_IMG.match(line)
        if m:
            target, attrs = m.group(1), m.group(2)
            first = attrs.split(",")[0].strip()
            if not first or "=" in first:
                err(i, "image", f"block image without alt text: {target}")
            if "width=" in attrs:
                err(i, "image", f"use positional width, not width=: {target}")
            if manifest is not None and target not in manifest:
                err(i, "image", f"no images/manifest.yml entry: {target}")
            continue
        # xrefs
        if re.search(r"<<[^>,]*\.adoc[^>]*>>", line):
            err(i, "xref", "cross-page <<...>> reference; use xref:")
        if "sliptonic.github.io" in line:
            err(i, "xref", "link to the published site; use xref:")
        # vocabulary on prose only
        prose = strip_exempt(line)
        if re.match(r"^(NOTE|WARNING|CAUTION):", prose):
            prose = prose.split(":", 1)[1]
        for term, rx in terms:
            for m in rx.finditer(prose):
                ctx = prose[max(0, m.start() - 20):m.end() + 20]
                if any(o.search(ctx) for o in ok):
                    continue
                err(i, "vocab", f"'{m.group(0)}' -> {term}")
        for rx in style:
            for m in rx.finditer(prose):
                err(i, "style", f"'{m.group(0)}' banned by STYLE.md §2")
        prose_buf.append((i, re.sub(r"\s+", " ", strip_exempt(line)).strip()))
    # sentences
    for lineno, text in prose_buf:
        text = re.sub(r"^[*.]+\s*", "", text)
        for s in re.split(r"(?<=[.!?])\s+", text):
            n = len(s.split())
            if n > MAX_WORDS:
                err(lineno, "sentence", f"{n} words: {s[:60]}…")
    # headings
    if is_command:
        order = [h for _, h in headings]
        for ln, h in headings:
            if h not in SKELETON:
                err(ln, "heading", f"'{h}' is not a command-page skeleton heading")
        idx = [SKELETON.index(h) for h in order if h in SKELETON]
        if idx != sorted(idx):
            err(headings[0][0], "heading", f"skeleton headings out of order: {order}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--manifest", default=os.path.join(ROOT, "modules/ROOT/images/manifest.yml"))
    a = ap.parse_args()
    terms, style, ok = load_vocab()
    manifest = None
    if os.path.exists(a.manifest):
        with open(a.manifest, encoding="utf-8") as fh:
            manifest = {e["file"] for e in (yaml.safe_load(fh) or {}).get("figures", [])}
    findings = []
    for p in a.pages:
        findings += lint_file(p, terms, style, ok, manifest)
    if a.json:
        print(json.dumps(findings, indent=1))
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']}: {f['kind']}: {f['msg']}")
        by = {}
        for f in findings:
            by[f["kind"]] = by.get(f["kind"], 0) + 1
        print(f"-- {len(findings)} findings " + " ".join(f"{k}={v}" for k, v in sorted(by.items())), file=sys.stderr)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
