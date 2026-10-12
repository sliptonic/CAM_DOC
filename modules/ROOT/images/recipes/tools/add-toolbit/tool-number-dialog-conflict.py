# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number dialog for a Tool Bit whose library tool number the default Tool Controller of
the Job already has."""
import os
import sys

PAGE = "tools/add-toolbit.adoc"
ALT = "Tool Number dialog, which names the Tool Controller that has the library tool number and asks for the tool number of the new Tool Bit"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _selector
    from PySide import QtWidgets

    dock = _selector.open_selector(shot, "Default")

    # QInputDialog.getInt() waits for the user, which stops the capture. Show the same dialog
    # without the wait, and answer as Cancel does.
    def get_int(parent, title, label, value, minimum):
        dialog = QtWidgets.QInputDialog(parent)
        dialog.setInputMode(QtWidgets.QInputDialog.IntInput)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setIntMinimum(minimum)
        dialog.setIntValue(value)
        dialog.show()
        shot.settle()
        dialog.findChild(QtWidgets.QSpinBox).lineEdit().deselect()    # no selected text in the figure
        shot.widget(dialog)
        dialog.close()
        return value, False

    QtWidgets.QInputDialog.getInt = get_int

    # The first Tool Bit of the library has tool number 1, as the default Tool Controller has.
    tools = dock.browser_widget._tool_list_widget
    tools.setCurrentRow(0)
    dock.addToolControllerButton.click()
    dock.form.reject()
