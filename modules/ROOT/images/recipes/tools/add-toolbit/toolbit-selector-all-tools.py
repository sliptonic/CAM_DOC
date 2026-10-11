# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector that the Add Toolbit command opens, with All Tools in the library drop-down."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector with All Tools selected, the list of Tool Bits and the buttons Open Library Editor, Add to Job and Close"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "All Tools")
    shot.widget(dock.form)
    dock.form.reject()
