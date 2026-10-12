# SPDX-License-Identifier: LGPL-2.1-or-later
"""Feeds & Speeds tab of the Toolbit Parameter Editor, for a library Tool Bit with two Presets."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Feeds & Speeds tab of the Tool Bit editor with two Presets, the Notes column and the buttons Add preset, Edit, Copy and Delete"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _presets

    editor = _presets.open_presets_tab(shot)
    shot.widget(editor.form)
    editor.form.reject()
