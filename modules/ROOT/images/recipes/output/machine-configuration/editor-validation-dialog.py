# SPDX-License-Identifier: LGPL-2.1-or-later
"""Validation dialog of the Machine Editor for a new Machine with a Post: no axes (error), no
Toolheads (warning)."""
PAGE = "output/machine-configuration.adoc"
ALT = "Validation dialog with one error and one warning, and the details shown"


def capture(shot):
    from PySide import QtWidgets
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    # Validate opens its dialog with exec_(), which stops the capture. Show it without the wait.
    QtWidgets.QMessageBox.exec_ = QtWidgets.QMessageBox.show

    dialog = MachineEditorDialog()
    dialog.show()
    posts = dialog.post_processor_combo                # a Post, so that only two findings stay
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
