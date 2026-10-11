# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Selector dialog with the All Tools entry selected in the library list."""
PAGE = "tools/toolbit-library.adoc"
ALT = "Toolbit Selector dialog with the All Tools entry selected in the library list, without a sort control and without tool numbers"


def capture(shot):
    from PySide import QtGui
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    # The pointer of the off-screen display must not highlight a row of the dialog.
    QtGui.QCursor.setPos(0, 0)
    # ToolBitLibraryDock.open() calls exec_(), which stops the capture. Show the dialog
    # without the wait.
    dock = ToolBitLibraryDock()
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    libraries.setCurrentIndex(libraries.findText("All Tools"))
    shot.widget(dock.form)
    dock.form.reject()
