# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor for the 5 mm Endmill on the dark theme: the shape drawing with the
darker artwork and the dimension color of a dark theme."""
import os
import sys

PAGE = "tools/tool-shape.adoc"
ALT = "Toolbit Parameter Editor on a dark theme, with the darker endmill artwork and light dimensions"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _shape

    _shape.select_theme(shot, "FreeCAD Dark")
    editor = _shape.open_editor()
    shot.widget(editor.form)
    editor.form.reject()
