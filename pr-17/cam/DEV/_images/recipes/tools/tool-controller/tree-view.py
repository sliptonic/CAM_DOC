# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tree view of a Job with the Tools group, its Tool Controller and the Tool Bit object shown."""
import os
import sys

import FreeCADGui

PAGE = "tools/tool-controller.adoc"
ALT = "Tree view of a Job, with a Tool Controller in the Tools group and the Tool Bit object below the Tool Controller"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    from PySide import QtCore, QtWidgets
    import _controller

    job = _controller.new_job(shot)
    tc = job.Tools.Group[0]
    trees = FreeCADGui.getMainWindow().findChildren(QtWidgets.QTreeWidget)
    tree = [t for t in trees if t.metaObject().className() == "Gui::TreeWidget" and t.isVisible()][0]
    for label in (job.Label, job.Tools.Label, tc.Label):
        tree.findItems(label, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)[0].setExpanded(True)
        shot.settle()
    FreeCADGui.Selection.clearSelection()
    shot.widget(tree)
