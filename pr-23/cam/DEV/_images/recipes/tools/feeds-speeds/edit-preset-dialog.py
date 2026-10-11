# SPDX-License-Identifier: LGPL-2.1-or-later
"""Edit preset dialog for a Preset of a 5mm Endmill that has notes."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Edit preset dialog with the Name field, the material, the op type, the Direct feed and speed group and the Notes group with a short text"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _presets
    from PySide import QtCore
    from Path.Tool.FeedsSpeeds import preset_key
    from Path.Tool.toolbit.ui.presets_tab import _EditPresetDialog

    editor = _presets.open_presets_tab(shot)
    tab = editor.presets_tab
    tab.table.selectRow(tab.table.findItems("Wood", QtCore.Qt.MatchExactly)[0].row())
    # The Edit button opens the dialog with exec_(), which stops the capture. Create the same
    # dialog for the selected Preset and show it without the wait.
    presets = tab._presets()
    index = tab._selected_index()
    diameter, flutes = tab._tool_geometry()
    dialog = _EditPresetDialog(
        presets[index], diameter_mm=diameter, flutes=flutes,
        existing_keys={preset_key(p) for i, p in enumerate(presets) if i != index}, parent=tab,
    )
    dialog.form.show()
    shot.widget(dialog.form)
    dialog.form.reject()
    editor.form.reject()
