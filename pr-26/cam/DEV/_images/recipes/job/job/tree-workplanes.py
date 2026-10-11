# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tree view of a Job with one Work Plane in the Workplanes group."""
import os
import sys

import FreeCADGui

PAGE = "job/job.adoc"
ALT = "Tree view of a Job, with one Work Plane below the Workplanes group"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _tree

    job, tree, item = _tree.job_in_tree(shot)
    FreeCADGui.runCommand("CAM_Workplane")             # no face selected: a Work Plane at the Job origin
    shot.settle()
    _tree.find_item(tree, job.Workplanes.Label).setExpanded(True)
    FreeCADGui.Selection.clearSelection()
    shot.widget(tree)
