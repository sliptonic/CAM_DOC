# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the tree view recipes: a Job, and its item in the tree view with the children shown."""
from PySide import QtCore, QtWidgets

import FreeCADGui


def find_item(tree, label):
    return tree.findItems(label, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)[0]


def job_in_tree(shot):
    """Create a Job. Returns the Job, the tree view and the tree item of the Job, expanded."""
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    trees = FreeCADGui.getMainWindow().findChildren(QtWidgets.QTreeWidget)
    tree = [t for t in trees if t.metaObject().className() == "Gui::TreeWidget" and t.isVisible()][0]
    item = find_item(tree, job.Label)
    item.setExpanded(True)
    shot.settle()
    return job, tree, item
