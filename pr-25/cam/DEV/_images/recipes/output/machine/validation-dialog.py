# SPDX-License-Identifier: LGPL-2.1-or-later
"""Validation dialog of the Machine Editor for a new 3-axis Machine with a Post and no
Toolheads: one warning."""
PAGE = "output/machine.adoc"
ALT = "Validation dialog with one warning, and the details shown"


def capture(shot):
    from PySide import QtWidgets
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    # Validate opens its dialog with exec_(), which stops the capture. Show it without the wait.
    QtWidgets.QMessageBox.exec_ = QtWidgets.QMessageBox.show

    dialog = MachineEditorDialog()
    dialog.show()
    types = dialog.type_combo                          # axes and a Post, so that one finding stays
    types.setCurrentIndex(types.findText("3-Axis Mill (XYZ)"))
    posts = dialog.post_processor_combo
    posts.setCurrentIndex(posts.findText("linuxcnc"))
    dialog.validate_button.click()
    shot.settle()
    box = dialog.findChild(QtWidgets.QMessageBox)
    for button in box.buttons():
        if box.buttonRole(button) == QtWidgets.QMessageBox.ActionRole:   # Show Details…
            button.click()
    shot.widget(box)
    box.close()
    dialog.reject()
