# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor for a new Machine, Postprocessor tab, linuxcnc Post selected, moved down to
the end of the property list, where the Job-scope properties are."""
PAGE = "output/machine.adoc"
ALT = "Machine Editor, Postprocessor tab, moved down to the last properties of the linuxcnc Post"


def capture(shot):
    from PySide import QtWidgets
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    dialog.tabs.setCurrentWidget(dialog.postprocessor_tab)
    combo = dialog.post_processor_combo
    combo.setCurrentIndex(combo.findText("linuxcnc"))
    shot.settle()
    # The Job-scope properties are at the end of the list. Move the area to its end.
    scroll = dialog.postprocessor_tab.findChild(QtWidgets.QScrollArea)
    bar = scroll.verticalScrollBar()
    bar.setValue(bar.maximum())
    shot.widget(dialog)
    dialog.reject()
