# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Tool Controller recipes: a Job, and the Tool Controller Editor task panel."""
from PySide import QtWidgets

import FreeCADGui


def new_job(shot):
    """Create a Job. It has the Tool Controller "TC: 5mm Endmill" with the Tool Number 1."""
    doc = shot.open_model("drilling-1")
    return shot.new_job([doc.getObject("Body")])


def open_editor(shot, tc):
    """Open the Tool Controller Editor task panel, as a double-click on the Tool Controller in
    the tree view does. Returns the form of the panel."""
    FreeCADGui.ActiveDocument.setEdit(tc.Name)
    shot.settle(800)
    dialogs = FreeCADGui.getMainWindow().findChildren(QtWidgets.QDialog, "Dialog")
    return [d for d in dialogs if d.windowTitle() == "Tool Controller Editor"][0]
