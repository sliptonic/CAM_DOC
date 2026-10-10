# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Job task panel recipes: a Job with two Operations, and its task panel on one tab."""
import FreeCADGui
from PySide import QtCore

TABS = {"setup": 0, "general": 1, "output": 2, "tools": 3, "workplan": 4}


def capture_panel(shot, tab):
    FreeCADGui.getMainWindow().setGeometry(0, 0, 1500, 950)
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    tc = job.Tools.Group[0]                       # feeds and speed, so that the Workplan shows times
    tc.HorizFeed = "600 mm/min"
    tc.VertFeed = "200 mm/min"
    tc.SpindleSpeed = 12000
    shot.new_operation("Path.Op.Gui.Profile", job)
    shot.new_operation("Path.Op.Gui.Drilling", job)
    doc.recompute()
    job.ViewObject.Document.setEdit(job.ViewObject, 0)
    shot.settle(800)
    form = job.ViewObject.Proxy.taskPanel.form
    form.setCurrentIndex(TABS[tab])
    shot.settle(500)
    # The panel is inside the main window. Capture its area of the window, so that the image has
    # the background that the reader sees; the panel alone has none.
    top = form.window()
    area = QtCore.QRect(form.mapTo(top, QtCore.QPoint(0, 0)), form.size())
    if not top.grab(area).save(shot.out, "PNG"):
        raise RuntimeError(f"cannot write {shot.out}")
    shot.saved = True
