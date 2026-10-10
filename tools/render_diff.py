#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 sliptonic <shopinthewoods@gmail.com>
"""Rendered diff of two builds of the site.

Compares the article of every page in the head build with the same page in the base build and
writes, into the head build:

    <page>.diff.html   the rendered page with insertions and deletions marked
    changes.html       the list of changed, new and removed pages

A changed page also gets a banner that links to its diff. A figure whose file changed is shown
old and new, side by side, also when its name did not change.

    # two existing builds (CI)
    python3 tools/render_diff.py --base build/base --head build/site --summary build/changes.md

    # build both sides first: the branch `main` against the working tree
    python3 tools/render_diff.py --build --against main

Needs lxml.
"""
import argparse
import difflib
import filecmp
import os
import posixpath
import re
import shutil
import subprocess
import sys

from lxml import html as LH
from lxml.html.diff import htmldiff

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARTICLE = '//article[contains(concat(" ", normalize-space(@class), " "), " doc ")]'
BLOCKS = {"p", "li", "tr", "pre", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "figure", "caption"}
OLD_IMAGES = "_diff/old"

CSS = """
.diff-banner{position:sticky;top:var(--navbar-height,3.5rem);z-index:5;display:flex;flex-wrap:wrap;
  gap:.4rem 1rem;align-items:center;margin:0 0 1rem;padding:.5rem .75rem;border:1px solid #c9c9c9;
  border-radius:4px;background:#fffbe6;color:#222;font-size:.85rem;line-height:1.4}
.diff-banner a{font-weight:600}
.diff-banner button{font:inherit;padding:.1rem .5rem;cursor:pointer}
.diff-banner .diff-key ins,.diff-banner .diff-key del{padding:0 .3rem}
.doc ins{background:#d1f5d3;color:#0b3d12;text-decoration:none}
.doc del{background:#ffd8d6;color:#6b1210;text-decoration:line-through}
.doc ins img,.doc img.diff-img-new{outline:3px solid #2da44e;outline-offset:2px}
.doc del img,.doc img.diff-img-old{outline:3px solid #cf222e;outline-offset:2px;opacity:.75}
.doc .diff-img-pair{display:flex;flex-wrap:wrap;gap:1rem;align-items:flex-start}
.doc .diff-img-pair>span{display:flex;flex-direction:column;font-size:.8rem;color:#555}
.doc .diff-block-add{background:#e6f9e7;outline:1px solid #2da44e}
.doc .diff-block-del{background:#ffecea;outline:1px solid #cf222e;opacity:.8;text-decoration:line-through}
.doc .diff-block-del img{opacity:.6}
.doc .diff-changed{box-shadow:-.6rem 0 0 -.35rem #d4a72c}
.doc .diff-current{box-shadow:-.6rem 0 0 -.35rem #0969da}
.doc.diff-new-page{box-shadow:-.9rem 0 0 -.6rem #2da44e}
"""

JS = """
(function () {
  var marks = Array.prototype.slice.call(document.querySelectorAll('.diff-changed'));
  var at = -1;
  function go(step) {
    if (!marks.length) return;
    if (at >= 0) marks[at].classList.remove('diff-current');
    at = (at + step + marks.length) % marks.length;
    marks[at].classList.add('diff-current');
    marks[at].scrollIntoView({block: 'center'});
    var n = document.getElementById('diff-pos');
    if (n) n.textContent = (at + 1) + ' / ' + marks.length;
  }
  document.addEventListener('click', function (e) {
    if (e.target.id === 'diff-next') go(1);
    if (e.target.id === 'diff-prev') go(-1);
  });
  document.addEventListener('keydown', function (e) {
    if (/INPUT|TEXTAREA/.test(e.target.tagName)) return;
    if (e.key === 'n') go(1);
    if (e.key === 'p') go(-1);
  });
})();
"""


def pages(root):
    """Relative paths of the content pages of a build."""
    found = set()
    for folder, dirs, files in os.walk(root):
        rel = os.path.relpath(folder, root)
        if rel == "_" or rel.startswith(("_" + os.sep, "_diff", "pr-")):
            dirs[:] = []
            continue
        for name in files:
            if name.endswith(".html") and not name.endswith(".diff.html") \
                    and name not in ("404.html", "changes.html"):
                found.add(os.path.normpath(os.path.join(rel, name)))
    return found


def load(path):
    doc = LH.parse(path).getroot()
    found = doc.xpath(ARTICLE)
    return doc, (found[0] if found else None)


def inner(el):
    return (el.text or "") + "".join(LH.tostring(c, encoding="unicode") for c in el)


def normal(text):
    return re.sub(r"\s+", " ", text).strip()


def words(el, tag):
    return sum(len((n.text_content() or "").split()) for n in el.iter(tag))


def title_of(article, fallback):
    h1 = article.find(".//h1") if article is not None else None
    return normal(h1.text_content()) if h1 is not None else fallback


def rel_link(from_page, to_path):
    return posixpath.relpath(to_path.replace(os.sep, "/"),
                             posixpath.dirname(from_page.replace(os.sep, "/")) or ".")


FLATTEN = {"sect1", "sect2", "sect3", "sect4", "sectionbody"}
PAIR_RATIO = 0.45        # two blocks at least this similar are shown as one block with marks


def blocks_of(el):
    """The article as a flat list of blocks. Section wrappers are opened; a paragraph, a list,
    a table, a listing, a figure or a heading is one block."""
    out = []
    for child in el:
        if not isinstance(child.tag, str):
            continue
        classes = set(child.get("class", "").split())
        if child.tag == "div" and (classes & FLATTEN or child.get("id") == "preamble"):
            out.extend(blocks_of(child))
        else:
            child.tail = None
            out.append(child)
    return out


def key_of(block):
    """What makes two blocks equal: the tag, the text, and the figures."""
    images = " ".join(i.get("src", "") for i in block.iter("img"))
    return block.tag + "|" + normal(block.text_content()) + "|" + images


def ratio(a, b):
    wa, wb = a.text_content().split(), b.text_content().split()
    if not wa and not wb:
        return 1.0 if key_of(a) == key_of(b) else 0.0
    m = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    return m.ratio() if m.quick_ratio() >= PAIR_RATIO else 0.0


def whole(block, cls):
    block.set("class", (block.get("class", "") + " diff-changed " + cls).strip())
    return block


def word_diff(old, new):
    """One block with word-level marks. Link targets are hidden from the comparison, because
    lxml prints a changed target as text."""
    for el in list(old.iter("a")) + list(new.iter("a")):
        if el.get("href") is not None:
            el.set("data-diff-href", el.attrib.pop("href"))
    merged = LH.fragment_fromstring(
        htmldiff(LH.tostring(old, encoding="unicode"), LH.tostring(new, encoding="unicode")),
        create_parent="div")
    for el in merged.iter("a"):
        if el.get("data-diff-href") is not None:
            el.set("href", el.attrib.pop("data-diff-href"))
    return list(merged)


def pair_up(old, new):
    """Blocks of one replaced range, in order: (old, new), (old, None) or (None, new)."""
    out, i, j = [], 0, 0
    while i < len(old) and j < len(new):
        if old[i].tag == new[j].tag and ratio(old[i], new[j]) >= PAIR_RATIO:
            out.append((old[i], new[j]))
            i, j = i + 1, j + 1
        elif any(old[i].tag == n.tag and ratio(old[i], n) >= PAIR_RATIO for n in new[j + 1:j + 6]):
            out.append((None, new[j]))
            j += 1
        else:
            out.append((old[i], None))
            i += 1
    out += [(o, None) for o in old[i:]] + [(None, n) for n in new[j:]]
    return out


def block_diff(old_article, new_article):
    """The new article as a flat list of blocks, with removed blocks put back in place."""
    old, new = blocks_of(old_article), blocks_of(new_article)
    matcher = difflib.SequenceMatcher(None, [key_of(b) for b in old], [key_of(b) for b in new],
                                      autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            out.extend(new[j1:j2])
            continue
        for o, n in pair_up(old[i1:i2], new[j1:j2]):
            if o is None:
                out.append(whole(n, "diff-block-add"))
            elif n is None:
                out.append(whole(o, "diff-block-del"))
            elif key_of(o) == key_of(n):
                out.append(n)
            else:
                out.extend(word_diff(o, n))
    body = LH.Element("div")
    body.extend(out)
    return body


def mark_blocks(article):
    """Give every block that holds a change a marker, so the reader can step through them."""
    for node in article.iter("ins", "del"):
        block, inside_whole = node, False
        while block is not None and block is not article and block.tag not in BLOCKS:
            block = block.getparent()
        if block is None or block is article:
            block = node
        up = block
        while up is not None and up is not article:
            if "diff-changed" in up.get("class", "").split():
                inside_whole = True
                break
            up = up.getparent()
        if not inside_whole:
            block.set("class", (block.get("class", "") + " diff-changed").strip())
    return sum(1 for el in article.iter() if isinstance(el.tag, str)
               and "diff-changed" in el.get("class", "").split())


def mark_images(article, page, base_root, head_root):
    """Show a figure whose file changed although its name did not."""
    changed = 0
    page_dir = os.path.dirname(page)
    for img in list(article.iter("img")):
        src = img.get("src", "")
        if not src or re.match(r"^(?:[a-z]+:)?//|^data:", src):
            continue
        inside = img.getparent()
        while inside is not None and inside.tag not in ("ins", "del"):
            inside = inside.getparent()
        if inside is not None:                      # htmldiff marked it already
            continue
        rel = os.path.normpath(os.path.join(page_dir, src.split("?")[0].split("#")[0]))
        old, new = os.path.join(base_root, rel), os.path.join(head_root, rel)
        if not os.path.exists(new) or not os.path.exists(old) or filecmp.cmp(old, new, shallow=False):
            continue
        keep = os.path.join(head_root, OLD_IMAGES, rel)
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.copy(old, keep)
        pair = LH.Element("span", {"class": "diff-img-pair diff-changed"})
        before = LH.Element("span")
        before.text = "Before"
        old_img = LH.Element("img", {"src": rel_link(page, os.path.join(OLD_IMAGES, rel)),
                                     "class": "diff-img-old", "alt": "Before: " + img.get("alt", "")})
        for key in ("width", "height"):
            if img.get(key):
                old_img.set(key, img.get(key))
        before.append(old_img)
        after = LH.Element("span")
        after.text = "After"
        parent, tail = img.getparent(), img.tail
        img.tail = None
        parent.replace(img, pair)
        img.set("class", (img.get("class", "") + " diff-img-new").strip())
        after.append(img)
        pair.append(before)
        pair.append(after)
        pair.tail = tail
        changed += 1
    return changed


def banner(text_html, links):
    el = LH.fragment_fromstring(
        '<div class="diff-banner"><span>' + text_html + "</span>" +
        "".join(f'<a href="{href}">{label}</a>' for label, href in links) + "</div>")
    return el


def add_head(doc, with_js):
    head = doc.find("head")
    style = LH.Element("style")
    style.text = CSS
    head.append(style)
    if with_js:
        script = LH.Element("script")
        script.text = JS
        doc.find("body").append(script)


def write(doc, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(LH.tostring(doc, encoding="unicode", doctype="<!DOCTYPE html>"))


def diff_page(page, base_root, head_root, labels):
    """Returns None when the page did not change, else a dict for the index."""
    head_path = os.path.join(head_root, page)
    base_path = os.path.join(base_root, page)
    doc, article = load(head_path)
    if article is None:
        return None
    new_html = inner(article)
    is_new = not os.path.exists(base_path)
    old_article = None if is_new else load(base_path)[1]
    old_html = "" if old_article is None else inner(old_article)
    diff_name = page[:-len(".html")] + ".diff.html"
    title = title_of(article, page)

    if is_new:
        body = LH.fragment_fromstring(new_html, create_parent="div")
        added, removed, blocks, figures = len(body.text_content().split()), 0, 0, 0
        article.set("class", article.get("class", "") + " diff-new-page")
    else:
        text_changed = normal(old_html) != normal(new_html)
        if text_changed:
            body = block_diff(old_article, load(head_path)[1])
        else:
            body = LH.fragment_fromstring(new_html, create_parent="div")
        figures = mark_images(body, page, base_root, head_root)
        if not text_changed and not figures:
            return None
        added = words(body, "ins") + sum(len(b.text_content().split()) for b in body.find_class("diff-block-add"))
        removed = words(body, "del") + sum(len(b.text_content().split()) for b in body.find_class("diff-block-del"))
        blocks = mark_blocks(body)

    # the diff page
    for child in list(article):
        article.remove(child)
    article.text = body.text
    for child in list(body):
        article.append(child)
    here = os.path.basename(page)
    if is_new:
        text = f"<strong>New page</strong> in {labels['head']}; it is not in {labels['base']}."
        controls = ""
    else:
        text = (f"<strong>Rendered diff</strong>: {labels['head']} against {labels['base']}. "
                f'<span class="diff-key"><ins>added</ins> <del>removed</del></span>')
        controls = ('<button id="diff-prev" title="key: p">◀ Previous</button> '
                    '<button id="diff-next" title="key: n">Next change ▶</button> '
                    f'<span id="diff-pos">{blocks} changed blocks</span>')
    article.insert(0, banner(text + " " + controls, [
        ("Page without marks", here), ("All changed pages", rel_link(page, "changes.html"))]))
    add_head(doc, with_js=not is_new)
    write(doc, os.path.join(head_root, diff_name))

    # the clean page: a pointer to the diff
    doc, article = load(head_path)
    what = "is new" if is_new else "changes"
    article.insert(0, banner(f"This page {what} in {labels['head']}.", [
        ("Show the changes", os.path.basename(diff_name)),
        ("All changed pages", rel_link(page, "changes.html"))]))
    add_head(doc, with_js=False)
    write(doc, head_path)

    return {"page": page, "diff": diff_name, "title": title, "new": is_new,
            "added": added, "removed": removed, "figures": figures}


def index_html(changed, removed, labels):
    rows = []
    for c in changed:
        note = "new page" if c["new"] else f'+{c["added"]} / −{c["removed"]} words'
        if c["figures"]:
            note += f', {c["figures"]} figure(s) changed'
        rows.append(f'<tr><td><a href="{c["diff"]}">{c["title"]}</a></td><td>{note}</td>'
                    f'<td><a href="{c["page"]}">without marks</a></td><td><code>{c["page"]}</code></td></tr>')
    gone = "".join(f"<li><code>{p}</code></li>" for p in removed)
    body = ("<table><thead><tr><th>Page</th><th>Change</th><th></th><th>Path</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>") if rows else "<p>No page changed.</p>"
    if gone:
        body += f"<h2>Removed pages</h2><ul>{gone}</ul>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Changed pages</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#222}}
table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:.35rem .6rem;border-bottom:1px solid #ddd}}
code{{font-size:.85em;color:#555}}</style></head><body>
<h1>Changed pages</h1>
<p>{labels['head']} against {labels['base']}. {len(changed)} changed or new, {len(removed)} removed.
<a href="index.html">Open the site</a>.</p>
{body}
</body></html>
"""


def summary_md(changed, removed, labels, url):
    url = url.rstrip("/")
    lines = [f"**Rendered changes** against {labels['base']}: {url}/changes.html", ""]
    if not changed and not removed:
        return lines[0].replace(f": {url}/changes.html", ": no page changed.") + "\n"
    lines += ["| Page | Change |", "|---|---|"]
    for c in changed:
        note = "new page" if c["new"] else f'+{c["added"]} / −{c["removed"]} words'
        if c["figures"]:
            note += f', {c["figures"]} figure(s) changed'
        lines.append(f'| [{c["title"]}]({url}/{c["diff"].replace(os.sep, "/")}) | {note} |')
    lines += [f"| `{p}` | removed |" for p in removed]
    return "\n".join(lines) + "\n"


def render(base_root, head_root, labels, url, summary):
    head_pages, base_pages = pages(head_root), pages(base_root)
    # Compare only the versions that both builds hold, plus pages new to such a version.
    versions = {os.sep.join(p.split(os.sep)[:2]) for p in base_pages}
    changed = []
    for page in sorted(head_pages):
        if os.sep.join(page.split(os.sep)[:2]) not in versions:
            continue
        result = diff_page(page, base_root, head_root, labels)
        if result:
            changed.append(result)
    removed = sorted(p.replace(os.sep, "/") for p in base_pages - head_pages)
    with open(os.path.join(head_root, "changes.html"), "w", encoding="utf-8") as fh:
        fh.write(index_html(changed, removed, labels))
    if summary:
        with open(summary, "w", encoding="utf-8") as fh:
            fh.write(summary_md(changed, removed, labels, url))
    for c in changed:
        print(f'{"new    " if c["new"] else "changed"}  {c["diff"]}  +{c["added"]} -{c["removed"]}')
    for p in removed:
        print(f"removed  {p}")
    print(f"{len(changed)} changed or new, {len(removed)} removed; index: {os.path.join(head_root, 'changes.html')}")


def build(against, base_root, head_root):
    """Build the branch `against` and the working tree (HEAD) with Antora."""
    for only_base, out in ((True, base_root), (False, head_root)):
        playbook = os.path.join(ROOT, "antora-playbook-pr.yml")
        cmd = [sys.executable, os.path.join(HERE, "pr_playbook.py"), "--base", against,
               "--url", "http://localhost"] + (["--only-base"] if only_base else [])
        with open(playbook, "w", encoding="utf-8") as fh:
            subprocess.run(cmd, cwd=ROOT, check=True, stdout=fh)
        shutil.rmtree(out, ignore_errors=True)
        subprocess.run(["npx", "antora", "--to-dir", out, playbook], cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=os.path.join(ROOT, "build/base"), help="build of the base branch")
    ap.add_argument("--head", default=os.path.join(ROOT, "build/site"), help="build of the change; written to")
    ap.add_argument("--build", action="store_true", help="build both sides first (needs --against)")
    ap.add_argument("--against", default="main", help="base branch for --build, and its label")
    ap.add_argument("--head-label", default="this change")
    ap.add_argument("--url", default=".", help="site URL of the head build, for the summary links")
    ap.add_argument("--summary", help="write a Markdown summary to this file (for the PR comment)")
    a = ap.parse_args()
    if a.build:
        build(a.against, a.base, a.head)
    labels = {"base": f"<code>{a.against}</code>", "head": a.head_label}
    render(a.base, a.head, labels, a.url, a.summary)
    if a.summary:                                   # the Markdown summary takes no HTML labels
        with open(a.summary, encoding="utf-8") as fh:
            text = fh.read().replace(f"<code>{a.against}</code>", f"`{a.against}`")
        with open(a.summary, "w", encoding="utf-8") as fh:
            fh.write(text)


if __name__ == "__main__":
    sys.exit(main())
