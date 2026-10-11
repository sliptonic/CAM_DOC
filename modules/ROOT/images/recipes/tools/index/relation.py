# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tree view of a Job with the Tools group open: the Tool Controller and its Tool Bit object."""
import FreeCADGui
from PySide import QtCore, QtWidgets

PAGE = "tools/index.adoc"
ALT = "Tree view of a Job, with one Tool Controller in the Tools group and the Tool Bit object below the Tool Controller"


def capture(shot):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])        # a new Job has one Tool Controller
    controller = job.Tools.Group[0]
    print("controllers:", [tc.Label for tc in job.Tools.Group], "tool bit:", controller.Tool.Label)
    FreeCADGui.Selection.clearSelection()

    trees = FreeCADGui.getMainWindow().findChildren(QtWidgets.QTreeWidget)
    tree = [t for t in trees if t.metaObject().className() == "Gui::TreeWidget" and t.isVisible()][0]
    for label in (job.Label, job.Tools.Label, controller.Label):
        tree.findItems(label, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)[0].setExpanded(True)
        shot.settle()
    tree.scrollToTop()
    shot.widget(tree)
