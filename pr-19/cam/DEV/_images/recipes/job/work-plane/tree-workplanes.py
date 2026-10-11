# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tree view of a Job with two Work Planes in the Workplanes group."""
import os
import sys

import FreeCADGui
from PySide import QtCore, QtWidgets

PAGE = "job/work-plane.adoc"
ALT = "Tree view of a Job, with two Work Planes below the Workplanes group"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _workplane

    job, workplane = _workplane.job_with_workplane(shot)
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.runCommand("CAM_Workplane")             # no face selected: a Work Plane at the Job origin
    shot.settle()
    FreeCADGui.Selection.clearSelection()

    trees = FreeCADGui.getMainWindow().findChildren(QtWidgets.QTreeWidget)
    tree = [t for t in trees if t.metaObject().className() == "Gui::TreeWidget" and t.isVisible()][0]
    for label in (job.Label, job.Workplanes.Label):
        tree.findItems(label, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)[0].setExpanded(True)
    shot.widget(tree)
