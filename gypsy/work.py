#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy work: issues are the work items, and labels are the decisions.

    python3 gypsy/work.py                       # every open work issue and what it waits for
    python3 gypsy/work.py propose FILE.yml      # open an issue for the work that FILE defines
    python3 gypsy/work.py propose --upstream PR # open an issue for one merged FreeCAD pull request
    python3 gypsy/work.py show N                # the work definition and the guidance of issue N
    python3 gypsy/work.py run [--dry]           # draft the next approved issue; in ~/CAM_DOC-gypsy

A work issue has the label `gypsy`. It is one cause with all its pages; it gives one pull
request, and the merge of that pull request closes it. Its body holds the work definition in a
YAML block that gypsy reads and that a person can edit:

    title    the cause, in a few words
    prs      upstream pull requests delivered in full: every page they change is in the issue
    partial  upstream pull requests with a different cause that also change a rewritten page;
             only that effect is delivered. The value says where the rest goes.
    pages    reference: current pages that the drafter reads and does not change
             generated: pages that a tool writes from the FreeCAD source, {page, command}
             rewrite:   pages rewritten to STYLE.md for all of prs and partial
             new:       pages that do not exist yet
             amend:     pages that get only what prs make false or missing
    nav      lines to add to modules/ROOT/nav.adoc, each {after, line}
    facts    fact files given to the drafter

Labels are the decisions, and only a person sets `approved`:

    proposed   gypsy opened the issue. It waits for a person.
    approved   a person agrees. gypsy drafts it.
    blocked    gypsy cannot continue. Its last comment says why. Remove the label to try again.

The other states need no label. An approved issue without a pull request is in draft. An
issue with an open pull request is in review. A closed issue is delivered, or it is rejected
when it was closed as not planned.

Comments are guidance, not decisions. Each comment of a person on the issue goes to the drafter
of each page. gypsy marks its own comments, and the drafter does not get those.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGES = os.path.join(ROOT, "modules/ROOT/pages")
MARK = "<!-- gypsy -->"                 # first line of a comment that gypsy wrote
BLOCK = re.compile(r"<details>\s*<summary>Work definition[^<]*</summary>\s*```yaml\n(.*?)\n```\s*</details>", re.S)
LABELS = {"gypsy": ("5319e7", "Work that gypsy does"),
          "proposed": ("fbca04", "gypsy proposes this work; it waits for a person"),
          "approved": ("0e8a16", "A person approved this work; gypsy drafts it"),
          "blocked": ("d93f0b", "gypsy cannot continue; its last comment says why"),
          "check-findings": ("d93f0b", "The last check of the runner has findings that a reader must not get")}
DIATAXIS = {"tutorial": "learning: a lesson", "how-to": "a goal: steps", "explanation": "understanding: concepts",
            "reference": "information: exact facts"}
LABELS.update({k: ("1d76db", f"Diátaxis: {v}") for k, v in DIATAXIS.items()})
KINDS = ("rewrite", "new", "amend")
DOES = {"rewrite": "Full rewrite to STYLE.md.", "new": "New page.", "amend": "Small change only.",
        "generated": "Written by a tool from the FreeCAD source.", "reference": "Read, not changed."}


def gh(*args, check=True):
    r = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"gh {' '.join(args[:3])}: {r.stderr.strip()[:300]}")
    return r.stdout


def gh_json(*args):
    return json.loads(gh(*args) or "null")


def branch(number):
    return f"gypsy/issue-{number}"


def ensure_labels():
    have = {l["name"] for l in gh_json("label", "list", "--limit", "200", "--json", "name")}
    for name, (color, text) in LABELS.items():
        if name not in have:
            gh("label", "create", name, "--color", color, "--description", text)


def members(work):
    """The pages that the work changes."""
    pages = work.get("pages") or {}
    return [p for k in KINDS for p in pages.get(k, [])] + [g["page"] for g in pages.get("generated", [])]


def parse(body):
    m = BLOCK.search(body or "")
    if not m:
        return None
    work = yaml.safe_load(m.group(1))
    return work if isinstance(work, dict) and work.get("prs") and work.get("pages") else None


def load(number):
    """The work definition of an issue, with its labels and the guidance of people."""
    i = gh_json("issue", "view", str(number), "--json", "number,title,body,state,labels,comments")
    work = parse(i["body"])
    if work is None:
        sys.exit(f"issue #{number} has no work definition that gypsy can read")
    work["issue"] = number
    work["state"] = i["state"]
    work["labels"] = [l["name"] for l in i["labels"]]
    work["guidance"] = [c["body"].strip() for c in i["comments"] if not c["body"].lstrip().startswith(MARK)]
    return work


def open_work():
    """Every open work issue, with its open pull request when it has one."""
    issues = gh_json("issue", "list", "--label", "gypsy", "--state", "open", "--limit", "200",
                     "--json", "number,title,body,labels,comments")
    prs = gh_json("pr", "list", "--state", "open", "--limit", "200",
                  "--json", "number,headRefName,reviewDecision,files")
    by_branch = {p["headRefName"]: p for p in prs}
    out = []
    for i in sorted(issues, key=lambda x: x["number"]):
        labels = [l["name"] for l in i["labels"]]
        work = parse(i["body"])
        pr = by_branch.get(branch(i["number"]))
        if "blocked" in labels:
            waits = "blocked: a person reads the last comment"
        elif pr and pr["reviewDecision"] == "CHANGES_REQUESTED":
            waits = f"review of #{pr['number']}: changes requested; gypsy drafts again"
        elif pr:
            waits = f"review of #{pr['number']}: a person"
        elif work is None:
            waits = "request of a person: gypsy writes a work definition"
        elif "approved" in labels:
            waits = "draft: gypsy"
        elif "proposed" in labels:
            waits = "approval: a person sets the label approved"
        else:
            waits = "no label: a person sets proposed or approved"
        out.append({"number": i["number"], "title": i["title"], "labels": labels, "work": work, "pr": pr,
                    "waits": waits, "pages": members(work) if work else []})
    return out, prs


def held_pages(prs):
    """Pages in open pull requests: the page is the unit of conflict."""
    held = {}
    for p in prs:
        for f in p["files"]:
            if f["path"].startswith("modules/ROOT/pages/"):
                held[f["path"].removeprefix("modules/ROOT/pages/")] = p["number"]
    return held


def verdict(pr):
    path = os.path.join(HERE, "verdicts", f"{pr}.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def upstream_work(pr):
    """One merged upstream pull request as work, made from its verdict."""
    v = verdict(pr)
    if v is None:
        sys.exit(f"no verdict for upstream pull request {pr}; run gypsy/triage.py {pr} first")
    want = [p["page"] for p in v["pages"] if p["verdict"] != "no change"]
    if not want:
        sys.exit(f"upstream pull request {pr} has no effect on the documentation")
    exists = lambda p: os.path.exists(os.path.join(PAGES, p))
    pages = {"new": [p for p in want if not exists(p)], "amend": [p for p in want if exists(p)]}
    return {"title": f"FreeCAD #{pr}: {v['meta']['title']}", "prs": [pr],
            "pages": {k: v for k, v in pages.items() if v}}


def body_of(work, why=""):
    """The issue text: what a person reads, the evidence, and the definition that gypsy reads."""
    pages = work["pages"]
    out = ["gypsy proposes this work: one cause, all its pages, one pull request.", "",
           "- **To approve:** set the label `approved`. gypsy then drafts the pages.",
           "- **To guide:** write a comment. Each comment goes to the drafter of each page.",
           "- **To change the pages or the upstream pull requests:** edit the work definition below.",
           "- **To reject:** close the issue as not planned.", ""]
    if why:
        out += ["## Why", "", why.strip(), ""]
    out += ["## Upstream pull requests", ""]
    evidence = []
    for pr in work["prs"]:
        v = verdict(pr)
        out.append(f"- FreeCAD/FreeCAD#{pr}" + (f": {v['meta']['title']}" if v else ""))
        if v:
            evidence += [f"**#{pr}**: {v['summary']}", ""]
            evidence += [f"- `{p['page']}` ({p['verdict']}): {p['reason']}" for p in v["pages"] if p["verdict"] != "no change"]
            evidence.append("")
    for pr, rest in (work.get("partial") or {}).items():
        out.append(f"- FreeCAD/FreeCAD#{pr}, in part: only its effect on the rewritten pages. The rest: {rest}.")
    out += ["", f"## Pages ({len(members(work))})", "", "| Page | What gypsy does |", "|---|---|"]
    for kind in ("generated", *KINDS, "reference"):
        for p in pages.get(kind, []):
            out.append(f"| `{p['page'] if isinstance(p, dict) else p}` | {DOES[kind]} |")
    out += ["", "The drafts list the figures they want, and the figure stage makes them before the pull request opens.", ""]
    if evidence:
        out += ["<details><summary>Evidence: the verdicts of the triage</summary>", "", *evidence, "</details>", ""]
    definition = {k: work[k] for k in ("title", "prs", "partial", "pages", "nav", "facts") if work.get(k)}
    out += ["<details><summary>Work definition (gypsy reads this block)</summary>", "", "```yaml",
            yaml.safe_dump(definition, sort_keys=False, allow_unicode=True, width=100).strip(), "```", "", "</details>"]
    return "\n".join(out)


def propose(a):
    if a.upstream:
        work, why, guidance = upstream_work(a.upstream), "", []
    else:
        work = yaml.safe_load(open(a.file, encoding="utf-8"))
        why, guidance = work.pop("why", ""), work.pop("guidance", [])
    n, prs = len(members(work)), len(work["prs"])
    title = f"{work['title']} ({n} page{'s' * (n != 1)}, {prs} upstream PR{'s' * (prs != 1)})"
    body = body_of(work, why)
    if a.dry:
        return print(title + "\n\n" + body)
    ensure_labels()
    if a.update:
        gh("issue", "edit", str(a.update), "--title", title, "--body", body, "--add-label", "gypsy")
        number = a.update
    else:
        url = gh("issue", "create", "--title", title, "--body", body, "--label", "gypsy", "--label", "proposed").strip()
        number = int(url.rsplit("/", 1)[1])
    for g in guidance:                      # guidance that gypsy proposes; a person can answer it
        comment(number, "Guidance that gypsy proposes for the drafter. Write a comment to correct it.\n\n" + g,
                marked=False)
    print(f"issue #{number}: {title}")


def comment(number, text, marked=True):
    gh("issue", "comment", str(number), "--body", (MARK + "\n" if marked else "") + text)


def show(a):
    work = load(a.number)
    guidance = work.pop("guidance")
    print(yaml.safe_dump(work, sort_keys=False, allow_unicode=True, width=100))
    print(f"guidance: {len(guidance)} comment(s)")
    for g in guidance:
        print("  - " + g.replace("\n", "\n    "))


def listing(_a=None):
    items, _ = open_work()
    if not items:
        return print("no open work issue")
    for i in items:
        print(f"#{i['number']:<4} {i['title'][:70]}\n      waits for {i['waits']}   ({len(i['pages'])} pages)")


def run(a):
    """Draft the first approved issue that is free. One issue for each run: one cluster in work."""
    items, prs = open_work()
    held = held_pages(prs)
    for i in items:
        if "approved" not in i["labels"] or "blocked" in i["labels"] or i["work"] is None:
            continue
        if i["pr"]:                              # a person asked for changes: revise the same pull request
            if i["pr"]["reviewDecision"] != "CHANGES_REQUESTED" or not i["work"].get("goals"):
                continue
            cmd = [sys.executable, os.path.join(HERE, "run.py"), str(i["number"]), "--revise", "--pr"]
            print(f"#{i['number']}: revise  {' '.join(cmd[1:])}", flush=True)
            if not a.dry:
                subprocess.run(cmd, cwd=ROOT)
            return
        clash = sorted({held[p] for p in i["pages"] if p in held})
        if clash:
            print(f"#{i['number']}: waits, its pages are in open pull request(s) {', '.join(f'#{n}' for n in clash)}")
            continue
        tool = ["run.py", str(i["number"])] if i["work"].get("goals") else ["draft.py", "--issue", str(i["number"])]
        cmd = [sys.executable, os.path.join(HERE, tool[0]), *tool[1:], "--pr"]
        print(f"#{i['number']}: draft   {' '.join(cmd[1:])}", flush=True)
        if a.dry:
            return
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode:
            gh("issue", "edit", str(i["number"]), "--add-label", "blocked")
            comment(i["number"], f"The draft stopped with exit code {r.returncode}. The log of the run has the cause. "
                                 "Remove the label `blocked` to try again.")
        return
    print("no approved issue is free for a draft")
    listing()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("propose")
    p.add_argument("file", nargs="?")
    p.add_argument("--upstream", type=int, metavar="PR")
    p.add_argument("--update", type=int, metavar="N", help="write the body of issue N again; no new issue")
    p.add_argument("--dry", action="store_true")
    p = sub.add_parser("show")
    p.add_argument("number", type=int)
    p = sub.add_parser("run")
    p.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.cmd == "propose" and not (a.file or a.upstream):
        ap.error("propose needs FILE.yml or --upstream PR")
    {"propose": propose, "show": show, "run": run, None: listing}[a.cmd](a)


if __name__ == "__main__":
    main()
