# SPDX-License-Identifier: LGPL-2.1-or-later
"""Edit preset dialog for the Preset "Alu profile" of a library Tool Bit."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Edit preset dialog with the Name field, the material, the op type, the feed and speed values and the Notes group"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _presets
    from PySide import QtCore
    from Path.Tool.toolbit.ui.presets_tab import _EditPresetDialog

    editor = _presets.open_presets_tab(shot)
    tab = editor.presets_tab
    tab.table.selectRow(tab.table.findItems("Alu profile", QtCore.Qt.MatchExactly)[0].row())
    # The Edit button opens the dialog with exec_(), which stops the capture. Create the same
    # dialog for the selected Preset and show it without the wait.
    diameter, flutes = tab._tool_geometry()
    dialog = _EditPresetDialog(tab._presets()[tab._selected_index()],
                               diameter_mm=diameter, flutes=flutes, parent=tab)
    dialog.form.show()
    shot.widget(dialog.form)
    dialog.form.reject()
    editor.form.reject()
