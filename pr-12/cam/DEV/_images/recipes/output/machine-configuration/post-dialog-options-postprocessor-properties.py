# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Options tab, moved down to the Postprocessor Properties group."""
import os
import sys

PAGE = "output/machine-configuration.adoc"
ALT = "Post-Processing Dialog, Options tab, Postprocessor Properties group of the linuxcnc Post"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _machine
    from PySide import QtWidgets
    from Path.Post.Gui.DlgPostProcess import PostProcessDialog

    _machine.save_machine()
    job = _machine.job_with_operations(shot)
    job.Machine = _machine.NAME
    post = PostProcessDialog(job)
    dialog = post.dialog
    dialog.show()
    dialog.tabWidget.setCurrentWidget(dialog.tabOutput)
    shot.settle()
    groups = dialog.scrollContentsOutput.findChildren(QtWidgets.QGroupBox)
    group = [g for g in groups if g.title() == "Postprocessor Properties"][0]
    bar = dialog.scrollAreaOutput.verticalScrollBar()
    bar.setValue(min(group.y(), bar.maximum()))
    shot.widget(dialog)
    dialog.reject()
