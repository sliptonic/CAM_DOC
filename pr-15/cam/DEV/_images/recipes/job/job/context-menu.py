# SPDX-License-Identifier: LGPL-2.1-or-later
"""Context menu of a Job in the tree view."""
import os
import sys

import FreeCADGui

PAGE = "job/job.adoc"
ALT = "Context menu of a Job in the tree view, with the Update Tools from Library entry"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _tree
    from PySide import QtCore, QtGui, QtWidgets

    job, tree, item = _tree.job_in_tree(shot)
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(job)
    shot.settle()

    # The tree view opens its menu with exec(), which waits. Capture the menu from a timer,
    # then close the menu, so that the capture continues.
    def capture_menu():
        menu = QtWidgets.QApplication.activePopupWidget()
        try:
            shot.widget(menu)
        finally:
            menu.close()

    QtCore.QTimer.singleShot(1500, capture_menu)
    at = tree.visualItemRect(item).center()
    event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse, at, tree.viewport().mapToGlobal(at))
    QtWidgets.QApplication.sendEvent(tree.viewport(), event)
