# SPDX-License-Identifier: LGPL-2.1-or-later
"""Property editor of a Work Plane with the Fixture property set."""
import os
import sys

import FreeCADGui
from PySide import QtWidgets

PAGE = "job/work-plane.adoc"
ALT = "Property editor of a Work Plane, with the Fixture property set to G55"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _workplane

    job, workplane = _workplane.job_with_workplane(shot)   # the command selects the new Work Plane
    workplane.Fixture = "G55"
    shot.settle()

    mw = FreeCADGui.getMainWindow()
    editors = [w for w in mw.findChildren(QtWidgets.QTreeView)
               if w.metaObject().className() == "Gui::PropertyEditor::PropertyEditor" and w.isVisible()]
    shot.widget(editors[0])
