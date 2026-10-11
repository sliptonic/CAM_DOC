# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector dialog with the Default Tool Library selected in the library list."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector dialog with the Default Tool Library selected, where each row shows the number, the label, the summary and the shape icon of a Tool Bit"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "Default")
    shot.widget(dock.form)
    dock.form.reject()
