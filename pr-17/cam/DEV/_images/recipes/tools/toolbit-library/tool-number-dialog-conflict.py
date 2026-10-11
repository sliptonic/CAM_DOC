# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number dialog: Add to Job for a Tool Bit whose library number a Tool Controller of
a different Tool Bit has."""
PAGE = "tools/toolbit-library.adoc"
ALT = "Tool Number dialog with the text Tool number 1 is already used by TC: 5mm Endmill, and the next free number 2 as the value"


def capture(shot):
    from PySide import QtWidgets
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    # The Job has the Tool Controller "TC: 5mm Endmill" with the Tool Number 1.
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])

    # QInputDialog.getInt() waits for the user, which stops the capture. Show the same
    # dialog without the wait, and return as Cancel does.
    def get_int(parent, title, label, value, minimum):
        box = QtWidgets.QInputDialog(parent)
        box.setInputMode(QtWidgets.QInputDialog.IntInput)
        box.setWindowTitle(title)
        box.setLabelText(label)
        box.setIntMinimum(minimum)
        box.setIntValue(value)
        box.show()
        shot.settle()
        box.findChild(QtWidgets.QLineEdit).deselect()    # no selected text in a figure
        shot.widget(box)
        box.close()
        return value, False

    QtWidgets.QInputDialog.getInt = get_int

    dock = ToolBitLibraryDock(job)
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    libraries.setCurrentIndex(libraries.findText("Default"))
    shot.settle()
    # The 3.175 mm endmill has the number 1 in the Default library.
    dock.browser_widget.select_by_uri(["toolbit://3.175mm_Endmill"])
    dock.addToolControllerButton.click()
    dock.form.reject()
