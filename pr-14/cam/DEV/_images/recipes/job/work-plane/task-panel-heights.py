# SPDX-License-Identifier: LGPL-2.1-or-later
"""Heights page of the task panel of an Operation, with a Work Plane selected."""
import os
import sys

from PySide import QtWidgets

PAGE = "job/work-plane.adoc"
ALT = "Profile task panel, Heights page, with a Work Plane selected in the Work Plane selector and the Reset to defaults button"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _workplane

    job, workplane = _workplane.job_with_workplane(shot)
    op = shot.new_operation("Path.Op.Gui.Profile", job)
    op.ViewObject.Document.setEdit(op.ViewObject, 0)
    shot.settle(800)

    form = op.ViewObject.Proxy.panel.form              # the tab widget of the task panel
    titles = [form.tabText(i).replace("&", "") for i in range(form.count())]
    form.setCurrentIndex(titles.index("Heights"))
    selector = form.currentWidget().findChild(QtWidgets.QComboBox, "workplane")
    selector.setCurrentIndex(selector.findText(workplane.Label))
    shot.settle()
    shot.widget(form)
