# gypsy

Keeps the CAM documentation on `main` current with FreeCAD `main`. Modelled on
[campr-bot](https://github.com/Connor9220/campr): a local machine, a timer, a job queue, nothing
merged without a person. Design record: the user's research notes, `gypsy_design.md`.

## Pipeline

A **verdict** is a request to change the documentation (`verdicts/<id>.json`). A **unit of work**
is one or more verdicts that a person approves as one issue and that one pull request delivers.

1. **Triage** (`triage.py`). Reads one merged FreeCAD pull request and writes a verdict: a
   summary, the `intent` (what the documentation must achieve as a whole), and for each page a
   verdict (`no change`, `revise`, `new page`, `capture only`) and a `role` (`primary`,
   `supporting`, `capture`). It records the first FreeCAD release that contains the change.
   A change gets text only when a reader acts on it. Other sources can write a verdict too.
2. **Propose** (`propose.py`). `survey` groups all open verdicts into ranked units. `make` writes
   the issue for a set of verdicts: summary, goals, questions for a person, the part of each
   page, what is not documented, and the work definition.
3. **A person** guides with comments and sets the label `approved`.
4. **Run** (`run.py`, started by `work.py run`). The runner takes the unit to a pull request:
   - **brief**: one agent reads the FreeCAD source and writes the facts and terms that all
     pages share;
   - **draft**: one writer for each page, in parallel, with the goals, the plan and the brief;
   - **check**: one agent compares the pages with the goals, the plan, the brief, the source and
     each other;
   - **revise**: the writers correct the findings; check and revise repeat for a fixed number of
     rounds;
   - **lint** (`lint.py`) after each draft and revision;
   - **figures** (`figures.py`): an agent writes a recipe for each wanted figure, runs it with
     `capture.py`, looks at the image and puts it into the page;
   - **pull request**: reports each goal of the issue as achieved or not, the open findings of
     the last check, and the pages. Branch `gypsy/issue-N`. A person merges, and the merge
     closes the issue and deploys the site.

An issue without goals (made by `work.py propose`) still runs through `draft.py --issue N`.

## Work issues and labels

Issues control the work (`work.py`). A pull request is for page changes, or for a change to
gypsy and the tools. Process state does not go through a pull request.

- A work issue is one cause with all its pages. Its body has the work definition in a YAML
  block that gypsy reads and that a person can edit. For work after the backlog, the cause is
  one upstream pull request.
- Labels are the decisions. gypsy sets `proposed`. Only a person sets `approved`. gypsy sets
  `blocked` when it cannot continue, with a comment that says why.
- The other states need no label: approved without a pull request is in draft; an open pull
  request is in review; closed is delivered, or rejected when closed as not planned.
- Comments are guidance, not decisions. Each comment of a person goes to the drafter.
- The backlog is not a set of issues. `status.py` reports it. gypsy proposes an issue to
  decrease it, and a person approves.

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
python3 gypsy/status.py                                      # state of every page, ranked
python3 gypsy/status.py --page job/job.adoc                  # one page in detail
python3 gypsy/lint.py --since origin/main PAGE.adoc           # only the lines changed since main
python3 gypsy/work.py                                        # open work issues and what each waits for
python3 gypsy/work.py propose --upstream 33254               # propose one upstream PR as work
python3 gypsy/work.py propose FILE.yml                       # propose a set of upstream PRs as work
python3 gypsy/work.py run                                    # draft the next approved issue; in ~/CAM_DOC-gypsy
python3 gypsy/figures.py --list                              # figures that the drafts want
python3 gypsy/figures.py --pr                                # make them; in ~/CAM_DOC-gypsy
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
| `status.py` | step 1 of an iteration: one record for each page (pending verdicts, lint, status, figures, links in, cluster), ranked by need x how central the page is |
| `importance.yml` | optional: `page: weight` to replace the weight that `status.py` takes from the links |
| `figures.py`, `prompts/figures.md` | the figure stage: an agent writes and runs a recipe for each wanted figure |
| `capture.py`, `capture_host.py` | the figure runner, and the part of it that runs inside FreeCAD |

Not yet written: the bot runner and systemd units. The recipes do not use GuiDriver yet; they
create Jobs and operations by script and cannot drive a task panel through its controls.
