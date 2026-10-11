# SPDX-License-Identifier: LGPL-2.1-or-later
"""CAM Inspect dialog with Raw set, for a Profile operation that links to a Work Plane."""
import os
import sys

PAGE = "inspect/inspect.adoc"
ALT = "CAM Inspect dialog with Raw set for an Operation on a Work Plane; the note has one more line with the origin of the frame"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _inspect

    op = _inspect.profile(shot, tilted=True)
    dialog = _inspect.inspect(shot, op, raw=True)
    shot.widget(dialog)
    dialog.reject()
