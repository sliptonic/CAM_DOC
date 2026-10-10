# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor as it opens for a new Machine, Machine tab."""
PAGE = "output/machine.adoc"
ALT = "Machine Editor, Machine tab, for a new Machine"


def capture(shot):
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    shot.widget(dialog)
    dialog.reject()
