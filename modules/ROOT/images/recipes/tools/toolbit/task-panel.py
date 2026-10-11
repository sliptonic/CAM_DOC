# SPDX-License-Identifier: LGPL-2.1-or-later
"""Task panel of the Tool Bit object of a Job, as a double-click in the tree view opens it."""
import os
import sys

import FreeCADGui

PAGE = "tools/toolbit.adoc"
ALT = "Task panel of a Tool Bit object, with the properties form and the shape drawing"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _toolbit

    # The panel is higher than the task view of the default window. Make the window higher.
    FreeCADGui.getMainWindow().resize(1600, 1300)
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    tool = _toolbit.add_tool(job, "5mm_Endmill", 2)
    doc.recompute()
    FreeCADGui.ActiveDocument.setEdit(tool.Name)        # what the double-click does
    shot.settle(800)
    shot.widget(tool.ViewObject.Proxy.panel.form)
