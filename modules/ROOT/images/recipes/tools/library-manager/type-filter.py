# SPDX-License-Identifier: LGPL-2.1-or-later
"""Open type filter of the Library Manager, for a library that has a Tool Bit of each Drill
subtype."""
import os
import sys

PAGE = "tools/library-manager.adoc"
ALT = "Open type filter of the Library Manager, with the subtypes Jobber, Spot and Stub below the Drill type, with an indent"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _manager

    _manager.add_drill_subtypes()
    editor = _manager.open_manager(shot)
    combo = editor.browser._tool_type_combo
    combo.showPopup()
    shot.settle()
    # The list of the drop-down is a window of its own. Capture this window.
    shot.widget(combo.view().window())
    combo.hidePopup()
    editor.form.reject()
