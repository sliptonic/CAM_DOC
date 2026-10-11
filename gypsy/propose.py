#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy propose: make units of work from verdicts, as issues that a person approves.

    python3 gypsy/propose.py survey                      # group all open verdicts into ranked units
    python3 gypsy/propose.py make ID [ID ...]            # write the issue for these verdicts
    python3 gypsy/propose.py make ID ... --update 13     # write the body of issue #13 again
    python3 gypsy/propose.py make ID ... --dry           # show the issue, change nothing

A verdict is a request to change the documentation (gypsy/verdicts/ID.json): from the triage of
an upstream pull request, from a person, or from a review. `make` asks a model what the unit must
achieve for the documentation as a whole. The issue has the goals, what is left out, the part of
each page, and the definition that the runner reads. Only a person sets the label `approved`.
"""
import argparse, functools, json, os, sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import status   # noqa: E402
import triage   # noqa: E402
import work     # noqa: E402

print = functools.partial(print, flush=True)
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(os.path.dirname(HERE), "modules/ROOT/pages")
MODEL = os.environ.get("GYPSY_PROPOSE_MODEL", "")


def load(vid):
    path = os.path.join(HERE, "verdicts", f"{vid}.json")
    if not os.path.exists(path):
        sys.exit(f"no verdict {vid}; an upstream pull request needs gypsy/triage.py {vid} first")
    return json.load(open(path, encoding="utf-8"))


def open_pages():
    """verdict id -> the pages of the verdict that are not delivered."""
    pages = status.survey_pages()
    status.add_verdicts(pages)
    return {str(u["pr"]): u["open_pages"] for u in status.upstream(pages)}


def held_text():
    issues, prs = work.open_work()
    lines = [f"- {p}: pull request #{n}" for p, n in sorted(work.held_pages(prs).items())]
    lines += [f"- {p}: work issue #{i['number']}" for i in issues for p in i["pages"]]
    return "\n".join(lines) or "(none)", issues


def verdict_text(vid, v, still):
    m = v.get("meta") or {}
    out = [f"## Verdict {vid}: {m.get('title', v.get('summary', ''))}",
           f"Source: {(v.get('source') or {}).get('type', 'upstream-pr')}. Release: {m.get('release', '?')}.",
           f"Summary: {v['summary']}"]
    if v.get("intent"):
        out.append(f"Intent: {v['intent']}")
    for p in v["pages"]:
        if p["verdict"] == "no change":
            continue
        done = "" if p["page"] in still else " (already delivered)"
        out.append(f"- {p['page']}: {p['verdict']}, role {p.get('role', 'not given')}{done}. {p['reason']}")
    return "\n".join(out)


def ask(name, fields):
    prompt = open(os.path.join(HERE, "prompts", f"{name}.md"), encoding="utf-8").read()
    for k, v in fields.items():
        prompt = prompt.replace(f"${k}", v)
    schema = json.load(open(os.path.join(HERE, "schema", f"{name}.schema.json")))
    return triage.ask(prompt, MODEL, schema)


def survey(a):
    still = open_pages()
    held, issues = held_text()
    blocks = [verdict_text(vid, load(vid), pages) for vid, pages in sorted(still.items()) if pages]
    res, run = ask("survey", {"verdicts": "\n\n".join(blocks), "held": held})
    for n, u in enumerate(res["units"], 1):
        print(f"{n:2}. {u['title']}  ({len(u['verdicts'])} verdicts)\n    {u['why']}\n"
              f"    python3 gypsy/propose.py make {' '.join(u['verdicts'])}")
    print(f"\nnothing to document: {len(res['nothing'])}; held by open work: {len(res['held'])}; "
          f"{len(blocks)} open verdicts; cost ${run.get('cost_usd') or 0:.2f}")
    for x in res["nothing"]:
        print(f"  {x['verdict']}: {x['why']}")
    json.dump(res, open(os.path.join(HERE, "jobs", "survey.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


ROLE = {"primary": "tells the subject", "supporting": "agrees and links", "capture": "new figure only"}
MODE = {"new": "new page", "rewrite": "full rewrite", "amend": "small change", "capture": "figure"}


def body_of(unit, verdicts):
    out = ["gypsy proposes this unit of work. One pull request delivers it.", "",
           "- **To approve:** set the label `approved`.",
           "- **To guide:** write a comment. The runner and each writer get it.",
           "- **To change the goals or the pages:** edit the work definition at the end.",
           "- **To reject:** close the issue as not planned.", "",
           "## Summary", "", unit["summary"], "", "## Goals", ""]
    out += [f"{n}. {g}" for n, g in enumerate(unit["goals"], 1)]
    if unit["questions"]:
        out += ["", "## Questions for a person", ""] + [f"- {q}" for q in unit["questions"]]
    out += ["", f"## Pages ({len(unit['pages'])})", "", "| Page | Part | Change | What the page does |", "|---|---|---|---|"]
    out += [f"| `{p['page']}` | {ROLE[p['role']]} | {MODE[p['mode']]} | {p['does']} |" for p in unit["pages"]]
    if unit["excluded"]:
        out += ["", "## Not documented", ""] + [f"- {x['what']}: {x['why']}" for x in unit["excluded"]]
    out += ["", f"## Verdicts ({len(verdicts)})", ""]
    for vid, v in verdicts.items():
        ref = f"FreeCAD/FreeCAD#{v['pr']}" if (v.get("source") or {}).get("type", "upstream-pr") == "upstream-pr" else vid
        out.append(f"- {ref}: {v['summary']}")
    pages = {k: [p["page"] for p in unit["pages"] if p["mode"] == k] for k in ("new", "rewrite", "amend", "capture")}
    definition = {"title": unit["title"], "verdicts": list(verdicts),
                  "prs": [v["pr"] for v in verdicts.values() if isinstance(v.get("pr"), int)],
                  "goals": unit["goals"], "excluded": [x["what"] for x in unit["excluded"]],
                  "pages": {k: v for k, v in pages.items() if v},
                  "plan": {p["page"]: {"role": p["role"], "does": p["does"]} for p in unit["pages"]}}
    out += ["", "<details><summary>Work definition (gypsy reads this block)</summary>", "", "```yaml",
            yaml.safe_dump(definition, sort_keys=False, allow_unicode=True, width=100).strip(), "```", "", "</details>"]
    return "\n".join(out)


def make(a):
    still = open_pages()
    verdicts = {vid: load(vid) for vid in a.ids}
    names = sorted({p["page"] for v in verdicts.values() for p in v["pages"] if p["verdict"] != "no change"})
    held, issues = held_text()
    if a.update:                                 # the pages of the issue itself are not held by other work
        mine = next((i for i in issues if i["number"] == a.update), None)
        held = "\n".join(l for l in held.split("\n") if not l.endswith(f"work issue #{a.update}")) or "(none)"
    unit, run = ask("propose", {
        "verdicts": "\n\n".join(verdict_text(vid, v, still.get(vid, [])) for vid, v in verdicts.items()),
        "pages": "\n".join(triage.page_excerpt(p) for p in names), "held": held})
    n = len(unit["pages"])
    title = f"{unit['title']} ({n} page{'s' * (n != 1)}, {len(verdicts)} verdict{'s' * (len(verdicts) != 1)})"
    body = body_of(unit, verdicts)
    if a.dry:
        return print(f"{title}\n\n{body}\n\n[cost ${run.get('cost_usd') or 0:.2f}]")
    work.ensure_labels()
    if a.update:
        work.gh("issue", "edit", str(a.update), "--title", title, "--body", body, "--add-label", "gypsy")
        number = a.update
    else:
        url = work.gh("issue", "create", "--title", title, "--body", body, "--label", "gypsy", "--label", "proposed").strip()
        number = int(url.rsplit("/", 1)[1])
    print(f"issue #{number}: {title}  [cost ${run.get('cost_usd') or 0:.2f}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("survey")
    m = sub.add_parser("make")
    m.add_argument("ids", nargs="+")
    m.add_argument("--update", type=int, help="write the body of this issue again")
    m.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    {"survey": survey, "make": make}[a.cmd](a)


if __name__ == "__main__":
    main()
