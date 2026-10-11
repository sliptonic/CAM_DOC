# SPDX-License-Identifier: LGPL-2.1-or-later
"""Duplicate preset message: Copy for a Preset, then OK in the Edit preset dialog with the
name, the material and the op type not changed."""
import os
import sys

PAGE = "tools/feeds-speeds.adoc"
ALT = "Duplicate preset message above the Edit preset dialog, with the text This tool already has a preset named 'Finish' for this material and op type"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    from PySide import QtWidgets
    import Path.Tool.toolbit.ui.presets_tab as presets_tab
    import _presets

    # QMessageBox.warning() waits for the user, which stops the capture. Show the same
    # message without the wait, in the centre of the Edit preset dialog.
    def warning(parent, title, text):
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, text,
                                    QtWidgets.QMessageBox.Ok, parent)
        box.show()
        shot.settle()
        box.move(parent.geometry().center() - box.rect().center())
        parent.nameEdit.deselect()                     # no selected text in a figure
        shot.settle()
        # shot.widget() captures one window. Capture the area of the dialog from the display,
        # so that the figure shows the message above the dialog.
        area = parent.geometry()
        image = parent.screen().grabWindow(0, area.x(), area.y(), area.width(), area.height())
        shot.saved = image.save(shot.out, "PNG")
        box.close()

    QtWidgets.QMessageBox.warning = warning

    # exec_() waits for the user too. Show the dialog, click OK, and return as Cancel does.
    def exec_(dialog):
        dialog.form.show()
        shot.settle()
        dialog.form.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).click()
        dialog.form.close()
        return QtWidgets.QDialog.Rejected

    presets_tab._EditPresetDialog.exec_ = exec_

    editor = _presets.open_presets_tab()
    _presets.select_preset(editor, "Finish")
    editor.presets_tab.copy_button.click()
    editor.form.reject()
