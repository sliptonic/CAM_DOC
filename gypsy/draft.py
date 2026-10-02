#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy draft: rewrite one page for every verdict that names it, lint, and open a pull request.

    python3 gypsy/draft.py PAGE [--facts gypsy/facts/machine.json] [--pr] [--model M] [--dry]

PAGE is relative to modules/ROOT/pages. Without --pr the draft is written on a branch
gypsy/<slug> in the working tree and the lint report printed; with --pr it is also committed,
pushed and opened as a pull request. The working tree must be clean and on main.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


def verdicts_for(page):
    out = []
    for f in glob.glob(os.path.join(HERE, "verdicts", "*.json")):
        v = json.load(open(f, encoding="utf-8"))
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


def lint(page_path):
    r = subprocess.run([sys.executable, os.path.join(HERE, "lint.py"), page_path], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--facts", action="append", default=[])
    ap.add_argument("--pr", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--model", default=os.environ.get("GYPSY_DRAFT_MODEL", ""))
    a = ap.parse_args()
    page = a.page
    page_path = os.path.join(PAGES, page)
    vs = verdicts_for(page)
    if not vs:
        sys.exit(f"no verdicts name {page}")
    if not a.dry:
        if sh("git", "status", "--porcelain").strip():
            sys.exit("working tree not clean")
        if sh("git", "rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
            sys.exit("not on main")
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
    for f in a.facts:
        d = json.load(open(f, encoding="utf-8"))
        facts_commit = d.get("freecad_commit", facts_commit)
        facts.append(f"## {os.path.basename(f)}\n```json\n{json.dumps(d, indent=1)[:60_000]}\n```")
    pending, pending_prs = pending_text(page)
    current = open(page_path, encoding="utf-8").read() if os.path.exists(page_path) else "(page does not exist yet)"
    tmpl = open(os.path.join(HERE, "prompts", "draft.md"), encoding="utf-8").read()
    fields = {
        "page": page,
        "style": open(os.path.join(ROOT, "STYLE.md"), encoding="utf-8").read(),
        "glossary": open(os.path.expanduser("~/FreeCAD/src/Mod/CAM/Roadmap/ADR/ADR-000.md"), encoding="utf-8").read(),
        "verdicts": verdict_text,
        "prs": "\n\n".join(pr_texts),
        "facts_commit": facts_commit or "(none)",
        "facts": "\n\n".join(facts) or "(none)",
        "pending": pending,
        "page_text": current,
    }
    prompt = tmpl
    for k, v in fields.items():
        prompt = prompt.replace(f"${k}", v)
    if a.dry:
        print(prompt)
        print(f"\n[prompt {len(prompt)} chars; PRs {prs}]", file=sys.stderr)
        return
    schema = json.load(open(os.path.join(HERE, "schema", "draft.schema.json")))
    slug = re.sub(r"[^a-z0-9]+", "-", page[:-5].lower()).strip("-")
    branch = f"gypsy/{slug}"
    sh("git", "checkout", "-q", "-B", branch, "main")
    res, run = ask(prompt, a.model, schema)
    runs = [run]
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    open(page_path, "w", encoding="utf-8").write(res["page_text"].rstrip("\n") + "\n")
    report, rc = lint(page_path)
    if rc != 0:
        fix_prompt = (prompt + "\n\n# Your previous draft\n\n" + res["page_text"] +
                      "\n\n# gypsy lint findings on it\n\nFix every finding and return the full page again, "
                      "with the same JSON fields.\n\n" + report)
        res2, run2 = ask(fix_prompt, a.model, schema)
        runs.append(run2)
        res2.setdefault("changes", res["changes"])
        res = res2
        open(page_path, "w", encoding="utf-8").write(res["page_text"].rstrip("\n") + "\n")
        report, rc = lint(page_path)
    cost = sum(r.get("cost_usd") or 0 for r in runs)
    job = {"page": page, "prs": prs, "branch": branch, "changes": res["changes"], "unverified": res["unverified"],
           "figures_wanted": res["figures_wanted"], "notes": res["notes"], "lint_rc": rc, "lint": report,
           "pending_prs": pending_prs, "facts": a.facts, "facts_commit": facts_commit, "runs": runs,
           "cost_usd": cost, "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    jobdir = os.path.join(HERE, "jobs")
    os.makedirs(jobdir, exist_ok=True)
    jobfile = os.path.join(jobdir, f"{slug}.json")
    json.dump(job, open(jobfile, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"draft written: {page_path} on {branch}; lint rc={rc}; cost ${cost:.2f}; job {jobfile}")
    if report:
        print(report)
    if not a.pr:
        return
    labels = ["gypsy"] + (["draft"] if res["unverified"] else []) + (["lint-failed"] if rc else []) + \
             (["needs-capture"] if res["figures_wanted"] else [])
    title = f"gypsy: {page[:-5]} for PRs {', '.join(f'#{p}' for p in prs)}"[:120]
    body = [f"Rewrites `{page}` to STYLE.md for these merged FreeCAD pull requests:", ""]
    body += [f"- FreeCAD/FreeCAD#{c['pr']}: {c['what']}" for c in res["changes"]]
    body += ["", "**Verdicts** (`gypsy/verdicts/`):", ""]
    body += [f"- #{pr}: {p['verdict']}, needs_gui={p['needs_gui']}: {p['reason']}" for _, pr, _, _, p in vs]
    body += ["", "**Not verified in a running FreeCAD:**", ""] + ([f"- {u}" for u in res["unverified"]] or ["- nothing"])
    body += ["", "**Figures wanted:**", ""] + ([f"- {u}" for u in res["figures_wanted"]] or ["- none"])
    if pending_prs:
        body += ["", f"Drafted on top of open gypsy PR(s) {', '.join(f'#{n}' for n in pending_prs)}."]
    body += ["", f"**Lint:** {'clean' if rc == 0 else 'findings remain'}", ""] + (["```", report, "```"] if report else [])
    body += ["", f"Facts from FreeCAD `{facts_commit}`; model {runs[0]['model']}; cost ${cost:.2f}.",
             "", "Preview: the `docs` workflow publishes this PR under `pr-<n>/` on the site.",
             "", "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    if res["notes"]:
        body.insert(2, f"_{res['notes']}_\n")
    sh("git", "add", "-A")
    sh("git", "-c", "user.name=sliptonic", "-c", "user.email=shopinthewoods@gmail.com", "commit", "-q", "-m",
       f"{page[:-5]}: revise for FreeCAD PRs {', '.join(f'#{p}' for p in prs)}\n\nDrafted by gypsy. See the pull request for verdicts and unverified claims.\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
    sh("git", "push", "-q", "-u", "origin", branch)
    url = sh("gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", "\n".join(body),
             *sum((["--label", l] for l in labels), [])).strip()
    sh("git", "checkout", "-q", "main")
    print(f"pull request: {url}")


if __name__ == "__main__":
    main()
