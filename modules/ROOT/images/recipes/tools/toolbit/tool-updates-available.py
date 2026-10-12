# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Updates Available dialog for a Job with two stale Tool Bits: the diameter of each
embedded Tool Bit is different from the library Tool Bit."""
PAGE = "tools/toolbit.adoc"
ALT = "Tool Updates Available dialog with two rows, and the Changes cell of the first row expanded"


def capture(shot):
    from PySide import QtWidgets
    import Path.Tool.Gui.Controller as GuiController
    import Path.Tool.Gui.UpdateDocumentToolsDlg as UpdateDlg
    from Path.Tool.camassets import cam_assets

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    # The Tool Bit of the default Tool Controller is not from the library. Add two that are.
    endmill = cam_assets.get("toolbit://5mm_Endmill").attach_to_doc(doc)
    job.Proxy.addToolController(GuiController.Create("TC: 5mm Endmill", endmill, 2))
    drill = cam_assets.get("toolbit://5mm_Drill").attach_to_doc(doc)
    job.Proxy.addToolController(GuiController.Create("TC: 5mm Drill", drill, 3))
    endmill.Diameter = "4.8 mm"                        # local edits of the embedded Tool Bits
    drill.Diameter = "5.1 mm"
    doc.recompute()

    # Update Tools from Library opens the dialog with exec_(), which stops the capture. Create
    # the same dialog and show it without the wait.
    stale = UpdateDlg.job_stale_tools(job, cam_assets)
    dialog = UpdateDlg._UpdateToolsDialog(job.Label, [(job.Label, stale)])
    dialog.show()
    shot.settle()
    dialog.findChild(QtWidgets.QTreeWidget).expandAll()     # the Changes cell of the first row
    shot.widget(dialog)
    dialog.reject()
