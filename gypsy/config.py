# SPDX-License-Identifier: LGPL-2.1-or-later
"""Where gypsy works. gypsy has its own git worktrees, so that it does not change the branch,
the files or the build of the trees you develop in.

    CAM_DOC   ~/CAM_DOC-gypsy    a worktree of this repository, detached at origin/main
    FreeCAD   ~/FreeCAD-gypsy    a worktree of your FreeCAD clone with its own build
                                 (gypsy/freecad-tree.sh creates and builds it)

GYPSY_FREECAD_TREE selects a different FreeCAD tree.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FREECAD_TREE = os.path.expanduser(os.environ.get("GYPSY_FREECAD_TREE", "~/FreeCAD-gypsy"))
FREECAD_BIN = os.path.join(FREECAD_TREE, "build/bin/FreeCAD")
FREECAD_CMD = os.path.join(FREECAD_TREE, "build/bin/FreeCADCmd")
ADR_000 = os.path.join(FREECAD_TREE, "src/Mod/CAM/Roadmap/ADR/ADR-000.md")


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def in_own_worktree():
    """True when this copy of the repository is a linked worktree, not the main work tree."""
    return os.path.realpath(_git("rev-parse", "--git-dir")) != \
        os.path.realpath(_git("rev-parse", "--git-common-dir"))


def require_own_worktree(what):
    """Stop a command that changes branches or commits when it runs in the main work tree."""
    if in_own_worktree():
        return
    sys.exit(f"gypsy: {what} changes the checked-out branch, so it does not run in the main "
             f"work tree ({ROOT}).\nRun it in the gypsy worktree:\n"
             f"  git worktree add --detach ../CAM_DOC-gypsy origin/main   # one time\n"
             f"  cd ../CAM_DOC-gypsy && python3 gypsy/{what} ...")


def require_freecad_tree():
    if not os.path.isdir(os.path.join(FREECAD_TREE, "src/Mod/CAM")):
        sys.exit(f"gypsy: no FreeCAD tree at {FREECAD_TREE}; run gypsy/freecad-tree.sh")
