# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number dialog for a Tool Bit from All Tools, which has no library tool number. The Job
has one Tool Controller with Tool Number 1, so the default value is 2."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Tool Number dialog with the label Tool number for 5mm Drill and the default value 2"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "All Tools")
    _selector.capture_tool_number(shot, dock, "toolbit://5mm_Drill")
    dock.form.reject()
