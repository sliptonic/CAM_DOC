# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector dialog with the All Tools entry selected in the library list."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Toolbit Selector dialog with All Tools selected, without the sort list and without numbers in the rows"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "All Tools")
    shot.widget(dock.form)
    dock.form.reject()
