#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy run: the runner. It takes one approved unit of work from its issue to a pull request.

    python3 gypsy/run.py ISSUE [--pr] [--rounds N] [--no-figures]

    1. brief     one agent reads the FreeCAD source and writes the facts that all pages share
    2. draft     one writer for each page, in parallel, with the goals, the plan and the brief
    3. review    one independent reviewer compares the pages with the FreeCAD source, the plan,
                 the guidance and each other. The source is the authority, not the brief; each
                 finding gives its evidence, and a finding can correct a fact of the brief
    4. revise    the writer of each page with a finding drafts again; steps 3 and 4 repeat, at
                 most N rounds (default 2); after round 1 only `must` findings start a revision
    5. figures   the figure stage makes the images that the pages want
    6. review    one last review; its result is the report of the pull request
    7. pull request, linked to the issue

Lint runs after each draft and each revision. The issue must have the label `approved`.
"""
import argparse, concurrent.futures, datetime, functools, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config   # noqa: E402
import draft    # noqa: E402
import triage   # noqa: E402
import work     # noqa: E402

print = functools.partial(print, flush=True)
ROOT, PAGES = config.ROOT, draft.PAGES
READ_TOOLS = "Read,Grep,Glob"
REVIEW_TOOLS = READ_TOOLS + ",Bash(git diff:*),Bash(git show:*),Bash(git log:*),Bash(git status:*)"
BUDGET = os.environ.get("GYPSY_AGENT_BUDGET", "10")          # US dollars for one brief or one review
WRITERS = int(os.environ.get("GYPSY_WRITERS", "4"))


def agent(name, fields, model, tools=READ_TOOLS):
    """Run a read-only agent with a prompt template and a schema. Returns (result, run)."""
    prompt = open(os.path.join(HERE, "prompts", f"{name}.md"), encoding="utf-8").read()
    for k in sorted(fields, key=len, reverse=True):
        prompt = prompt.replace(f"${k}", fields[k])
    schema = json.load(open(os.path.join(HERE, "schema", f"{name}.schema.json")))
    cmd = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
           "--add-dir", config.FREECAD_TREE, "--allowedTools", tools, "--max-budget-usd", BUDGET]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=ROOT)
    try:
        env = json.loads(r.stdout)
    except ValueError:
        sys.exit(f"{name}: {(r.stderr or r.stdout).strip()[:1500]}")
    res = env.get("structured_output")
    if not isinstance(res, dict):
        sys.exit(f"{name}: no result: {str(env.get('result') or env.get('subtype'))[:1500]}")
    return res, {"stage": name, "cost_usd": env.get("total_cost_usd") or 0, "turns": env.get("num_turns"),
                 "duration_ms": env.get("duration_ms")}


def unit_text(c, page=None):
    out = ["Goals:"] + [f"{n}. {g}" for n, g in enumerate(c["goals"], 1)]
    if c.get("excluded"):
        out += ["", "Not documented in this unit:"] + [f"- {x}" for x in c["excluded"]]
    out += ["", "Plan (the part of each page):"]
    out += [f"- {p} ({v['role']}, {v.get('diataxis', 'form not given')}): {v['does']}" for p, v in c["plan"].items()]
    if page:
        out += ["", f"Your page is {page}. Its part: {c['plan'][page]['does']}"]
        form = c["plan"][page].get("diataxis")
        if form:
            out.append(f"The Diátaxis form of what you add is {form} ({work.DIATAXIS[form]}). Write it in that form.")
    return "\n".join(out)


def brief_text(b):
    out = ["Facts (id, owner page, fact, source):"]
    out += [f"- {f['id']} [{f['owner']}] {f['fact']} ({f['source']})" for f in b["facts"]]
    out += ["", "Terms:"] + [f"- Use \"{t['use']}\". Do not use: {t['not']}." for t in b["terms"]]
    out += ["", "Not established from the source:"] + [f"- {u}" for u in b["unknown"] or ["nothing"]]
    return "\n".join(out)


def verdicts_of(c):
    vs = {vid: json.load(open(os.path.join(HERE, "verdicts", f"{vid}.json"), encoding="utf-8"))
          for vid in map(str, c.get("verdicts") or c["prs"])}
    return vs


def page_verdicts(page, c, vs):
    """The verdict entries for a page, in the form that draft_page reads. A page that the plan
    added without a verdict gets the plan text for each upstream pull request of the unit."""
    found = draft.verdicts_for(page, set(c["prs"]))
    if found:
        return found
    part = {"verdict": "revise", "needs_gui": False, "sections": [], "reason": c["plan"][page]["does"]}
    return sorted((v["meta"]["merged_at"], v["pr"], v["meta"]["title"], v["meta"]["merge_commit"], part)
                  for v in vs.values() if isinstance(v.get("pr"), int))


def add_nav(page):
    """Put a new page into the navigation, after the last entry of its folder."""
    nav = os.path.join(ROOT, "modules/ROOT/nav.adoc")
    lines = open(nav, encoding="utf-8").read().split("\n")
    if any(f"xref:{page}[" in l for l in lines):
        return
    text = open(os.path.join(PAGES, page), encoding="utf-8").read()
    title = next((l[2:].strip() for l in text.split("\n") if l.startswith("= ")), page)
    folder = os.path.dirname(page)
    while folder and not any(f"xref:{folder}/" in l for l in lines):
        folder = os.path.dirname(folder)         # no entry of the folder yet: use the folder above
    at = max((i for i, l in enumerate(lines) if f"xref:{folder}/" in l), default=None) if folder else None
    if at is None:
        at = max(i for i, l in enumerate(lines) if l.startswith("*"))
    stars = lines[at].split(" ", 1)[0]
    lines.insert(at + 1, f"{stars} xref:{page}[{title}]")
    open(nav, "w", encoding="utf-8").write("\n".join(lines))


def review(c, brief, modes, previous, model):
    """The independent reviewer. `previous` is the findings that the writers got before this review."""
    before = ""
    if previous:
        before = ("# Findings of the review before this one\n\nThe writers got these findings and revised the pages. "
                  "Examine each one in the pages as they are now, and report it again only when it is still present. "
                  "Examine the lines that the revision changed for new faults.\n\n" +
                  "\n".join(f"- `{f['page']}` ({f['kind']}): {f['text']}" for f in previous))
    fields = {"freecad_tree": config.FREECAD_TREE, "unit": unit_text(c), "brief": brief_text(brief),
              "guidance": "\n\n".join(c["guidance"]) or "(none)", "previous": before,
              "pages": "\n".join(f"- {p}: {m}" for p, m in modes.items())}
    return agent("review", fields, model, REVIEW_TOOLS)


def correct_brief(brief, findings):
    """Put the brief corrections of the reviewer into the brief. Returns the ids that changed."""
    facts, changed = {f["id"]: f for f in brief["facts"]}, []
    for f in findings:
        fid = f.get("brief_fact", "").strip()
        if fid in facts and f.get("brief_correction", "").strip():
            facts[fid]["fact"] = f["brief_correction"].strip()
            facts[fid]["source"] = f["evidence"].strip() + " (corrected by the review)"
            changed.append(fid)
    return changed


def todo_line(f):
    return f"- ({f['kind']}) {f['text']}\n  Evidence: {f.get('evidence') or 'not given'}\n  Do: {f['fix']}"


def open_pr(branch):
    prs = work.gh_json("pr", "list", "--head", branch, "--state", "open", "--json", "number,reviews,comments")
    return prs[0] if prs else None


def feedback(pr):
    """What people wrote on the pull request: reviews and comments that gypsy did not write."""
    texts = [r["body"] for r in pr["reviews"] if r["body"].strip()] + \
            [x["body"] for x in pr["comments"] if not x["body"].lstrip().startswith(work.MARK)
             and "github-actions" not in (x.get("author") or {}).get("login", "")]
    return [t.strip() for t in texts if t.strip()]


def findings_md(findings):
    return [f"- `{f['page']}` ({f['kind']}, {f['severity']}): {f['text']}" for f in findings]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issue", type=int)
    ap.add_argument("--pr", action="store_true", help="commit, push and open the pull request")
    ap.add_argument("--rounds", type=int, default=2, help="revision rounds after the first draft")
    ap.add_argument("--revise", action="store_true",
                    help="work on the open pull request of the issue: review and revise its pages, with the "
                         "review comments of people; no new draft")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--no-replan", action="store_true", help="do not apply the comments of people to the plan")
    ap.add_argument("--model", default=os.environ.get("GYPSY_DRAFT_MODEL", ""))
    a = ap.parse_args()

    c = work.load(a.issue)
    if "approved" not in c["labels"]:
        sys.exit(f"issue #{a.issue} does not have the label approved")
    if c["guidance"] and not a.no_replan and not a.revise:        # the comments of the person can change the plan
        subprocess.run([sys.executable, os.path.join(HERE, "propose.py"), "make", "--update", str(a.issue), "--replan"],
                       cwd=ROOT, check=True)
        c = work.load(a.issue)
    if not c.get("goals") or not c.get("plan"):
        sys.exit(f"issue #{a.issue} has no goals and plan; write it again with gypsy/propose.py make ... --update {a.issue}")
    draft.start_clean()
    branch = work.branch(a.issue)
    pr = open_pr(branch)
    if a.revise:
        if not pr:
            sys.exit(f"issue #{a.issue} has no open pull request to revise")
        draft.sh("git", "fetch", "-q", "origin", f"+{branch}:refs/remotes/origin/{branch}")
        draft.sh("git", "checkout", "-q", "-B", branch, f"origin/{branch}")
        # The runner reads its prompts, schemas and the figure stage from the working tree. Bring the branch to
        # the published main, so that the tools and the other pages are current.
        merged = subprocess.run(["git", "-c", "user.name=sliptonic", "-c", "user.email=shopinthewoods@gmail.com", "merge",
                                 "-q", "--no-edit", "origin/main"], cwd=ROOT, capture_output=True, text=True)
        if merged.returncode:
            subprocess.run(["git", "merge", "--abort"], cwd=ROOT)
            draft.sh("git", "checkout", "-q", "-f", "--detach", "origin/main")
            sys.exit(f"origin/main does not merge into {branch}; a person must resolve it:\n{merged.stdout}{merged.stderr}"[:1500])
        said = feedback(pr)
        c["guidance"] += [f"Review of a person on pull request #{pr['number']}:\n{s}" for s in said]
        print(f"revise pull request #{pr['number']}: {len(said)} review comments of people")
    else:
        if pr:
            sys.exit(f"issue #{a.issue} has the open pull request #{pr['number']}; use --revise, or close it for a new draft")
        draft.sh("git", "checkout", "-q", "-B", branch, "origin/main")
    vs = verdicts_of(c)
    lacks = config.update_freecad_tree({v["meta"]["merge_commit"] for v in vs.values() if v.get("meta")})
    if lacks:
        sys.exit(f"the FreeCAD tree does not contain {', '.join(x[:11] for x in lacks)}; the brief needs the source")
    modes = {p: m for m in ("new", "rewrite", "amend") for p in c["pages"].get(m, [])}
    runs = []

    jobfile = os.path.join(HERE, "jobs", f"issue-{a.issue}.json")
    history, figure_pages = [], []

    def unit_of(page):
        return unit_text(c, page) + "\n\nBrief:\n" + brief_text(brief)

    def write(page, prompt_only=False):
        return draft.draft_page(page, page_verdicts(page, c, vs), modes[page], c.get("facts") or [], "(the plan and "
                                "the brief replace the text of the other pages)", a.model, guidance=c["guidance"],
                                unit=unit_of(page), prompt_only=prompt_only)

    if a.revise:                                 # the brief and the page records of the first run
        old = json.load(open(jobfile, encoding="utf-8"))
        brief, jobs, history, runs, figure_pages = old["brief"], old["pages"], old["checks"], old["runs"], old["figures"]
        for j in jobs:
            j["prompt"] = write(j["page"], prompt_only=True)
    else:
        # 1. brief
        files = sorted({f["filename"] for pr in c["prs"] for f in triage.gh_paged(f"repos/{triage.REPO}/pulls/{pr}/files")})
        vtext = "\n\n".join(f"## {vid}: {v['meta']['title']}\n{v['summary']}\n" + (v.get("intent") or "") + "\n" +
                            "\n".join(f"- {p['page']}: {p['reason']}" for p in v["pages"] if p["verdict"] != "no change")
                            for vid, v in vs.items())
        brief, run = agent("brief", {"freecad_tree": config.FREECAD_TREE, "unit": unit_text(c), "verdicts": vtext,
                                     "files": "\n".join(f"- {f}" for f in files)}, a.model)
        runs.append(run)
        print(f"brief: {len(brief['facts'])} facts, {len(brief['terms'])} terms, {len(brief['unknown'])} unknown; "
              f"cost ${run['cost_usd']:.2f}")

        # 2. draft, one writer for each page
        with concurrent.futures.ThreadPoolExecutor(WRITERS) as pool:
            jobs = list(pool.map(write, modes))
        for j in jobs:
            print(f"drafted {j['page']} ({j['mode']}); lint rc={j['lint_rc']}; cost ${j['cost_usd']:.2f}")
    by_page = {j["page"]: j for j in jobs}
    for page, mode in modes.items():
        if mode == "new":
            add_nav(page)

    # 3 and 4. review and revise
    first, given = len(history), []
    for rnd in range(1, a.rounds + 1):
        res, run = review(c, brief, modes, given, a.model)
        runs.append(run)
        fixed = correct_brief(brief, res["findings"])
        if fixed:                                # the writers get the corrected brief
            for j in jobs:
                j["prompt"] = write(j["page"], prompt_only=True)
        must = [f for f in res["findings"] if f["severity"] == "must" and f["page"] in by_page]
        history.append({"round": len(history) + 1, "findings": res["findings"], "goals": res["goals"]})
        print(f"review {rnd}: {len(res['findings'])} findings, {len(must)} must; {res['confirmed']} statements confirmed; "
              f"brief corrected: {', '.join(fixed) or 'none'}; goals " +
              ", ".join(g["met"] for g in res["goals"]) + f"; cost ${run['cost_usd']:.2f}")
        act = [f for f in res["findings"] if f["page"] in by_page] if rnd == 1 else must
        if not act:                              # round 1 corrects each finding; later rounds only `must`
            break
        todo = {}
        for f in res["findings"]:                # a writer that drafts again gets all its findings
            if f["page"] in {m["page"] for m in act}:
                todo.setdefault(f["page"], []).append(todo_line(f))
        given = [f for f in res["findings"] if f["page"] in todo]
        with concurrent.futures.ThreadPoolExecutor(WRITERS) as pool:
            list(pool.map(lambda p: draft.revise_page(by_page[p], "\n".join(todo[p]), a.model), todo))
        print(f"revised {len(todo)} pages: " + ", ".join(f"{p} (lint rc={by_page[p]['lint_rc']})" for p in todo))

    # 5. figures
    have = {f["file"] for p in figure_pages for f in p["figures"] if f["status"] != "failed" and not f["check"]}
    wanted = {j["page"]: [w for w in j["figures_wanted"] if w.split(":", 1)[0].strip() not in have] for j in jobs}
    wanted = {p: w for p, w in wanted.items() if w}
    for p in ([] if a.revise else c["pages"].get("capture", [])):
        wanted.setdefault(p, []).append(f"{p[:-5]}/(the figure of the page that changed): {c['plan'][p]['does']}")
    if wanted and not a.no_figures:
        import figures
        new_figures = figures.make(wanted, a.model)
        figure_pages = figure_pages + new_figures
        made = {f["wanted"] for p in new_figures for f in p["figures"] if f["status"] != "failed" and not f["check"]}
        for j in jobs:
            j["figures_wanted"] = [w for w in j["figures_wanted"] if w not in made]
            j["lint"], j["lint_rc"] = draft.lint(os.path.join(PAGES, j["page"]), "origin/main" if j["mode"] == "amend" else None)

    # 6. the last review is the report
    final, run = review(c, brief, modes, given, a.model)
    runs.append(run)
    if correct_brief(brief, final["findings"]):
        for j in jobs:
            j["prompt"] = write(j["page"], prompt_only=True)
    history.append({"round": "final", "findings": final["findings"], "goals": final["goals"], "merge": final["merge"],
                    "confirmed": final["confirmed"], "untested": final["untested"], "notes": final["notes"]})
    left = [f for f in final["findings"] if f["severity"] == "must"]
    print(f"final review: {len(final['findings'])} findings, {len(left)} must; merge {final['merge']}; goals " + ", ".join(g["met"] for g in final["goals"]))

    # the writers correct what the last review and the last lint found; no review follows
    todo = {}
    for f in final["findings"]:
        if f["page"] in by_page and f["kind"] != "figure":
            todo.setdefault(f["page"], []).append(todo_line(f))
    for j in jobs:
        if j["lint_rc"]:
            todo.setdefault(j["page"], []).append("- (lint) " + j["lint"].strip().replace("\n", "\n  "))
    if todo:
        with concurrent.futures.ThreadPoolExecutor(WRITERS) as pool:
            list(pool.map(lambda p: draft.revise_page(by_page[p], "\n".join(todo[p]), a.model), todo))
        print(f"finish: revised {len(todo)} pages: " + ", ".join(f"{p} (lint rc={by_page[p]['lint_rc']})" for p in todo))
    for j in jobs:
        j.pop("prompt", None)
    cost = sum(j["cost_usd"] for j in jobs) + sum(r["cost_usd"] for r in runs) + \
        sum(p["run"].get("cost_usd") or 0 for p in figure_pages)
    os.makedirs(os.path.join(HERE, "jobs"), exist_ok=True)
    json.dump({"issue": a.issue, "branch": branch, "brief": brief, "checks": history, "pages": jobs, "figures": figure_pages,
               "runs": runs, "cost_usd": cost,
               "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")},
              open(jobfile, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"issue {a.issue}: {len(jobs)} pages on {branch}; cost ${cost:.2f}; job {jobfile}")
    if not a.pr:
        return

    # 7. pull request
    mark = {"yes": "achieved", "partly": "in part", "no": "not achieved"}
    body = [f"**{c['title']}**", "", f"Closes #{a.issue}", "", "## Goals of the issue", "", "| Goal | Result | Where |", "|---|---|---|"]
    body += [f"| {g['goal']} | {mark[g['met']]}{': ' + g['note'] if g['met'] != 'yes' and g['note'] else ''} | {g['where']} |"
             for g in final["goals"]]
    body += ["", "## Findings of the last review", "",
             f"An independent reviewer compared the pages with the FreeCAD source. It confirmed {final['confirmed']} "
             f"statements. Its decision before the last corrections: {'merge' if final['merge'] == 'yes' else 'do not merge'}.",
             "", "The writers got these findings and corrected the pages after the review. No review ran after that, "
             "so examine each item. A `figure` finding is not corrected.", ""] + (findings_md(final["findings"]) or ["None."])
    if final["untested"]:
        body += ["", "Only a test in FreeCAD can decide these statements:", ""] + [f"- {u}" for u in final["untested"]]
    if final["notes"].strip():
        body += ["", final["notes"].strip()]
    body += ["", "## Pages", "", "| Page | Part | Change | Lint | Not verified |", "|---|---|---|---|---|"]
    body += [f"| `{j['page']}` | {c['plan'][j['page']]['role']} | {j['mode']} | {'clean' if j['lint_rc'] == 0 else 'findings'} | "
             f"{len(j['unverified'])} |" for j in jobs]
    if figure_pages:
        import figures
        lines = figures.report_lines(figure_pages)[0]
        body += ["", "## Figures", ""] + lines
    rounds = [h for h in history if h["round"] != "final"]
    for n, h in enumerate(rounds, 1):
        h["round"] = n
    body += ["", "## How the runner worked", "",
             f"- Brief: {len(brief['facts'])} shared facts, {len(brief['terms'])} terms, {len(brief['unknown'])} not established.",
             *[f"- Review {h['round']}: {len(h['findings'])} findings, {sum(f['severity'] == 'must' for f in h['findings'])} of them `must`."
               for h in rounds],
             f"- Cost: ${cost:.2f}.", "", "Review the rendered changes from the preview comment below.", "",
             "<details><summary>Changes, unverified claims and lint for each page</summary>", ""]
    for j in jobs:
        body += draft.page_report(j)
    body += ["</details>", "", "<details><summary>Brief</summary>", "", brief_text(brief), "", "</details>", "",
             "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    labels = ["gypsy"] + (["draft"] if any(j["unverified"] for j in jobs) else []) + \
        (["lint-failed"] if any(j["lint_rc"] for j in jobs) else []) + (["check-findings"] if left else [])
    n = len(jobs)
    work.ensure_labels()
    if a.revise:                                 # the same pull request: new commit, new report
        draft.sh("git", "add", "-A")
        draft.sh("git", "-c", "user.name=sliptonic", "-c", "user.email=shopinthewoods@gmail.com", "commit", "-q", "-m",
                 f"{c['title']}: revise from the review\n\nRevised by gypsy.\n\n"
                 "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        draft.sh("git", "push", "-q", "origin", branch)
        work.gh("pr", "edit", str(pr["number"]), "--body", "\n".join(body)[:64000],
                *(["--add-label", "check-findings"] if left else ["--remove-label", "check-findings"]))
        work.gh("pr", "comment", str(pr["number"]), "--body", work.MARK + "\nThe runner revised the pages: " +
                f"{len(history) - first - 1} review rounds, {len(final['findings'])} findings at the last review. "
                "The description has the new report.")
        draft.sh("git", "checkout", "-q", "--detach", "origin/main")
        return print(f"pull request #{pr['number']} revised")
    url = draft.publish(branch, f"gypsy: {c['title']} ({n} pages)"[:120],
                        f"{c['title']}: {n} pages for issue #{a.issue}", "\n".join(body)[:64000], labels)
    print(f"pull request: {url}")


if __name__ == "__main__":
    main()
