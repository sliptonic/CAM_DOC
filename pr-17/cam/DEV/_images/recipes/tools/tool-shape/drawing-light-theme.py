# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor for the 5 mm Endmill on the light theme: the shape drawing with its
dimensions."""
import os
import sys

PAGE = "tools/tool-shape.adoc"
ALT = "Toolbit Parameter Editor on a light theme, with the endmill shape drawing and the dimensions L, S, H and D"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _shape

    editor = _shape.open_editor()
    shot.widget(editor.form)
    editor.form.reject()
