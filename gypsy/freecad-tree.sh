#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# gypsy's own FreeCAD tree: a git worktree of your FreeCAD clone, with its own build.
#
#   gypsy/freecad-tree.sh [COMMIT]
#
# Creates the worktree when it does not exist, moves it to COMMIT (default: upstream/main,
# fetched first), updates the submodules, and builds. gypsy reads FreeCAD source and runs
# FreeCAD only from this tree, so the branch and the build of your own clone are not used.
#
# Settings (environment):
#   GYPSY_FREECAD_CLONE   your FreeCAD clone (default ~/FreeCAD)
#   GYPSY_FREECAD_TREE    the worktree gypsy uses (default ~/FreeCAD-gypsy)
#   GYPSY_FREECAD_REMOTE  the remote that is FreeCAD/FreeCAD (default upstream)
#   GYPSY_JOBS            parallel build jobs (default: three quarters of the processors)
set -euo pipefail
CLONE=${GYPSY_FREECAD_CLONE:-$HOME/FreeCAD}
TREE=${GYPSY_FREECAD_TREE:-$HOME/FreeCAD-gypsy}
REMOTE=${GYPSY_FREECAD_REMOTE:-upstream}
JOBS=${GYPSY_JOBS:-$(( $(nproc) * 3 / 4 ))}
COMMIT=${1:-}

git -C "$CLONE" fetch -q "$REMOTE" main
[ -n "$COMMIT" ] || COMMIT=$REMOTE/main

if [ ! -e "$TREE/.git" ]; then
  git -C "$CLONE" worktree add --detach "$TREE" "$COMMIT"
else
  if [ -n "$(git -C "$TREE" status --porcelain --ignore-submodules)" ]; then
    echo "freecad-tree: $TREE has local changes; gypsy does not change this tree by hand" >&2
    exit 1
  fi
  git -C "$TREE" checkout -q --detach "$COMMIT"
fi
git -C "$TREE" submodule update --init --recursive -q

if [ ! -f "$TREE/build/build.ninja" ]; then
  cmake -S "$TREE" -B "$TREE/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DFREECAD_USE_CCACHE=ON -DBUILD_TEST=OFF -DENABLE_DEVELOPER_TESTS=OFF
fi
nice -n 10 cmake --build "$TREE/build" -j "$JOBS"
echo "freecad-tree: $TREE at $(git -C "$TREE" rev-parse --short=11 HEAD), $TREE/build/bin/FreeCAD"
