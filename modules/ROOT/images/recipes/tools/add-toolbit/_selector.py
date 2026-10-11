# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Add Toolbit… recipes: the Toolbit Selector dialog with one entry of the
library list selected."""


def open_selector(shot, library, job=None):
    """Show the dialog as the Add Toolbit… command opens it, and select `library` in the
    library list. Returns the ToolBitLibraryDock; the dialog is dock.form."""
    from PySide import QtGui
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    # The pointer of the off-screen display must not highlight a row of the dialog.
    QtGui.QCursor.setPos(0, 0)
    # ToolBitLibraryDock.open() calls exec_(), which stops the capture. Show the dialog
    # without the wait.
    dock = ToolBitLibraryDock(job)
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    libraries.setCurrentIndex(libraries.findText(library))
    shot.settle()
    return dock
