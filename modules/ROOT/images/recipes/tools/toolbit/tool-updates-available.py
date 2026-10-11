# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Updates Available dialog for a Job with two Tool Bits that are different from the library:
one in its Presets, one in two shape parameters."""
import os
import sys

import FreeCADGui

PAGE = "tools/toolbit.adoc"
ALT = "Tool Updates Available dialog with a Presets row and an expanded Geometry row with old and new values"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _toolbit
    from PySide import QtWidgets
    from Path.Tool.camassets import cam_assets
    from Path.Tool.FeedsSpeeds import make_preset, set_presets
    from Path.Tool.Gui.UpdateDocumentToolsDlg import _UpdateToolsDialog
    from Path.Tool.UpdateDocumentTools import job_stale_tools

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    endmill = _toolbit.add_tool(job, "5mm_Endmill", 2)
    drill = _toolbit.add_tool(job, "5mm_Drill", 3)
    # Change the Tool Bits in the document, so that the library is different.
    set_presets(endmill, [make_preset(name="Aluminium profile", surface_speed=300.0, chipload=0.05)])
    drill.Diameter = "4.8 mm"
    drill.Length = "45 mm"
    doc.recompute()

    # Update Tools from Library opens the dialog with exec_(), which stops the capture. Create
    # the same dialog from the same comparison and show it without the wait.
    stale = job_stale_tools(job, cam_assets)
    dialog = _UpdateToolsDialog(job.Label, [(job.Label, stale)], parent=FreeCADGui.getMainWindow())
    dialog.show()
    shot.settle()
    for tree in dialog.findChildren(QtWidgets.QTreeWidget):
        tree.topLevelItem(0).setExpanded(True)
    shot.widget(dialog)
    dialog.reject()
