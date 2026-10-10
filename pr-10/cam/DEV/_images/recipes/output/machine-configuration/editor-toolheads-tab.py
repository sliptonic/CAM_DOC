# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor, Toolheads tab, after one click on Add Toolhead."""
PAGE = "output/machine-configuration.adoc"
ALT = "Machine Editor, Toolheads tab, with one rotary Toolhead and the Add Toolhead button"


def capture(shot):
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    dialog.tabs.setCurrentWidget(dialog.toolheads_tab)
    dialog.add_toolhead_button.click()
    shot.widget(dialog)
    dialog.reject()
