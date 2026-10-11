# SPDX-License-Identifier: LGPL-2.1-or-later
"""Sketch of the test geometry for a Post-Processor, open in the Sketcher."""
import FreeCADGui

PAGE = "output/postprocessor-customization.adoc"
ALT = "Sketch of the test geometry: straight lines and arcs that start at the origin and go in the Y direction"


def capture(shot):
    shot.open_model("lines-arcs-1")
    gui_doc = FreeCADGui.ActiveDocument
    gui_doc.setEdit("Sketch")                     # the Sketcher shows the axes and looks along Z
    shot.settle(800)
    FreeCADGui.SendMsgToActiveView("ViewFit")
    shot.settle(800)
    # shot.view() is isometric; this figure is about the XY plane (STYLE.md §10.3).
    gui_doc.ActiveView.saveImage(shot.out, 1200, 900, "Current")
    shot.saved = True
