#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy figures: make the figures that the drafts want.

    python3 gypsy/figures.py                         # every wanted figure, page by page
    python3 gypsy/figures.py --page job/job.adoc     # the wanted figures of one page
    python3 gypsy/figures.py --list                  # show what is wanted, do nothing
    python3 gypsy/figures.py --pr                    # also commit, push and open a pull request

A draft lists the figures it wants (`figures_wanted` in gypsy/jobs/*.json). For each page this
stage starts one agent: it reads the FreeCAD source, writes a capture recipe for each figure,
runs it with gypsy/capture.py, looks at the image, corrects the recipe, and puts the figure into
the page. The agent can read files, edit files in this repository and run capture.py and lint.py;
it has no other commands. A recipe is Python that FreeCAD runs on this machine.

After the agent, this stage checks each figure itself: the image, the recipe and the manifest
entry exist, the page uses the image, and lint is clean on the changed lines. With --pr it runs
only in gypsy's own worktree and delivers all pages as one pull request.
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402
import draft  # noqa: E402

ROOT = config.ROOT
PAGES = draft.PAGES
IMAGES = os.path.join(ROOT, "modules/ROOT/images")
TOOLS = "Read,Grep,Glob,Write,Edit,Bash(python3 gypsy/capture.py:*),Bash(python3 gypsy/lint.py:*)"
BUDGET = os.environ.get("GYPSY_FIGURE_BUDGET", "8")          # US dollars for one page


def wanted_figures():
    """page -> list of 'file.png: description', for figures whose image does not exist."""
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, "jobs", "*.json"))):
        job = json.load(open(f, encoding="utf-8"))
        for entry in job.get("pages") or [job]:
            for line in entry.get("figures_wanted") or []:
                target = line.split(":", 1)[0].strip()
                if not target.endswith(".png") or os.path.exists(os.path.join(IMAGES, target)):
                    continue
                lines = out.setdefault(entry["page"], [])
                if line not in lines:
                    lines.append(line)
    return out


def manifest_files():
    path = os.path.join(IMAGES, "manifest.yml")
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    return {f["file"] for f in data.get("figures") or []}


def run_agent(page, lines, model):
    tmpl = open(os.path.join(HERE, "prompts", "figures.md"), encoding="utf-8").read()
    prompt = tmpl.replace("$freecad_tree", config.FREECAD_TREE).replace("$page", page) \
                 .replace("$figures", "\n".join(f"- {l}" for l in lines))
    schema = json.load(open(os.path.join(HERE, "schema", "figures.schema.json")))
    cmd = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
           "--add-dir", config.FREECAD_TREE, "--permission-mode", "acceptEdits",
           "--allowedTools", TOOLS, "--max-budget-usd", BUDGET]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=ROOT)
    try:
        env = json.loads(r.stdout)
    except ValueError:
        return None, {"error": (r.stderr or r.stdout).strip()[:1500]}
    res = env.get("structured_output") or env.get("result")
    if isinstance(res, str):
        try:
            res = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", res.strip()))
        except ValueError:
            res = None
    run = {"cost_usd": env.get("total_cost_usd"), "duration_ms": env.get("duration_ms"),
           "turns": env.get("num_turns"),
           "model": (env.get("modelUsage") and next(iter(env["modelUsage"]))) or model or "default"}
    if res is None:
        run["error"] = str(env.get("result") or env.get("subtype") or "no structured result")[:1500]
    return res, run


def check(page, fig):
    """What this stage can verify without the agent. Returns the list of problems."""
    problems = []
    if fig["status"] != "done":
        return problems
    file = fig["file"].removeprefix("modules/ROOT/images/")
    fig["file"] = file
    recipe = os.path.join(IMAGES, "recipes", file[:-4] + ".py")
    if not os.path.exists(os.path.join(IMAGES, file)):
        problems.append("the image file does not exist")
    if not os.path.exists(recipe):
        problems.append("the recipe does not exist")
    if file not in manifest_files():
        problems.append("no manifest entry")
    if f"image::{file}[" not in open(os.path.join(PAGES, page), encoding="utf-8").read():
        problems.append("the page does not use the image")
    return problems


def make(wanted, model=""):
    """Run the agent for each page of `wanted` (page -> lines). Returns one entry for each page.

    A line can name an image that exists: a draft asks for a new capture of a figure that changed."""
    pages = []
    for page, lines in wanted.items():
        if not lines:
            continue
        res, run = run_agent(page, lines, model)
        figures = (res or {}).get("figures") or []
        for fig in figures:
            fig["check"] = check(page, fig)
        report, rc = draft.lint(os.path.join(PAGES, page), "origin/main")
        pages.append({"page": page, "wanted": lines, "figures": figures, "notes": (res or {}).get("notes", ""),
                      "lint_rc": rc, "lint": report, "run": run})
        done = sum(1 for f in figures if f["status"] == "done" and not f["check"])
        print(f"{page}: {done} of {len(lines)} figures done; lint rc={rc}; "
              f"cost ${run.get('cost_usd') or 0:.2f}" + (f"; ERROR {run['error'][:200]}" if run.get("error") else ""),
              flush=True)
    return pages


def report_lines(pages):
    """Markdown for a pull request: the figures made and the figures not made."""
    all_figs = [(p["page"], f) for p in pages for f in p["figures"]]
    done = [(pg, f) for pg, f in all_figs if f["status"] == "done" and not f["check"]]
    out = []
    if done:
        out += ["| Page | Figure | Shows |", "|---|---|---|"]
        out += [f"| `{pg}` | `{f['file']}` | {f['shows']} |" for pg, f in done]
    rest = [(pg, f) for pg, f in all_figs if (pg, f) not in done]
    if rest:
        out += ["", "Figures not made:", ""]
        out += [f"- `{pg}`: {f['wanted'].split(':', 1)[0]}: {f['status']}. "
                f"{f['problem'] or '; '.join(f['check']) or f['file']}" for pg, f in rest]
    return out, done, rest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", action="append", help="only this page (relative to modules/ROOT/pages)")
    ap.add_argument("--list", action="store_true", help="show the wanted figures and stop")
    ap.add_argument("--pr", action="store_true", help="commit, push and open one pull request")
    ap.add_argument("--model", default=os.environ.get("GYPSY_FIGURE_MODEL", ""))
    a = ap.parse_args()

    if a.pr:
        draft.start_clean()
    wanted = wanted_figures()
    if a.page:
        wanted = {p: v for p, v in wanted.items() if p in a.page}
    if a.list or not wanted:
        for page, lines in wanted.items():
            print(page)
            for l in lines:
                print(f"  {l}")
        print(f"{sum(len(v) for v in wanted.values())} figures wanted on {len(wanted)} pages")
        return
    config.require_freecad_tree()
    if not os.access(config.FREECAD_BIN, os.X_OK):
        sys.exit(f"gypsy figures: no FreeCAD build at {config.FREECAD_BIN}; run gypsy/freecad-tree.sh")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    branch = f"gypsy/figures-{stamp}"
    if a.pr:
        draft.sh("git", "checkout", "-q", "-B", branch, "origin/main")

    pages = make(wanted, a.model)

    cost = sum(p["run"].get("cost_usd") or 0 for p in pages)
    jobdir = os.path.join(HERE, "jobs")
    os.makedirs(jobdir, exist_ok=True)
    jobfile = os.path.join(jobdir, f"figures-{stamp}.json")
    json.dump({"figures_run": stamp, "pages": pages, "cost_usd": cost}, open(jobfile, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    all_figs = [(p["page"], f) for p in pages for f in p["figures"]]
    done = [(pg, f) for pg, f in all_figs if f["status"] == "done" and not f["check"]]
    print(f"figures: {len(done)} done of {sum(len(p['wanted']) for p in pages)} wanted; cost ${cost:.2f}; job {jobfile}")
    if not a.pr:
        return
    if not done:
        draft.sh("git", "checkout", "-q", "-f", "--detach", "origin/main")
        sys.exit("gypsy figures: no figure was made; no pull request")

    table, done, rest = report_lines(pages)
    body = [f"Figures that the drafts wanted: {len(done)} made, on {len({pg for pg, _ in done})} pages.", "",
            "Each figure has a recipe (`modules/ROOT/images/recipes/`) and a manifest entry. "
            "Review the figures in the rendered diff from the preview comment below.", ""] + table
    failed_lint = [p for p in pages if p["lint_rc"]]
    for p in failed_lint:
        body += ["", f"Lint on `{p['page']}`:", "", "```", p["lint"], "```"]
    body += ["", f"FreeCAD `{config.FREECAD_TREE}`; model {pages[0]['run'].get('model')}; cost ${cost:.2f}.",
             "", "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    labels = ["gypsy"] + (["lint-failed"] if failed_lint else []) + (["needs-capture"] if rest else [])
    url = draft.publish(branch, f"gypsy: {len(done)} figures for {len({pg for pg, _ in done})} pages",
                        f"figures: {len(done)} captured figures for {len({pg for pg, _ in done})} pages",
                        "\n".join(body), labels)
    print(f"pull request: {url}")


if __name__ == "__main__":
    main()
