# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor, Toolheads tab, after one click on Add Toolhead: a rotary Toolhead with the
default Max RPM and Min RPM."""
PAGE = "output/machine.adoc"
ALT = "Machine Editor, Toolheads tab, with one rotary Toolhead and its Max RPM and Min RPM"


def capture(shot):
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    dialog.tabs.setCurrentWidget(dialog.toolheads_tab)
    dialog.add_toolhead_button.click()
    shot.widget(dialog)
    dialog.reject()
