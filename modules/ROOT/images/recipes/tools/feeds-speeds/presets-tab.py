# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor, Feeds & Speeds tab: three Presets, sorted by Surface speed."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Toolbit Parameter Editor, Feeds & Speeds tab, with three Presets sorted by Surface speed and the Add preset, Edit, Copy and Delete buttons"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    from PySide import QtCore
    import _presets

    editor = _presets.open_presets_tab()
    # The same as a click on the Surface speed column header.
    editor.presets_tab.table.sortByColumn(3, QtCore.Qt.AscendingOrder)
    shot.widget(editor.form)
    editor.form.reject()
