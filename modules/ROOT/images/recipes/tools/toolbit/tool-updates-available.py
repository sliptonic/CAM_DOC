# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Updates Available dialog for a Job with two library Tool Bits that were edited in the
document: one has a new preset, the other has a new preset and a different Diameter."""
PAGE = "tools/toolbit.adoc"
ALT = "Tool Updates Available dialog with a Presets row and an expanded Presets, Geometry row that shows the Diameter change"


def capture(shot):
    from PySide import QtWidgets
    import FreeCADGui
    import Path.Tool.Gui.Controller as GuiController
    from Path.Tool.camassets import cam_assets
    from Path.Tool.FeedsSpeeds.presets import make_preset, set_presets
    from Path.Tool.Gui.UpdateDocumentToolsDlg import _UpdateToolsDialog
    from Path.Tool.UpdateDocumentTools import job_stale_tools

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    endmill = cam_assets.get("toolbit://5mm_Endmill").attach_to_doc(doc)
    drill = cam_assets.get("toolbit://5mm_Drill").attach_to_doc(doc)
    job.Proxy.addToolController(GuiController.Create("TC: 5mm Endmill", endmill, 2))
    job.Proxy.addToolController(GuiController.Create("TC: 5mm Drill", drill, 3))

    # The edits of the Tool Bits in the document. The library Tool Bits stay as shipped.
    preset = make_preset(name="Aluminium", surface_speed=300.0, chipload=0.05)
    set_presets(endmill, [preset])
    set_presets(drill, [preset])
    drill.Diameter = "4.8 mm"
    doc.recompute()

    # Update Tools from Library opens the dialog with exec_(), which stops the capture.
    # Create the same dialog and show it without the wait.
    stale = job_stale_tools(job, cam_assets)
    dialog = _UpdateToolsDialog(job.Label, [(job.Label, stale)], parent=FreeCADGui.getMainWindow())
    dialog.show()
    shot.settle()
    for tree in dialog.findChildren(QtWidgets.QTreeWidget):    # each row that has Geometry
        tree.topLevelItem(0).setExpanded(True)
    shot.widget(dialog)
    dialog.reject()
