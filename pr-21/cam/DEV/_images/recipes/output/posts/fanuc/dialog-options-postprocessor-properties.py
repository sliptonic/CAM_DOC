# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog for a Job with a fanuc Machine, Options tab, moved down to the
Postprocessor Properties group."""
import os
import sys

PAGE = "output/posts/fanuc.adoc"
ALT = "Post-Processing Dialog, Options tab, Postprocessor Properties group of the fanuc Post, with Program Number and Park Empty Spindle at End"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _machine
    from PySide import QtWidgets
    from Path.Post.Gui.DlgPostProcess import PostProcessDialog

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    shot.new_operation("Path.Op.Gui.Profile", job)
    doc.recompute()
    _machine.save_machine()
    job.Machine = _machine.NAME
    post = PostProcessDialog(job)
    dialog = post.dialog
    dialog.show()
    # The Options tab has the object name tabOutput.
    dialog.tabWidget.setCurrentWidget(dialog.tabOutput)
    shot.settle()
    groups = dialog.scrollContentsOutput.findChildren(QtWidgets.QGroupBox)
    group = [g for g in groups if g.title() == "Postprocessor Properties"][0]
    bar = dialog.scrollAreaOutput.verticalScrollBar()
    bar.setValue(min(group.y(), bar.maximum()))
    shot.widget(dialog)
    dialog.reject()
