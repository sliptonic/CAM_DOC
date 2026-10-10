#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate the Post-Processor genealogy page from the FreeCAD source tree.

    python3 tools/post_genealogy.py [--source ~/FreeCAD-gypsy] [--out modules/ROOT/pages/output/posts/genealogy.adoc]

Reads the classes of src/Mod/CAM/Path/Post/Processor.py and Path/Post/scripts/*.py with the
Python parser (nothing is imported or run) and writes which Post-Processor class inherits from
which, as a Mermaid graph and a table. The page is generated; to change it, change the source.
"""
import argparse
import ast
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST = "src/Mod/CAM/Path/Post"
BASE = "PostProcessor"


def classes_of(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else b.attr for b in node.bases
                     if isinstance(b, (ast.Name, ast.Attribute))]
            out.append((node.name, bases, (ast.get_docstring(node) or "").strip().split("\n")[0]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.path.expanduser(os.environ.get("GYPSY_FREECAD_TREE", "~/FreeCAD-gypsy")))
    ap.add_argument("--out", default=os.path.join(ROOT, "modules/ROOT/pages/output/posts/genealogy.adoc"))
    a = ap.parse_args()
    post = os.path.join(a.source, POST)
    if not os.path.isdir(post):
        sys.exit(f"post_genealogy: no {POST} in {a.source}")
    files = [os.path.join(post, "Processor.py")] + sorted(glob.glob(os.path.join(post, "scripts", "*.py")))
    found = {}                                    # class -> (parent, file, docstring)
    scripts_without_class = []
    for path in files:
        rel = os.path.relpath(path, a.source)
        mine = classes_of(path)
        for name, bases, doc in mine:
            if bases:
                found[name] = (bases[0], rel, doc)
        if path.endswith("_post.py") and not any(b for _, b, _ in mine):
            scripts_without_class.append(os.path.basename(path))

    def descends(name, seen=()):
        if name == BASE:
            return True
        parent = found.get(name, (None,))[0]
        return parent is not None and name not in seen and descends(parent, seen + (name,))

    family = {n: v for n, v in found.items() if descends(n)}
    # A script whose class does not descend from the base is a script post too.
    for path in files:
        base = os.path.basename(path)
        if base.endswith("_post.py") and base not in scripts_without_class \
                and not any(v[1].endswith(base) for v in family.values()):
            scripts_without_class.append(base)
    commit = subprocess.run(["git", "-C", a.source, "log", "-1", "--format=%h %cs"],
                            capture_output=True, text=True).stdout.strip()

    def depth(name):
        return 0 if name == BASE else 1 + depth(family[name][0])

    order = sorted(family, key=lambda n: (depth(n), family[n][0], n.lower()))
    out = ["= Post-Processor Genealogy", ":page-status: generated",
           f":page-source: {POST} ({commit})",
           ":description: Which machine-based Post-Processor class inherits from which, generated from the FreeCAD source tree.",
           "",
           f"Generated from `{POST}` in the FreeCAD source tree. To change this page, change the source.",
           "",
           f"A machine-based xref:reference/glossary.adoc#post-processor[Post-Processor] is a Python class that "
           f"inherits from `{BASE}` in `Path/Post/Processor.py`, directly or through a different Post-Processor. "
           "A class gets the behaviour of its parent and replaces the parts that its control needs. "
           "xref:output/mbpp-postprocessor.adoc[Writing a Machine-Based Post-Processor] describes how to write one.",
           "", "== Inheritance", "", "[.mermaid]", "....", "flowchart LR", f"  {BASE}"]
    out += [f"  {family[n][0]} --> {n}" for n in order]
    out += ["....", "", "== Classes", "",
            '[cols="2,2,2,3",options="header"]', "|===", "| Class | Inherits from | Post-Processor name | Source file", ""]
    for n in order:
        parent, rel, _ = family[n]
        base = os.path.basename(rel)
        name = f"`{base[:-len('_post.py')]}`" if base.endswith("_post.py") else "_none_"
        out += [f"| `{n}` | `{parent}` | {name} | `{rel}`"]
    out += ["|===", "",
            "The Post-Processor name is the file name without `_post.py`. It is the name in the *Post-Processor* "
            "list of a Machine.", ""]
    if scripts_without_class:
        legacy = sorted(scripts_without_class, key=str.lower)
        out += ["== Script posts", "",
                f"These {len(legacy)} files are script posts. They have no class in this tree. `WrapperPost` loads a "
                "script post and runs it, thus a script post inherits nothing from a different post.", ""]
        out += [f"* `{f}`" for f in legacy] + [""]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"{os.path.relpath(a.out, ROOT)}: {len(family)} classes, {len(scripts_without_class)} script posts, source {commit}")


if __name__ == "__main__":
    main()
