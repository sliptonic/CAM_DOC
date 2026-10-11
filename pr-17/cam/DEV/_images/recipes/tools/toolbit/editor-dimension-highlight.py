# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit tab of the Toolbit Parameter Editor with the pointer on the D dimension of the shape
drawing."""
import os
import sys

PAGE = "tools/toolbit.adoc"
ALT = "Toolbit tab with the D dimension of the shape drawing and the Diameter field highlighted"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _toolbit
    from PySide import QtCore, QtGui, QtWidgets

    editor = _toolbit.open_editor()
    shot.settle()
    # Move the pointer on the label of the Diameter dimension.
    drawing = editor._shape_widget
    at = drawing._dimension_rects()["Diameter"][0].center().toPoint()
    at = drawing.icon_widget.mapFromParent(at)
    move = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, at, drawing.icon_widget.mapToGlobal(at),
                             QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
    QtWidgets.QApplication.sendEvent(drawing.icon_widget, move)
    shot.widget(editor.form)
    editor.form.reject()
