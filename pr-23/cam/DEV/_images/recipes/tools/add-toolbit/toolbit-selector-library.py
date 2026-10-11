# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector with the shipped Default library selected: each entry of the tool list has
its library tool number."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector with the Default library selected in the library drop-down; each entry of the tool list shows its tool number, label, summary and shape icon"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "Default")
    shot.widget(dock.form)
    dock.form.reject()
