# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor as a task panel, for the Tool Bit of the Tool Controller of a new Job."""
PAGE = "tools/toolbit.adoc"
ALT = "Toolbit Parameter Editor as a task panel for a Tool Bit in a document, with the Properties list and the shape drawing"


def capture(shot):
    import FreeCADGui

    # A tall main window, so that the task panel shows whole.
    FreeCADGui.getMainWindow().setGeometry(0, 0, 1920, 1400)
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    toolbit = job.Tools.Group[0].Tool
    # What a double-click on the Tool Bit in the tree view calls.
    toolbit.ViewObject.Proxy.doubleClicked(toolbit.ViewObject)
    shot.settle(800)

    box = toolbit.ViewObject.Proxy.panel.form.parentWidget()
    while box.metaObject().className() != "Gui::TaskView::TaskBox":
        box = box.parentWidget()                   # the box of the task panel, with its title bar
    shot.widget(box)
