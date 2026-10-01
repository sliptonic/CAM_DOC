# gypsy

Keeps the CAM documentation on `main` current with FreeCAD `main`. Modelled on
[campr-bot](https://github.com/Connor9220/campr): a local machine, a timer, a job queue, nothing
merged without a person. Design record: the user's research notes, `gypsy_design.md`.

## Pipeline

1. **Watch.** A merged FreeCAD pull request with the `Mod: CAM` label or touching `src/Mod/CAM/`.
2. **Triage** (`triage.py`). Stage 1 maps changed files to candidate pages (`source-map.yml`).
   Stage 2 asks a model for a verdict per page (`prompts/verdict.md`, `schema/verdict.schema.json`):
   `no change`, `revise`, `new page`, `capture only`, with `needs_gui`. The verdict is committed to
   `verdicts/<pr>.json` by direct push so "nothing to do" is on record.
3. **Draft.** For `revise` / `new page` / `capture only`: rewrite the page to `STYLE.md`. Jobs
   with `needs_gui` run FreeCAD at the merge commit off screen and exercise the change first;
   jobs without it draft text-only and set `:page-status: draft`.
4. **Capture.** Figures come from replayable recipes under `modules/ROOT/images/recipes/`, with a
   `modules/ROOT/images/manifest.yml` entry each.
5. **Lint** (`lint.py`). Mechanical STYLE.md checks; one fix attempt, then the PR opens anyway
   with `lint-failed`.
6. **Pull request.** One per upstream PR, own branch off `main`, labels `gypsy` /
   `needs-capture` / `conflict` / `lint-failed`. A person merges. Merging deploys the site.

## Commands

```
python3 gypsy/triage.py 32711 32903          # verdicts for these PRs
python3 gypsy/triage.py --since 2026-08-15   # every merged Mod: CAM PR since the date
python3 gypsy/triage.py 32711 --dry          # print the stage-2 prompt, write nothing
python3 gypsy/lint.py modules/ROOT/pages/operations/drilling.adoc
```

`GYPSY_TRIAGE_MODEL` selects the stage-2 model. Needs `gh` and `claude`, both logged in; triage
uses `gh` read-only and gives the model no tools.

## Files

| Path | What |
|---|---|
| `source-map.yml` | stage 1: source path globs → pages; proposed pages for commands without one |
| `prompts/verdict.md` | stage 2 prompt, `$placeholders` filled by `triage.py` |
| `schema/verdict.schema.json` | structured-output schema for the verdict |
| `verdicts/` | one JSON per upstream PR, with `meta` (merge commit, candidates, model, cost) |
| `vocabulary.yml` | ADR-000 avoid lists and STYLE.md §2 banned words, as regexes |
| `lint.py` | the mechanical checks |

Not yet written: the drafter, the capture recipes and manifest, the bot runner and systemd units.
