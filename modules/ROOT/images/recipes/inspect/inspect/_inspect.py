# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the CAM Inspect recipes: a Profile operation, the dialog, and a tilted Work Plane."""
import FreeCADGui
from PySide import QtGui

TILTED_FACE = "Face7"                              # the chamfer face of drilling-1, 21 degrees from the top


def profile(shot, tilted=False):
    """Create a Job with a Profile operation. With `tilted`, the operation links to a Work Plane
    that the Work Plane command makes from the tilted face. Returns the operation."""
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    op = shot.new_operation("Path.Op.Gui.Profile", job)
    if tilted:
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(job.Model.Group[0], TILTED_FACE)
        FreeCADGui.runCommand("CAM_Workplane")
        shot.settle()
        op.Workplane = job.Workplanes.Group[-1]
        if not op.Workplane.AttachmentSupport:     # the sketches of the model sometimes do not solve
            raise RuntimeError("the Work Plane has no attachment; the model did not recompute. Run again.")
        doc.recompute()
        shot.settle()
    if len(op.Path.Commands) < 10:                 # the first recompute of the model sometimes fails
        op.touch()
        doc.recompute()
        shot.settle()
    if len(op.Path.Commands) < 10:
        raise RuntimeError("the Profile has no Toolpath; the model did not recompute. Run again.")
    return op


def inspect(shot, op, raw=False):
    """Open the CAM Inspect dialog for the operation, as the command does, without the wait.
    Returns the dialog."""
    import Path.Main.Gui.Inspect as Inspect

    dialog = Inspect.GCodeEditorDialog(op)         # the dialog shows itself
    shot.settle()
    dialog.chkRaw.setChecked(raw)
    shot.settle()
    return dialog


def select_lines(dialog, first, last):
    """Select the lines `first` to `last` (from 1) in the viewer, as a drag with the mouse does."""
    document = dialog.editor.document()
    cursor = dialog.editor.textCursor()
    cursor.setPosition(document.findBlockByNumber(first - 1).position())
    end = document.findBlockByNumber(last - 1)
    cursor.setPosition(end.position() + end.length() - 1, QtGui.QTextCursor.KeepAnchor)
    dialog.editor.setTextCursor(cursor)
