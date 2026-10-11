# SPDX-License-Identifier: LGPL-2.1-or-later
"""Context menu of a Tool Bit in the Library Manager, with the Default library selected."""
import os
import sys

PAGE = "tools/library-manager.adoc"
ALT = "Context menu of a Tool Bit in a Tool Library, with the entries Edit, Copy, Cut, Paste, Duplicate and Remove from Library"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _manager
    from PySide import QtCore, QtGui, QtWidgets

    editor = _manager.open_manager(shot)
    bits = editor.browser._tool_list_widget
    item = bits.item(1)
    bits.setCurrentItem(item)
    shot.settle()

    # The Tool Bit list opens its menu with exec_(), which waits. Capture the menu from a timer,
    # then close the menu, so that the capture continues.
    def capture_menu():
        menu = QtWidgets.QApplication.activePopupWidget()
        try:
            shot.widget(menu)
        finally:
            menu.close()

    QtCore.QTimer.singleShot(1500, capture_menu)
    at = bits.visualItemRect(item).center()
    event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse, at, bits.viewport().mapToGlobal(at))
    QtWidgets.QApplication.sendEvent(bits.viewport(), event)
    editor.form.reject()
