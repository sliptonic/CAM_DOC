# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector that the Add Toolbit command opens, with the Tool Library that FreeCAD
supplies in the library drop-down."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector with a Tool Library selected, the library tool number in each list entry and the sort drop-down"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "Default")
    shot.widget(dock.form)
    dock.form.reject()
