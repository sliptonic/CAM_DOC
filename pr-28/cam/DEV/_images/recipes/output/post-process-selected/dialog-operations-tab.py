# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Operations tab, as Post Process Selected opens it after the answer
"Only selected": two of the three Operations of the Job are selected in the Tree View."""
PAGE = "output/post-process-selected.adoc"
ALT = "Post-Processing Dialog, Operations tab, opened from Post Process Selected, with the two selected Operations checked and the third Operation not checked"
NAME = "Shop Router"


def save_machine():
    """Write Shop_Router.fcm, a 3-axis Machine with the linuxcnc Post, into the asset folder."""
    from Machine.models.machine import Machine, MachineFactory

    machine = Machine.create_3axis_config()
    machine.name = NAME
    machine.postprocessor_file_name = "linuxcnc"
    MachineFactory.save_configuration(machine)


def capture(shot):
    import FreeCADGui
    from Path.Post.Gui.DlgPostProcess import PostProcessDialog

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    # Feed rates and a spindle speed: without them the Time column shows an error.
    controller = job.Tools.Group[0]
    controller.HorizFeed = "600 mm/min"
    controller.VertFeed = "200 mm/min"
    controller.SpindleSpeed = 12000
    shot.new_operation("Path.Op.Gui.MillFacing", job)
    profile = shot.new_operation("Path.Op.Gui.Profile", job)
    drilling = shot.new_operation("Path.Op.Gui.Drilling", job)
    # The Auto Select button of the Drilling task panel does this.
    drilling.Proxy.findAllHoles(drilling)
    doc.recompute()
    save_machine()
    job.Machine = NAME
    # Select two Operations in the Tree View, as the user does before the command.
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(profile)
    FreeCADGui.Selection.addSelection(drilling)
    selected = FreeCADGui.Selection.getSelection()
    # CAM_PostSelected asks "What needs to be exported?" in a modal message box. The answer
    # "Only selected" gives the dialog this argument (Path/Post/Command.py).
    post = PostProcessDialog(job, {"job": job, "operations": selected})
    dialog = post.dialog
    dialog.show()
    dialog.tabWidget.setCurrentWidget(dialog.tabOperations)
    shot.widget(dialog)
    dialog.reject()
