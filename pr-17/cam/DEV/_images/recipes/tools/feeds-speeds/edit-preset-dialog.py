# SPDX-License-Identifier: LGPL-2.1-or-later
"""Edit preset dialog: the Edit button for a Preset with a name, a material, an op type and
notes."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Edit preset dialog with the name Finish, the material 6061, the op type profile and the text Use coolant in the Notes group box"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    from PySide import QtWidgets
    import Path.Tool.toolbit.ui.presets_tab as presets_tab
    import _presets

    # exec_() waits for the user, which stops the capture. Show the dialog without the wait,
    # and return as Cancel does.
    def exec_(dialog):
        dialog.form.show()
        shot.widget(dialog.form)
        dialog.form.close()
        return QtWidgets.QDialog.Rejected

    presets_tab._EditPresetDialog.exec_ = exec_

    editor = _presets.open_presets_tab()
    _presets.select_preset(editor, "Finish")
    editor.presets_tab.edit_button.click()
    editor.form.reject()
