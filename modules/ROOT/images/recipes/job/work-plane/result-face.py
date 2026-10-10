# SPDX-License-Identifier: LGPL-2.1-or-later
"""3D view of a Work Plane that the command made from a tilted planar face."""
import os
import sys

import FreeCADGui

PAGE = "job/work-plane.adoc"
ALT = "3D view of a Model with the axes of a Work Plane at the centroid of a tilted planar face"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _workplane

    job, workplane = _workplane.job_with_workplane(shot)   # the command selects the new Work Plane
    FreeCADGui.runCommand("Std_ToggleVisibility")          # a new Work Plane is hidden: show it
    shot.view(1200, 900)
