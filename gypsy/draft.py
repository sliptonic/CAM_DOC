#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy draft: revise pages for the verdicts that name them, lint, and open a pull request.

    python3 gypsy/draft.py PAGE [--facts gypsy/facts/machine.json] [--pr] [--model M] [--dry]
    python3 gypsy/draft.py --cluster gypsy/clusters/NAME.yml [--pr] [--model M] [--dry]

A cluster is one cause with all its pages (gypsy/clusters/README.md). Its pages are drafted
together, on one branch, and delivered as one pull request that closes the cluster's issue.

PAGE is relative to modules/ROOT/pages. Without --pr the draft is written on a branch
gypsy/<slug> in the working tree and the lint report printed; with --pr it is also committed,
pushed and opened as a pull request. It runs only in gypsy's own worktree (gypsy/config.py),
which must be clean; it starts from origin/main and leaves the worktree detached there.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import triage  # noqa: E402

HERE = triage.HERE
ROOT = triage.ROOT
PAGES = triage.PAGES
MAX_PR_DIFF = 45_000
MAX_TOTAL_DIFF = 220_000


def sh(*cmd, check=True, **kw):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
    if check and r.returncode != 0:
        sys.exit(f"{' '.join(cmd)}: {r.stderr.strip()[:1500]}")
    return r.stdout


def verdicts_for(page, prs=None):
    """Verdicts that name the page; with prs, only those of these upstream pull requests."""
    out = []
    for f in glob.glob(os.path.join(HERE, "verdicts", "*.json")):
        v = json.load(open(f, encoding="utf-8"))
        if prs is not None and v["pr"] not in prs:
            continue
        for p in v["pages"]:
            if p["page"] == page and p["verdict"] != "no change":
                out.append((v["meta"]["merged_at"], v["pr"], v["meta"]["title"], v["meta"]["merge_commit"], p))
    return sorted(out)


def pr_context(pr, page, smap, cited):
    meta = triage.gh(f"repos/{triage.REPO}/pulls/{pr}")
    files = triage.gh_paged(f"repos/{triage.REPO}/pulls/{pr}/files")
    paths = [f["filename"] for f in files]
    cand, _ = triage.candidates(paths, smap)
    relevant = set(cand.get(page, set()))
    for f in paths:
        base = f.rsplit("/", 1)[-1]
        if any(base in c or f in c for c in cited):
            relevant.add(f)
    if not relevant:
        relevant = {f for f in paths if f.startswith("src/Mod/CAM/") and not f.endswith(triage.SKIP_PATCH)}
    diff, used = [], 0
    for f in files:
        name = f["filename"]
        if name not in relevant or any(n in name for n in triage.NOISE_DIRS):
            continue
        patch = f.get("patch")
        if not patch or name.endswith(triage.SKIP_PATCH):
            diff.append(f"--- {name} ({f['status']}, patch omitted)")
            continue
        if used + len(patch) > MAX_PR_DIFF:
            patch = patch[:max(0, MAX_PR_DIFF - used)] + "\n[... truncated ...]"
        diff.append(f"--- {name} ({f['status']}, +{f['additions']}/-{f['deletions']})\n{patch}")
        used += len(patch)
        if used >= MAX_PR_DIFF:
            break
    body = (meta.get("body") or "").replace("\r", "").strip()
    text = (f"## PR {pr}: {meta['title']}\nMerged {meta['merged_at']} at {meta.get('merge_commit_sha','')}\n\n"
            f"### Description\n{body[:4000] or '(empty)'}\n\n### Diff (files relevant to this page)\n" + "\n".join(diff))
    return text


def pending_text(page):
    """The page as it stands on open gypsy PR branches that touch it."""
    r = subprocess.run(["gh", "pr", "list", "--label", "gypsy", "--state", "open", "--json", "number,headRefName,files"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return "(none)", []
    out, nums = [], []
    for pr in json.loads(r.stdout or "[]"):
        if any(f["path"] == f"modules/ROOT/pages/{page}" for f in pr["files"]):
            sh("git", "fetch", "-q", "origin", pr["headRefName"], check=False)
            t = sh("git", "show", f"origin/{pr['headRefName']}:modules/ROOT/pages/{page}", check=False)
            if t:
                out.append(f"## From open PR #{pr['number']} (branch {pr['headRefName']})\n\n{t}")
                nums.append(pr["number"])
    return ("\n\n".join(out) or "(none)"), nums


def ask(prompt, model, schema):
    cmd = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
           "--disallowedTools", "Bash,Read,Edit,Write,Glob,Grep,WebFetch,WebSearch,Agent,Task"]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"claude: {r.stderr.strip()[:2000]}")
    env = json.loads(r.stdout)
    res = env.get("structured_output") or env.get("result")
    if isinstance(res, str):
        res = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", res.strip()))
    return res, {"cost_usd": env.get("total_cost_usd"), "duration_ms": env.get("duration_ms"),
                 "model": (env.get("modelUsage") and next(iter(env["modelUsage"]))) or model or "default"}


def lint(page_path, since=None):
    cmd = [sys.executable, os.path.join(HERE, "lint.py")] + (["--since", since] if since else []) + [page_path]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode


MODES = {
    "rewrite": "Rewrite the whole page so that it follows STYLE.md.",
    "new": "The page does not exist. Write it as STYLE.md specifies for its page type.",
    "amend": ("AMEND ONLY. Most of this page belongs to other work. Change only the statements that the "
              "listed pull requests make false or incomplete, and add what they introduce. Return every "
              "other line exactly as it is, also a line that does not follow STYLE.md, and keep the "
              "heading structure. The lines you add or change follow STYLE.md. Add the pull request "
              "numbers to `:page-source-pr:` and keep the numbers already there. Set `:page-status: draft` "
              "only when `unverified` is not empty; otherwise leave `:page-status:` as it is."),
}
SIBLING_BUDGET = 70_000


def outline(text):
    return "\n".join(l for l in text.splitlines() if l.startswith(("= ", "== ", "=== ", ":description:")))


def siblings_text(done, budget=SIBLING_BUDGET):
    """The other pages of the change set: full text while the budget lasts, then the outline."""
    if not done:
        return "(none)"
    out = []
    for page, text in done.items():
        if len(text) <= budget:
            out.append(f"## {page}\n\n{text}")
            budget -= len(text)
        else:
            out.append(f"## {page} (outline only)\n\n{outline(text)}")
    return "\n\n".join(out)


def draft_page(page, vs, mode, facts_files, siblings, model, dry=False, base="origin/main"):
    """Draft one page in the working tree. Returns a job entry; with dry, prints the prompt."""
    page_path = os.path.join(PAGES, page)
    smap = triage.load_map()
    prs = sorted({pr for _, pr, _, _, _ in vs})
    cited = [p["reason"] for *_, p in vs]
    pr_texts, total = [], 0
    for pr in prs:
        t = pr_context(pr, page, smap, cited)
        if total + len(t) > MAX_TOTAL_DIFF:
            t = t[:max(0, MAX_TOTAL_DIFF - total)] + "\n[... truncated ...]"
        pr_texts.append(t)
        total += len(t)
    verdict_text = "\n".join(f"- PR {pr} ({m[:10]}, {title}): {p['verdict']}, needs_gui={p['needs_gui']}, "
                             f"sections={p['sections']}. {p['reason']}" for m, pr, title, _, p in vs)
    facts, facts_commit = [], ""
    for f in facts_files:
        d = json.load(open(os.path.join(ROOT, f) if not os.path.isabs(f) else f, encoding="utf-8"))
        facts_commit = d.get("freecad_commit", facts_commit)
        facts.append(f"## {os.path.basename(f)}\n```json\n{json.dumps(d, indent=1)[:60_000]}\n```")
    pending, pending_prs = pending_text(page)
    current = open(page_path, encoding="utf-8").read() if os.path.exists(page_path) else "(page does not exist yet)"
    tmpl = open(os.path.join(HERE, "prompts", "draft.md"), encoding="utf-8").read()
    fields = {
        "page_text": current,
        "page": page,
        "mode": MODES[mode],
        "style": open(os.path.join(ROOT, "STYLE.md"), encoding="utf-8").read(),
        "glossary": open(config.ADR_000, encoding="utf-8").read(),
        "verdicts": verdict_text,
        "prs": "\n\n".join(pr_texts),
        "facts_commit": facts_commit or "(none)",
        "facts": "\n\n".join(facts) or "(none)",
        "pending": pending,
        "siblings": siblings,
    }
    prompt = tmpl
    for k in sorted(fields, key=len, reverse=True):       # $page_text before $page
        prompt = prompt.replace(f"${k}", fields[k])
    if dry:
        print(prompt)
        print(f"\n[{page}: mode {mode}; prompt {len(prompt)} chars; PRs {prs}]", file=sys.stderr)
        return None
    schema = json.load(open(os.path.join(HERE, "schema", "draft.schema.json")))
    since = base if mode == "amend" else None
    res, run = ask(prompt, model, schema)
    runs = [run]
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    open(page_path, "w", encoding="utf-8").write(res["page_text"].rstrip("\n") + "\n")
    report, rc = lint(page_path, since)
    if rc != 0:
        fix_prompt = (prompt + "\n\n# Your previous draft\n\n" + res["page_text"] +
                      "\n\n# gypsy lint findings on it\n\nFix every finding and return the full page again, "
                      "with the same JSON fields.\n\n" + report)
        res2, run2 = ask(fix_prompt, model, schema)
        runs.append(run2)
        res2.setdefault("changes", res["changes"])
        res = res2
        open(page_path, "w", encoding="utf-8").write(res["page_text"].rstrip("\n") + "\n")
        report, rc = lint(page_path, since)
    return {"page": page, "mode": mode, "prs": prs, "changes": res["changes"], "unverified": res["unverified"],
            "figures_wanted": res["figures_wanted"], "notes": res["notes"], "lint_rc": rc, "lint": report,
            "pending_prs": pending_prs, "facts": facts_files, "facts_commit": facts_commit, "runs": runs,
            "cost_usd": sum(r.get("cost_usd") or 0 for r in runs), "verdicts": vs}


def start_clean():
    config.require_own_worktree("draft.py")
    if sh("git", "status", "--porcelain").strip():
        sys.exit("working tree not clean")
    # Start from the published main: the newest verdicts, pages and gypsy code.
    sh("git", "fetch", "-q", "origin", "main")
    sh("git", "checkout", "-q", "--detach", "origin/main")


def publish(branch, title, message, body, labels):
    sh("git", "add", "-A")
    sh("git", "-c", "user.name=sliptonic", "-c", "user.email=shopinthewoods@gmail.com", "commit", "-q", "-m",
       message + "\n\nDrafted by gypsy. See the pull request for verdicts and unverified claims.\n\n"
       "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
    sh("git", "push", "-q", "-u", "--force-with-lease", "origin", branch)
    url = sh("gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body,
             *sum((["--label", l] for l in labels), [])).strip()
    sh("git", "checkout", "-q", "--detach", "origin/main")
    return url


def page_report(job):
    """The pull-request section for one page."""
    out = [f"### `{job['page']}` ({job['mode']})", ""]
    out += [f"- FreeCAD/FreeCAD#{c['pr']}: {c['what']}" for c in job["changes"]]
    out += ["", "Not verified in a running FreeCAD:", ""] + ([f"- {u}" for u in job["unverified"]] or ["- nothing"])
    if job["figures_wanted"]:
        out += ["", "Figures wanted:", ""] + [f"- {u}" for u in job["figures_wanted"]]
    if job["notes"]:
        out += ["", f"_{job['notes']}_"]
    out += ["", f"Lint: {'clean' if job['lint_rc'] == 0 else 'findings remain'}"]
    if job["lint"]:
        out += ["", "```", job["lint"], "```"]
    return out + [""]


def run_cluster(a):
    with open(a.cluster, encoding="utf-8") as fh:
        c = yaml.safe_load(fh)
    slug = os.path.splitext(os.path.basename(a.cluster))[0]
    owned, partial = set(c["prs"]), set(c.get("partial") or {})
    pages = c["pages"]
    plan = [(p, "rewrite", owned | partial) for p in pages.get("rewrite", [])] + \
           [(p, "new", owned) for p in pages.get("new", [])] + \
           [(p, "amend", owned) for p in pages.get("amend", [])]
    if not a.dry:
        start_clean()
    branch = f"gypsy/{slug}"
    done = {}
    for p in pages.get("reference", []):
        done[p] = open(os.path.join(PAGES, p), encoding="utf-8").read()
    if not a.dry:
        sh("git", "checkout", "-q", "-B", branch, "origin/main")
    jobs = []
    for page, mode, prs in plan:
        vs = verdicts_for(page, prs)
        if not vs:
            sys.exit(f"cluster {slug}: no verdict of its pull requests names {page}")
        others = {k: v for k, v in done.items() if k != page}
        budget = SIBLING_BUDGET if mode != "amend" else 0     # an amended page gets outlines only
        job = draft_page(page, vs, mode, c.get("facts") or [], siblings_text(others, budget), a.model, a.dry)
        if a.dry:
            continue
        done[page] = open(os.path.join(PAGES, page), encoding="utf-8").read()
        job["verdicts"] = [[m, pr, t, p["verdict"]] for m, pr, t, _, p in vs]
        jobs.append(job)
        print(f"drafted {page} ({mode}); lint rc={job['lint_rc']}; cost ${job['cost_usd']:.2f}", flush=True)
    if a.dry:
        return
    for entry in c.get("nav") or []:                         # navigation lines for new pages
        nav = os.path.join(ROOT, "modules/ROOT/nav.adoc")
        lines = open(nav, encoding="utf-8").read().split("\n")
        at = next((i for i, l in enumerate(lines) if entry["after"] in l), None)
        if at is None:
            sys.exit(f"cluster {slug}: nav anchor not found: {entry['after']}")
        if entry["line"] not in lines:
            lines.insert(at + 1, entry["line"])
        open(nav, "w", encoding="utf-8").write("\n".join(lines))
    cost = sum(j["cost_usd"] for j in jobs)
    jobdir = os.path.join(HERE, "jobs")
    os.makedirs(jobdir, exist_ok=True)
    jobfile = os.path.join(jobdir, f"{slug}.json")
    json.dump({"cluster": slug, "issue": c.get("issue"), "branch": branch, "pages": jobs, "cost_usd": cost,
               "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")},
              open(jobfile, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"cluster {slug}: {len(jobs)} pages on {branch}; cost ${cost:.2f}; job {jobfile}")
    if not a.pr:
        return
    failed = any(j["lint_rc"] for j in jobs)
    labels = ["gypsy"] + (["draft"] if any(j["unverified"] for j in jobs) else []) + \
             (["lint-failed"] if failed else []) + (["needs-capture"] if any(j["figures_wanted"] for j in jobs) else [])
    all_prs = sorted(owned | partial)
    body = [f"**{c['title']}**: one change set, {len(jobs)} pages. All pages merge together.", ""]
    if c.get("issue"):
        body += [f"Closes #{c['issue']}", ""]
    body += ["| Page | Mode | Upstream PRs | Lint | Not verified | Figures wanted |", "|---|---|---|---|---|---|"]
    body += [f"| `{j['page']}` | {j['mode']} | {len(j['prs'])} | {'clean' if j['lint_rc'] == 0 else 'findings'} | "
             f"{len(j['unverified'])} | {len(j['figures_wanted'])} |" for j in jobs]
    if pages.get("reference"):
        body += ["", "Used as reference, not changed: " + ", ".join(f"`{p}`" for p in pages["reference"]) + "."]
    body += ["", "Review the rendered changes from the preview comment below.", "",
             "<details><summary>Changes, unverified claims and lint for each page</summary>", ""]
    for j in jobs:
        body += page_report(j)
    body += ["</details>", "", f"Upstream pull requests: {', '.join(f'FreeCAD/FreeCAD#{p}' for p in all_prs)}.",
             "", f"Model {jobs[0]['runs'][0]['model']}; cost ${cost:.2f}.",
             "", "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    url = publish(branch, f"gypsy: {c['title']} ({len(jobs)} pages)"[:120],
                  f"{c['title']}: revise {len(jobs)} pages for {len(all_prs)} FreeCAD PRs", "\n".join(body), labels)
    print(f"pull request: {url}")




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?")
    ap.add_argument("--cluster", help="a cluster file; drafts all its pages as one pull request")
    ap.add_argument("--facts", action="append", default=[])
    ap.add_argument("--pr", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--model", default=os.environ.get("GYPSY_DRAFT_MODEL", ""))
    a = ap.parse_args()
    config.require_freecad_tree()
    if a.cluster:
        return run_cluster(a)
    if not a.page:
        ap.error("give a PAGE or --cluster FILE")
    page = a.page
    if not a.dry:
        start_clean()
    vs = verdicts_for(page)
    if not vs:
        sys.exit(f"no verdicts name {page}")
    slug = re.sub(r"[^a-z0-9]+", "-", page[:-5].lower()).strip("-")
    branch = f"gypsy/{slug}"
    if not a.dry:
        sh("git", "checkout", "-q", "-B", branch, "origin/main")
    mode = "rewrite" if os.path.exists(os.path.join(PAGES, page)) else "new"
    job = draft_page(page, vs, mode, a.facts, "(none)", a.model, a.dry)
    if a.dry:
        return
    job["verdicts"] = [[m, pr, t, p["verdict"]] for m, pr, t, _, p in vs]
    job.update(branch=branch, generated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
    jobdir = os.path.join(HERE, "jobs")
    os.makedirs(jobdir, exist_ok=True)
    jobfile = os.path.join(jobdir, f"{slug}.json")
    json.dump(job, open(jobfile, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"draft written: {page} on {branch}; lint rc={job['lint_rc']}; cost ${job['cost_usd']:.2f}; job {jobfile}")
    if job["lint"]:
        print(job["lint"])
    if not a.pr:
        return
    labels = ["gypsy"] + (["draft"] if job["unverified"] else []) + (["lint-failed"] if job["lint_rc"] else []) + \
             (["needs-capture"] if job["figures_wanted"] else [])
    prs = job["prs"]
    body = [f"Revises `{page}` for these merged FreeCAD pull requests.", ""] + page_report(job)
    body += [f"Facts from FreeCAD `{job['facts_commit']}`; model {job['runs'][0]['model']}; cost ${job['cost_usd']:.2f}.",
             "", "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    url = publish(branch, f"gypsy: {page[:-5]} for PRs {', '.join(f'#{p}' for p in prs)}"[:120],
                  f"{page[:-5]}: revise for FreeCAD PRs {', '.join(f'#{p}' for p in prs)}", "\n".join(body), labels)
    print(f"pull request: {url}")


if __name__ == "__main__":
    main()
