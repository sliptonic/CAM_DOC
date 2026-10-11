# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Add Toolbit recipes: a Job, the Toolbit Selector on one library, and the Tool
Number dialog that Add to Job opens."""


def open_selector(shot, library):
    """Open the Toolbit Selector as the Add Toolbit command does, and select `library` in the
    library drop-down. Returns the selector."""
    from PySide import QtCore, QtWidgets
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    doc = shot.open_model("drilling-1")
    shot.new_job([doc.getObject("Body")])
    # The command opens the dialog with exec_(), which stops the capture. Create the same
    # dialog and show it without the wait.
    dock = ToolBitLibraryDock(askToolNumber=True)
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    libraries.setCurrentIndex(libraries.findText(library))
    # The pointer is on the dialog and highlights a row. Tell the list that the pointer left.
    tools = dock.browser_widget._tool_list_widget
    QtWidgets.QApplication.sendEvent(tools.viewport(), QtCore.QEvent(QtCore.QEvent.Leave))
    # The dialog is the active window, as for a user. Then the capture can remove the keyboard
    # focus of the search box, and the figure has no text cursor.
    dock.form.activateWindow()
    shot.settle()
    return dock


def capture_tool_number(shot, dock, uri):
    """Select the Tool Bit `uri` in the tool list, press Add to Job, and capture the Tool Number
    dialog that opens."""
    from PySide import QtWidgets

    # QInputDialog.getInt() waits for the user, which stops the capture. Show the same dialog
    # without the wait, and cancel it.
    def get_int(parent, title, label, value, minimum):
        box = QtWidgets.QInputDialog(parent)
        box.setWindowTitle(title)
        box.setLabelText(label)
        box.setIntRange(minimum, 2147483647)
        box.setIntValue(value)
        box.show()
        shot.settle()
        box.findChild(QtWidgets.QLineEdit).deselect()    # no selected text in a figure
        shot.widget(box)
        box.close()
        return value, False

    QtWidgets.QInputDialog.getInt = get_int

    dock.browser_widget.select_by_uri([uri])
    shot.settle()
    dock.addToolControllerButton.click()
