# SPDX-License-Identifier: LGPL-2.1-or-later
"""3D view with lines selected in CAM Inspect, for a Profile operation on a tilted Work Plane."""
import os
import sys

PAGE = "inspect/inspect.adoc"
ALT = "3D view of a Profile operation on a tilted Work Plane, with highlighted moves and the Tool Bit shape along the Tool Axis"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _inspect

    op = _inspect.profile(shot, tilted=True)
    dialog = _inspect.inspect(shot, op)
    dialog.chkTool.setChecked(True)                # show the Tool Bit shape
    _inspect.select_lines(dialog, 6, 38)           # the first pass along the tilted face
    shot.view(1200, 900)
    dialog.reject()
