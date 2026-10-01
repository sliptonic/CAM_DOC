#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy triage: stage 1 (source map) and stage 2 (verdict) for merged FreeCAD PRs.

    python3 gypsy/triage.py PR [PR ...] [--dry] [--model MODEL] [--force]
    python3 gypsy/triage.py --since 2026-08-15          # every merged Mod: CAM PR since a date

Writes gypsy/verdicts/<pr>.json. --dry prints the prompt and writes nothing. Existing verdicts
are kept unless --force. Needs `gh` (logged in, read-only use) and `claude` (logged in).
"""
import argparse, datetime, fnmatch, json, os, re, subprocess, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGES = os.path.join(ROOT, "modules/ROOT/pages")
REPO = "FreeCAD/FreeCAD"
MAX_DIFF = 160_000       # characters of diff sent to the model
MAX_FILE_PATCH = 12_000  # per-file cap before truncation
SKIP_PATCH = (".ts", ".qm", ".po", ".svg", ".png", ".fcstd", ".FCStd", ".json")
NOISE_DIRS = ("translations/", "Resources/translations/")


def gh(path, **params):
    cmd = ["gh", "api", "-X", "GET", path]
    for k, v in params.items():
        cmd += ["-f", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"gh api {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def gh_paged(path):
    out, page = [], 1
    while True:
        chunk = gh(path, per_page=100, page=page)
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def load_map():
    p = os.path.join(HERE, "source-map.yml")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("map", [])


def candidates(files, smap):
    found, unmapped = {}, []
    for f in files:
        hit = False
        for entry in smap:
            pats = entry["match"] if isinstance(entry["match"], list) else [entry["match"]]
            if any(fnmatch.fnmatch(f, p) or f.startswith(p.rstrip("*")) for p in pats):
                hit = True
                for page in entry.get("pages", []):
                    found.setdefault(page, set()).add(f)
        if not hit and f.startswith("src/Mod/CAM/") and not any(n in f for n in NOISE_DIRS):
            unmapped.append(f)
    return found, unmapped


def page_list():
    out = []
    for d, _, fs in os.walk(PAGES):
        for f in fs:
            if f.endswith(".adoc"):
                out.append(os.path.relpath(os.path.join(d, f), PAGES))
    return sorted(out)


def page_excerpt(rel):
    p = os.path.join(PAGES, rel)
    if not os.path.exists(p):
        return f"### {rel}\n(no such page)\n"
    lines = open(p, encoding="utf-8").read().split("\n")
    keep = [l for l in lines[:25] if l.startswith(("=", ":"))]
    keep += [l for l in lines if l.startswith("== ") or l.startswith("=== ")]
    return f"### {rel}\n" + "\n".join(keep) + "\n"


def linked_issues(texts):
    nums = set()
    for t in texts:
        nums |= {int(n) for n in re.findall(r"(?:#|issues/)(\d{4,6})", t or "")}
    out = []
    for n in sorted(nums):
        try:
            it = gh(f"repos/{REPO}/issues/{n}")
        except SystemExit:
            continue
        if "pull_request" in it:
            out.append(f"- #{n} (pull request): {it['title']}")
        else:
            body = (it.get("body") or "").strip().replace("\r", "")
            out.append(f"- #{n}: {it['title']}\n  " + body[:1200].replace("\n", "\n  "))
    return "\n".join(out) or "(none)"


def build_prompt(pr, smap, tmpl):
    meta = gh(f"repos/{REPO}/pulls/{pr}")
    if not meta.get("merged_at"):
        sys.exit(f"PR {pr} is not merged")
    commits = gh_paged(f"repos/{REPO}/pulls/{pr}/commits")
    files = gh_paged(f"repos/{REPO}/pulls/{pr}/files")
    paths = [f["filename"] for f in files]
    cand, unmapped = candidates(paths, smap)
    diff, used = [], 0
    for f in files:
        name = f["filename"]
        if any(n in name for n in NOISE_DIRS):
            continue
        patch = f.get("patch")
        if not patch or name.endswith(SKIP_PATCH):
            diff.append(f"--- {name} ({f['status']}, +{f['additions']}/-{f['deletions']}, patch omitted)")
            continue
        if len(patch) > MAX_FILE_PATCH:
            patch = patch[:MAX_FILE_PATCH] + "\n[... truncated ...]"
        block = f"--- {name} ({f['status']}, +{f['additions']}/-{f['deletions']})\n{patch}"
        if used + len(block) > MAX_DIFF:
            diff.append(f"--- {name}: omitted, diff budget exhausted")
            continue
        diff.append(block)
        used += len(block)
    commit_text = "\n".join(f"- {c['sha'][:10]} {c['commit']['message'].strip().splitlines()[0]}"
                            + ("" if len(c['commit']['message'].strip().splitlines()) < 2 else
                               "\n  " + "\n  ".join(c['commit']['message'].strip().splitlines()[1:]))
                            for c in commits)
    body = (meta.get("body") or "").replace("\r", "")
    fields = {
        "pr": str(pr),
        "title": meta["title"],
        "merged_at": meta["merged_at"],
        "base": meta["base"]["ref"],
        "merge_commit": meta.get("merge_commit_sha") or "",
        "labels": ", ".join(l["name"] for l in meta.get("labels", [])) or "(none)",
        "body": body.strip() or "(empty)",
        "commits": commit_text or "(none)",
        "issues": linked_issues([body, commit_text]),
        "files": "\n".join(f"- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})" for f in files),
        "candidates": "\n".join(f"- {p}  <- {', '.join(sorted(fs))}" for p, fs in sorted(cand.items())) or "(none)",
        "page_excerpts": "\n".join(page_excerpt(p) for p in sorted(cand)) or "(none)",
        "page_list": "\n".join(page_list()),
        "diff": "\n".join(diff),
    }
    prompt = tmpl
    for k, v in fields.items():
        prompt = prompt.replace(f"${k}", v)
    info = {"merge_commit": fields["merge_commit"], "merged_at": fields["merged_at"],
            "title": fields["title"], "candidates": sorted(cand), "unmapped_by_map": unmapped,
            "files": len(files)}
    return prompt, info


def ask(prompt, model, schema):
    cmd = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
           "--disallowedTools", "Bash,Read,Edit,Write,Glob,Grep,WebFetch,WebSearch,Agent,Task"]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"claude: {r.stderr.strip()[:2000]}")
    env = json.loads(r.stdout)
    result = env.get("structured_output") or env.get("result")
    if isinstance(result, str):
        result = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", result.strip()))
    return result, {"model": env.get("model") or model, "cost_usd": env.get("total_cost_usd"),
                    "duration_ms": env.get("duration_ms"), "session": env.get("session_id")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prs", nargs="*", type=int)
    ap.add_argument("--since", help="merged on or after this date (YYYY-MM-DD)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default=os.environ.get("GYPSY_TRIAGE_MODEL", ""))
    a = ap.parse_args()
    prs = list(a.prs)
    if a.since:
        q = f'repo:{REPO} is:pr is:merged label:"Mod: CAM" merged:>={a.since}'
        items, page = [], 1
        while True:
            res = gh("search/issues", q=q, per_page=100, page=page)
            items += res["items"]
            if len(items) >= res["total_count"] or not res["items"]:
                break
            page += 1
        prs += sorted(it["number"] for it in items)
    if not prs:
        sys.exit("no PRs given")
    smap = load_map()
    tmpl = open(os.path.join(HERE, "prompts/verdict.md"), encoding="utf-8").read()
    schema = json.load(open(os.path.join(HERE, "schema/verdict.schema.json")))
    schema.pop("$schema", None)
    outdir = os.path.join(HERE, "verdicts")
    os.makedirs(outdir, exist_ok=True)
    for pr in prs:
        out = os.path.join(outdir, f"{pr}.json")
        if os.path.exists(out) and not a.force and not a.dry:
            print(f"{pr}: verdict exists, skip")
            continue
        prompt, info = build_prompt(pr, smap, tmpl)
        if a.dry:
            print(prompt)
            print(f"\n[prompt {len(prompt)} chars; candidates {info['candidates']}; unmapped {info['unmapped_by_map']}]", file=sys.stderr)
            continue
        verdict, run = ask(prompt, a.model, schema)
        verdict["meta"] = dict(info, **run, generated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(verdict, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        kinds = ", ".join(f"{p['page']}={p['verdict']}" for p in verdict.get("pages", [])) or "no pages"
        print(f"{pr}: {kinds}  [{run.get('cost_usd')} USD]")


if __name__ == "__main__":
    main()
