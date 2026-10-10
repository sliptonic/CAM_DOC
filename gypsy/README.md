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
6. **Pull request.** One per cluster (`clusters/README.md`): one cause with all its pages, proposed
   as an issue and confirmed by a person. For work after the backlog a cluster is one upstream
   PR. Own branch off `main`, labels `gypsy` /
   `needs-capture` / `conflict` / `lint-failed`. A person merges. Merging deploys the site.

## Worktrees

gypsy works in its own git worktrees. It does not change the branch, the files or the build of
the trees you develop in (`gypsy/config.py`).

| Tree | What | Made by |
|---|---|---|
| `~/CAM_DOC-gypsy` | This repository, detached at `origin/main`. `draft.py` makes its `gypsy/<page>` branches here and runs nowhere else. | `git worktree add --detach ../CAM_DOC-gypsy origin/main`, then `npm ci` there |
| `~/FreeCAD-gypsy` | FreeCAD at `upstream/main` or at a merge commit, with its own build. Source of ADR-000 and of the FreeCAD that `capture.py` runs. | `gypsy/freecad-tree.sh [COMMIT]` |

gypsy runs the code that is on `origin/main`. Develop gypsy in your usual work tree, merge, and
the next run in `~/CAM_DOC-gypsy` uses the new code. `lint.py`, `capture.py`, `triage.py --dry`
and `tools/render_diff.py` change no branch and run in any tree. `GYPSY_FREECAD_TREE` selects a
different FreeCAD tree; `GYPSY_FREECAD` or `--freecad` selects a different FreeCAD build for
`capture.py`.

## Commands

```
python3 gypsy/triage.py 32711 32903          # verdicts for these PRs
python3 gypsy/triage.py --since 2026-08-15   # every merged Mod: CAM PR since the date
python3 gypsy/triage.py 32711 --dry          # print the stage-2 prompt, write nothing
python3 gypsy/lint.py modules/ROOT/pages/operations/drilling.adoc
python3 gypsy/lint.py --since origin/main PAGE.adoc           # only the lines changed since main
python3 gypsy/draft.py --cluster gypsy/clusters/machine-post.yml --pr   # in ~/CAM_DOC-gypsy
python3 gypsy/capture.py output/machine/editor-machine-tab   # replay one figure recipe
python3 gypsy/capture.py --all                               # replay every recipe
python3 tools/render_diff.py --build --against main          # rendered diff of the working tree
```

`capture.py` runs FreeCAD (`--freecad` or `GYPSY_FREECAD`) on its own Xvfb display with an empty
user directory. A recipe is `modules/ROOT/images/recipes/<page>/<what>.py`; it sets `PAGE` and
`ALT` and defines `capture(shot)`. The image goes to `modules/ROOT/images/<page>/<what>.png` and
the manifest entry is replaced. Models are entries in `models/models.json`.

`render_diff.py` writes `<page>.diff.html` beside each changed page of `build/site` and the list
`build/site/changes.html`. CI runs it on every pull request and puts the list in the preview
comment.

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
| `capture.py`, `capture_host.py` | the figure runner, and the part of it that runs inside FreeCAD |

Not yet written: the bot runner and systemd units. The recipes do not use GuiDriver yet; they
create Jobs and operations by script and cannot drive a task panel through its controls.
