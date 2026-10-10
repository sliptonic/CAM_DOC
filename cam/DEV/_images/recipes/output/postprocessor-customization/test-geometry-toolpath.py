# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolpath of the test geometry, with the pointer on the first move so that the arrow shows."""
import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui, QtWidgets

PAGE = "output/postprocessor-customization.adoc"
ALT = "Toolpath of the test geometry in the 3D view, one level in the XY plane, with the blue arrow near the start point"


def capture(shot):
    doc = shot.open_model("lines-arcs-1")
    job = shot.new_job([doc.getObject("Sketch")])
    op = shot.new_operation("Path.Op.Gui.Engrave", job)   # the Tool Bit centre follows the sketch
    shot.view(1200, 900)                                  # the Toolpath is at the top of the Stock

    # Move the pointer onto the first move, near the start point. The arrow shows on that move.
    view = FreeCADGui.ActiveDocument.ActiveView
    viewport = view.graphicsView().viewport()
    x, y = view.getPointOnViewport(FreeCAD.Vector(0, 3, op.FinalDepth.Value))
    pos = QtCore.QPointF(x, viewport.height() - y)
    for p in (pos + QtCore.QPointF(1, 1), pos):
        QtWidgets.QApplication.sendEvent(viewport, QtGui.QMouseEvent(
            QtCore.QEvent.MouseMove, p, QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier))
        shot.settle(300)
    if not FreeCADGui.Selection.getPreselection().SubElementNames[0]:
        raise RuntimeError("the pointer is not on the Toolpath; the arrow does not show")
    view.saveImage(shot.out, 1200, 900, "Current")
