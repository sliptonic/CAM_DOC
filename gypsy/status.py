#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy status: the state of the documentation, one record for each page.

    python3 gypsy/status.py                 # summary, sections, and the pages that need work most
    python3 gypsy/status.py --top 0         # every page
    python3 gypsy/status.py --prs           # every upstream pull request that is not delivered in full
    python3 gypsy/status.py --page job/job.adoc
    python3 gypsy/status.py --json          # the full record, for other tools
    python3 gypsy/status.py --offline       # no GitHub calls

This is step 1 (Survey) of a gypsy iteration. It changes nothing. It joins:

  verdicts   gypsy/verdicts/: upstream pull requests that a page does not cover yet
             (not in its :page-source-pr:), and pages that a verdict wants and that do not exist
  lint       STYLE.md findings on the whole page
  status     :page-status: of the page, and the unverified claims of its last draft (gypsy/jobs/)
  figures    block images with and without an entry in the figure manifest; figures wanted
  links in   how many other pages link to the page: the measure of how central it is
  work       the open work issue (gypsy/work.py) and the open pull requests that hold the page
  GitHub     merged FreeCAD pull requests without a verdict; open issues of this repository

Gap. The report starts with the gap between the documentation and the FreeCAD source, counted
by upstream pull request. A pull request with effect is 'delivered' when each page of its
verdict covers it, 'in part' when some pages do, 'not started' when none does. The
documentation is 'current through' the day before the oldest pull request that is not delivered.
Three parts of the gap have a measure: not delivered, not triaged, not confirmed (claims of the
last draft that nobody checked in a FreeCAD that runs). Pages that were wrong before the first
triaged pull request, and wrong verdicts, have no measure: only an audit finds them.

Score. need = 1.0 for each pending 'revise' verdict, 2.0 for a 'new page', 0.3 for a
'capture only'. weight = 1 + links in / 10, at most 3; gypsy/importance.yml (page: weight)
replaces the weight of a page. score = need x weight. Lint and status are shown, not scored:
a rewrite of the page corrects them.
"""
import argparse
import collections
import glob
import json
import os
import re
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lint  # noqa: E402
import work  # noqa: E402
import triage  # noqa: E402

ROOT = triage.ROOT
PAGES = triage.PAGES
NEED = {"revise": 1.0, "new page": 2.0, "capture only": 0.3}
XREF = re.compile(r"xref:([A-Za-z0-9_./-]+\.adoc)")
BLOCK_IMG = re.compile(r"^image::([^\[]+)\[", re.M)
ATTR = re.compile(r"^:([a-z-]+):[ \t]*(.*)$", re.M)


def gh_json(*args):
    r = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "gh failed")
    return json.loads(r.stdout or "[]")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_yaml(path, default):
    return (yaml.safe_load(read(path)) or default) if os.path.exists(path) else default


def survey_pages():
    pages = {}
    for path in sorted(glob.glob(os.path.join(PAGES, "**/*.adoc"), recursive=True)):
        rel = os.path.relpath(path, PAGES)
        text = read(path)
        attrs = dict(ATTR.findall(text[:3000]))
        title = next((l[2:].strip() for l in text.splitlines() if l.startswith("= ")), rel)
        covered = {int(n) for n in re.findall(r"\d+", attrs.get("page-source-pr", ""))}
        pages[rel] = {"page": rel, "title": title, "exists": True, "text": text, "covered": sorted(covered),
                      "page_status": attrs.get("page-status", ""), "pending": [], "links_in": 0}
    return pages


def add_verdicts(pages):
    """Pending verdicts for each page; a wanted page that does not exist gets a record too."""
    last = ""
    for f in glob.glob(os.path.join(HERE, "verdicts", "*.json")):
        v = json.loads(read(f))
        last = max(last, v["meta"].get("merged_at") or "")
        for p in v["pages"]:
            if p["verdict"] == "no change":
                continue
            rec = pages.setdefault(p["page"], {"page": p["page"], "title": p["page"], "exists": False, "text": "",
                                               "covered": [], "page_status": "", "pending": [], "links_in": 0})
            if v["pr"] in rec["covered"]:
                continue
            rec["pending"].append({"pr": v["pr"], "verdict": p["verdict"], "needs_gui": p["needs_gui"],
                                   "title": v["meta"]["title"], "merged": (v["meta"].get("merged_at") or "")[:10]})
    for rec in pages.values():
        rec["pending"].sort(key=lambda x: x["pr"])
    return last[:10]


def upstream(pages):
    """One record for each triaged upstream pull request: how much of its effect is delivered."""
    out = []
    for f in glob.glob(os.path.join(HERE, "verdicts", "*.json")):
        v = json.loads(read(f))
        want = [p["page"] for p in v["pages"] if p["verdict"] != "no change"]
        open_pages = [p for p in want if any(x["pr"] == v["pr"] for x in pages[p]["pending"])]
        state = "no effect" if not want else "delivered" if not open_pages else \
                "in part" if len(open_pages) < len(want) else "not started"
        out.append({"pr": v["pr"], "title": v["meta"]["title"], "merged": (v["meta"].get("merged_at") or "")[:10],
                    "commit": (v["meta"].get("merge_commit") or "")[:11], "pages": len(want),
                    "open_pages": sorted(open_pages), "state": state})
    return sorted(out, key=lambda x: (x["merged"], x["pr"]))


def gap(ups, pages, info):
    real = [r for r in pages.values() if r["exists"]]
    effect = [u for u in ups if u["state"] != "no effect"]
    open_ = [u for u in effect if u["state"] != "delivered"]
    return {"triaged": len(ups), "no_effect": len(ups) - len(effect), "effect": len(effect),
            "delivered": len(effect) - len(open_), "in_part": sum(1 for u in open_ if u["state"] == "in part"),
            "not_started": sum(1 for u in open_ if u["state"] == "not started"),
            "page_changes": sum(u["pages"] for u in effect), "page_changes_open": sum(len(u["open_pages"]) for u in open_),
            "triaged_through": ups[-1]["merged"] if ups else None, "triaged_commit": ups[-1]["commit"] if ups else None,
            "oldest_open": open_[0] if open_ else None,
            "untriaged": None if info.get("untriaged") is None else len(info["untriaged"]),
            "draft_pages": sum(1 for r in real if r["page_status"] == "draft"),
            "unverified": sum(r["unverified"] for r in real)}


def add_links(pages):
    sources = collections.defaultdict(set)
    for rel, rec in pages.items():
        for target in set(XREF.findall(rec["text"])):
            if target != rel:
                sources[target].add(rel)
    for rel, rec in pages.items():
        rec["links_in"] = len(sources.get(rel, ()))


def add_lint_and_figures(pages):
    terms, style, ok = lint.load_vocab()
    manifest = {f["file"] for f in load_yaml(os.path.join(ROOT, "modules/ROOT/images/manifest.yml"), {}).get("figures") or []}
    for rel, rec in pages.items():
        rec["lint"], rec["lint_kinds"], rec["figures"], rec["figures_captured"] = 0, {}, 0, 0
        if not rec["exists"]:
            continue
        found = lint.lint_file(os.path.join(PAGES, rel), terms, style, ok, manifest)
        found = [f for f in found if f.get("level") != "warning"]
        rec["lint"] = len(found)
        rec["lint_kinds"] = dict(collections.Counter(f["kind"] for f in found))
        images = [t.strip() for t in BLOCK_IMG.findall(rec["text"])]
        rec["figures"] = len(images)
        rec["figures_captured"] = sum(1 for t in images if t in manifest)


def add_jobs(pages):
    """Unverified claims and wanted figures from the last draft of each page."""
    for rec in pages.values():
        rec["unverified"], rec["figures_wanted"] = 0, 0
    for f in glob.glob(os.path.join(HERE, "jobs", "*.json")):
        job = json.loads(read(f))
        for entry in job.get("pages") or [job]:
            rec = pages.get(entry.get("page"))
            if rec:
                rec["unverified"] = len(entry.get("unverified") or [])
                rec["figures_wanted"] = len(entry.get("figures_wanted") or [])


def add_work(pages, offline):
    """The open work issue and the open pull requests that hold each page."""
    for rec in pages.values():
        rec["issue"], rec["open_prs"] = None, []
    info = {"work": None, "untriaged": None, "open_prs": None}
    if offline:
        return info
    try:
        items, prs = work.open_work()
        info["open_prs"] = [p["number"] for p in prs]
        for page, number in work.held_pages(prs).items():
            if page in pages:
                pages[page]["open_prs"].append(number)
        info["work"] = [{k: i[k] for k in ("number", "title", "labels", "waits", "pages")} for i in items]
        for i in items:
            for p in i["pages"]:
                if p in pages:
                    pages[p]["issue"] = i["number"]
    except SystemExit as exc:                                 # no network, no login
        info["error"] = str(exc)[:200]
    return info


def untriaged(since):
    """Merged FreeCAD 'Mod: CAM' pull requests since the newest verdict that have no verdict."""
    have = {int(os.path.basename(f)[:-5]) for f in glob.glob(os.path.join(HERE, "verdicts", "*.json"))}
    out, page = [], 1
    q = f'repo:{triage.REPO} is:pr is:merged base:main label:"Mod: CAM" merged:>={since}'
    while True:
        res = triage.gh("search/issues", q=q, per_page=100, page=page)
        out += [{"pr": i["number"], "title": i["title"]} for i in res["items"] if i["number"] not in have]
        if len(res["items"]) < 100:
            return sorted(out, key=lambda x: x["pr"])
        page += 1


def score(pages):
    importance = load_yaml(os.path.join(HERE, "importance.yml"), {})
    for rel, rec in pages.items():
        rec["need"] = round(sum(NEED.get(p["verdict"], 1.0) for p in rec["pending"]), 1)
        rec["weight"] = float(importance.get(rel, min(3.0, 1 + rec["links_in"] / 10)))
        rec["score"] = round(rec["need"] * rec["weight"], 1)
        del rec["text"]


def row(rec):
    held = ", ".join(([f"#{rec['issue']}"] if rec["issue"] else []) + [f"PR #{n}" for n in rec["open_prs"]])
    state = "missing" if not rec["exists"] else (rec["page_status"] or "-")
    figures = f"{rec['figures_captured']}/{rec['figures']}" + (f" +{rec['figures_wanted']}" if rec["figures_wanted"] else "")
    return [f"{rec['score']:.1f}", rec["page"][:-5], str(len(rec["pending"])),
            str(sum(1 for p in rec["pending"] if p["needs_gui"])), str(rec["links_in"]), str(rec["lint"]),
            state, str(rec["unverified"] or "-"), figures, held or "-"]


def table(head, rows):
    widths = [max(len(r[i]) for r in [head] + rows) for i in range(len(head))]
    for r in [head, ["-" * w for w in widths]] + rows:
        print("  ".join(c.ljust(w) if i in (1, 6, 9) else c.rjust(w) for i, (c, w) in enumerate(zip(r, widths))).rstrip())


def print_report(pages, info, last, top, prs_shown):
    recs = list(pages.values())
    real = [r for r in recs if r["exists"]]
    pend = [r for r in recs if r["pending"]]
    print(f"gypsy status   {len(real)} pages   newest verdict {last or 'none'}\n")
    g = info["gap"]
    print("Gap between the documentation and the source, by upstream pull request\n")
    print(f"  triaged   {g['triaged']} through {g['triaged_through']} (FreeCAD {g['triaged_commit']}):"
          f"   {g['no_effect']} without effect   {g['effect']} with effect")
    done = f"{100 * g['delivered'] // g['effect']}%" if g["effect"] else "-"
    print(f"  1 not delivered   {g['in_part'] + g['not_started']} of {g['effect']}"
          f"   ({g['not_started']} not started, {g['in_part']} in part; {g['delivered']} delivered, {done})"
          f"   {g['page_changes_open']} of {g['page_changes']} page changes")
    print(f"  2 not triaged     {'not read' if g['untriaged'] is None else g['untriaged']}   merged after the newest verdict")
    print(f"  3 not confirmed   {g['unverified']} claims on {g['draft_pages']} pages with status draft")
    print("  4 unknown         no measure (no audit)")
    o = g["oldest_open"]
    print(f"  current through   " + (f"the day before {o['merged']}: #{o['pr']} {o['title'][:60]}" if o else
                                   f"{g['triaged_through']}, the newest verdict") + "\n")
    print("Pages\n")
    print(f"  pages with pending verdicts   {len(pend)}  ({sum(len(r['pending']) for r in pend)} verdicts, "
          f"{sum(1 for r in pend if not r['exists'])} pages to create)")
    print(f"  pages current with all verdicts and lint clean   "
          f"{sum(1 for r in real if not r['pending'] and not r['lint'])}")
    print(f"  lint findings   {sum(r['lint'] for r in real)} on {sum(1 for r in real if r['lint'])} pages")
    print(f"  pages with status draft   {sum(1 for r in real if r['page_status'] == 'draft')}"
          f"   unverified claims   {sum(r['unverified'] for r in real)}")
    print(f"  figures   {sum(r['figures_captured'] for r in real)} captured of {sum(r['figures'] for r in real)}"
          f"   wanted   {sum(r['figures_wanted'] for r in real)}")
    if info.get("error"):
        print(f"  GitHub   not read: {info['error']}")
    elif info["untriaged"] is not None:
        print(f"  merged FreeCAD pull requests without a verdict   {len(info['untriaged'])}")
        print(f"  open pull requests   {len(info['open_prs'])}")
    if info.get("work") is not None:
        print(f"\nWork issues ({len(info['work'])} open)\n")
        for i in info["work"]:
            left = sum(len(pages[p]["pending"]) for p in i["pages"] if p in pages)
            print(f"  #{i['number']:<4} {i['title'][:64]}\n        waits for {i['waits']}   {left} pending verdicts on its pages")

    sections = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for r in recs:
        s = sections[r["page"].split("/")[0] if "/" in r["page"] else "(top)"]
        s[0] += 1
        s[1] += len(r["pending"])
        s[2] += r["score"]
        s[3] += r["lint"]
    if prs_shown is not None:
        byscore = {u["pr"]: sum(pages[p]["weight"] for p in u["open_pages"]) for u in info["upstream"]}
        rows = sorted((u for u in info["upstream"] if u["open_pages"]), key=lambda u: -byscore[u["pr"]])
        rows = rows if not prs_shown else rows[:prs_shown]
        print(f"\nUpstream pull requests not delivered ({len(rows)}, by weight of their open pages)\n")
        for u in rows:
            print(f"  {byscore[u['pr']]:5.1f}  #{u['pr']} {u['merged']} {u['state']:11}  {len(u['open_pages'])}/{u['pages']} pages open"
                  f"  {u['title'][:56]}")
            print("         " + ", ".join(p[:-5] for p in u["open_pages"]))
    print("\nSections\n")
    rows = [[f"{v[2]:.1f}", k, str(v[0]), str(v[1]), str(v[3])] for k, v in sorted(sections.items(), key=lambda x: -x[1][2])]
    head = ["score", "section", "pages", "pending", "lint"]
    widths = [max(len(r[i]) for r in [head] + rows) for i in range(5)]
    for r in [head, ["-" * w for w in widths]] + rows:
        print("  ".join(c.ljust(w) if i == 1 else c.rjust(w) for i, (c, w) in enumerate(zip(r, widths))).rstrip())

    ranked = sorted(recs, key=lambda r: (-r["score"], -r["lint"], r["page"]))
    shown = ranked if not top else ranked[:top]
    print(f"\nPages ({len(shown)} of {len(ranked)}, by score)\n")
    table(["score", "page", "pend", "gui", "in", "lint", "status", "unver", "figures", "held by"], [row(r) for r in shown])
    print("\npend: verdicts not covered   gui: of these, need a running FreeCAD   in: pages that link here"
          "\nfigures: captured/all, +wanted   held by: work issue or open pull request")


def print_page(rec):
    print(f"{rec['page']}   {rec['title']}")
    print(f"  score {rec['score']} = need {rec['need']} x weight {rec['weight']}   links in {rec['links_in']}")
    print(f"  status {rec['page_status'] or '-'}   exists {rec['exists']}   unverified claims {rec['unverified']}")
    print(f"  lint {rec['lint']} {rec['lint_kinds'] or ''}")
    print(f"  figures {rec['figures_captured']} captured of {rec['figures']}, {rec['figures_wanted']} wanted")
    print(f"  work issue {rec['issue'] or '-'}   open pull requests {rec['open_prs'] or '-'}")
    print(f"  covers upstream PRs: {', '.join(map(str, rec['covered'])) or '-'}")
    print(f"  pending verdicts: {len(rec['pending'])}")
    for p in rec["pending"]:
        print(f"    #{p['pr']} {p['merged']} {p['verdict']}{' (gui)' if p['needs_gui'] else ''}: {p['title']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=20, help="pages in the table; 0 for all")
    ap.add_argument("--page", help="detail of one page, relative to modules/ROOT/pages")
    ap.add_argument("--prs", action="store_true", help="list every upstream pull request that is not delivered")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--offline", action="store_true", help="do not read GitHub")
    a = ap.parse_args()

    pages = survey_pages()
    last = add_verdicts(pages)
    add_links(pages)
    add_lint_and_figures(pages)
    add_jobs(pages)
    info = add_work(pages, a.offline)
    if not a.offline and not info.get("error") and last:
        try:
            info["untriaged"] = untriaged(last)
        except SystemExit as exc:
            info["error"] = str(exc)[:200]
    score(pages)
    info["upstream"] = upstream(pages)
    info["gap"] = gap(info["upstream"], pages, info)

    if a.page:
        if a.page not in pages:
            sys.exit(f"gypsy status: no such page and no verdict for it: {a.page}")
        return print(json.dumps(pages[a.page], indent=1)) if a.json else print_page(pages[a.page])
    if a.json:
        return print(json.dumps({"newest_verdict": last, **info, "pages": list(pages.values())}, indent=1))
    print_report(pages, info, last, a.top, 0 if a.prs else 8)


if __name__ == "__main__":
    main()
