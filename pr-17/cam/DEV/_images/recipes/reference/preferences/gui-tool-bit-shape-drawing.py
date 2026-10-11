# SPDX-License-Identifier: LGPL-2.1-or-later
"""CAM preferences, GUI page, with the Tool Bit Shape Drawing group at the default values."""
import FreeCADGui

PAGE = "reference/preferences.adoc"
ALT = "GUI page of the CAM preferences, with the Tool Bit Shape Drawing group: three dimension colors and the tool artwork brightness of 85 %"


def capture(shot):
    from PySide import QtCore, QtWidgets

    # The GUI page is a C++ class that only the Preferences Editor creates, and the editor
    # opens with exec(), which waits. Capture the page from a timer, then close the editor,
    # so that the capture continues.
    def capture_page():
        editor = QtWidgets.QApplication.activeModalWidget()
        try:
            group = editor.findChild(QtWidgets.QGroupBox, "groupBoxToolBitDrawing")
            shot.widget(group.parentWidget())
        finally:
            editor.reject()

    QtCore.QTimer.singleShot(1500, capture_page)
    FreeCADGui.showPreferences("CAM", 0)
