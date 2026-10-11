# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number dialog for a library tool number that is in use: the 3.175mm Endmill is tool 1
of the Default library, and the Tool Controller of the new Job has Tool Number 1."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Tool Number dialog with the text Tool number 1 is already used by TC: 5mm Endmill, above the label Tool number for 3.175mm Endmill"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector

    dock = _selector.open_selector(shot, "Default")
    _selector.capture_tool_number(shot, dock, "toolbit://3.175mm_Endmill")
    dock.form.reject()
