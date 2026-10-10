# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Post-Processing Dialog recipes of this page: a Job with a saved Machine, and
the dialog for that Job on one tab."""
NAME = "Shop Router"


def save_machine():
    """Write Shop_Router.fcm, a 3-axis Machine with the linuxcnc Post, into the asset folder."""
    from Machine.models.machine import Machine, MachineFactory

    machine = Machine.create_3axis_config()
    machine.name = NAME
    machine.postprocessor_file_name = "linuxcnc"
    MachineFactory.save_configuration(machine)


def open_dialog(shot, tab):
    """Open the dialog for a Job with a Profile and a Drilling Operation, and select the tab
    with this object name (tabOverview, tabOperations, tabOutput, tabGcodeOutput). Returns the
    PostProcessDialog; its `dialog` is the widget for shot.widget()."""
    from Path.Post.Gui.DlgPostProcess import PostProcessDialog

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    # Feed rates, a spindle speed and an Output File: without them the Time column shows an
    # error and the Filename template is empty.
    controller = job.Tools.Group[0]
    controller.HorizFeed = "600 mm/min"
    controller.VertFeed = "200 mm/min"
    controller.SpindleSpeed = 12000
    job.PostProcessorOutputFile = "%D/%d-%j.nc"
    shot.new_operation("Path.Op.Gui.Profile", job)
    drilling = shot.new_operation("Path.Op.Gui.Drilling", job)
    # The Auto Select button of the Drilling task panel does this.
    drilling.Proxy.findAllHoles(drilling)
    doc.recompute()
    save_machine()
    job.Machine = NAME
    post = PostProcessDialog(job)
    post.dialog.show()
    post.dialog.tabWidget.setCurrentWidget(getattr(post.dialog, tab))
    shot.settle()
    return post
