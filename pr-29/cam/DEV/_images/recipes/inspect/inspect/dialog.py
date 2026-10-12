# SPDX-License-Identifier: LGPL-2.1-or-later
"""CAM Inspect dialog for a Profile operation, as the command opens it."""
import os
import sys

PAGE = "inspect/inspect.adoc"
ALT = "CAM Inspect dialog with the G-code of a Profile operation, line numbers, the note about the units, and the Raw checkbox"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _inspect

    op = _inspect.profile(shot)
    dialog = _inspect.inspect(shot, op)
    shot.widget(dialog)
    dialog.reject()
