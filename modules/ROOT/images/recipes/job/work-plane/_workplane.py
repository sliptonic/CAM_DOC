# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Work Plane recipes: a Job with a Work Plane on the tilted face of the model."""
import FreeCADGui

TILTED_FACE = "Face7"                              # the chamfer face of drilling-1, 21 degrees from the top


def job_with_workplane(shot):
    """Create a Job, select the tilted face and run the Work Plane command.
    Returns the Job and the Work Plane."""
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(job.Model.Group[0], TILTED_FACE)
    FreeCADGui.runCommand("CAM_Workplane")
    shot.settle()
    workplane = job.Workplanes.Group[-1]
    if not workplane.AttachmentSupport:            # the sketches of the model sometimes do not solve
        raise RuntimeError("the Work Plane has no attachment; the model did not recompute. Run again.")
    return job, workplane
