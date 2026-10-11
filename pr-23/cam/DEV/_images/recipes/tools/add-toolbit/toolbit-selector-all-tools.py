# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector with All Tools selected: the tool list has no library tool numbers."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector with All Tools selected in the library drop-down; the tool list shows no tool numbers"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "All Tools")
    shot.widget(dock.form)
    dock.form.reject()
