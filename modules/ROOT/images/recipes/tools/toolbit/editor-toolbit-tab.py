# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor, Toolbit tab, for the 5 mm Endmill of the Default library."""
import os
import sys

PAGE = "tools/toolbit.adoc"
ALT = "Toolbit Parameter Editor, Toolbit tab, for a 5 mm Endmill, with the properties and the shape drawing"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _toolbit

    editor = _toolbit.open_editor()
    shot.widget(editor.form)
    editor.form.reject()
