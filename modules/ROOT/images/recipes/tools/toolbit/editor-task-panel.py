# SPDX-License-Identifier: LGPL-2.1-or-later
"""ToolBit editor as a task panel, for the Tool Bit of the first Tool Controller of a Job."""
import FreeCADGui

PAGE = "tools/toolbit.adoc"
ALT = "ToolBit editor as a task panel, with the properties and the shape drawing of the Tool Bit"


def capture(shot):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    tool = job.Tools.Group[0].Tool
    window = FreeCADGui.getMainWindow()
    window.resize(window.width(), 1400)                      # the panel is higher than the window
    tool.ViewObject.Document.setEdit(tool.ViewObject, 0)     # as a double-click in the tree view
    shot.settle(800)
    shot.widget(tool.ViewObject.Proxy.panel.form)
