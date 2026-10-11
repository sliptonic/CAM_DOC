# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Toolbit Selector recipes of this page: a Job, and the Toolbit Selector with one
entry of the library drop-down selected."""


def open_selector(shot, library):
    """Open the Toolbit Selector for a new Job and select `library` (the text of the entry) in
    the library drop-down. Returns the ToolBitLibraryDock; its `form` is the widget for
    shot.widget()."""
    from PySide import QtCore, QtGui, QtWidgets
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    doc = shot.open_model("drilling-1")
    shot.new_job([doc.getObject("Body")])
    # The Add Toolbit command opens the dialog with exec_(), which stops the capture. Create
    # the same dialog and show it without the wait.
    dock = ToolBitLibraryDock(askToolNumber=True)
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    names = [libraries.itemText(i) for i in range(libraries.count())]
    if library not in names:
        raise KeyError(f"the library drop-down has no entry '{library}'; it has {names}")
    libraries.setCurrentIndex(names.index(library))
    # The pointer is on the dialog and highlights a row. Tell the list that the pointer left.
    tools = dock.browser_widget._tool_list_widget
    QtWidgets.QApplication.sendEvent(tools.viewport(), QtCore.QEvent(QtCore.QEvent.Leave))
    # The search box has the text cursor. Tell it that the keyboard focus left.
    search = dock.browser_widget._search_edit
    QtWidgets.QApplication.sendEvent(search, QtGui.QFocusEvent(QtCore.QEvent.FocusOut))
    shot.settle()
    return dock
