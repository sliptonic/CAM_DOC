# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Options tab, moved down to the Postprocessor Properties group."""
import os
import sys

PAGE = "output/post-process.adoc"
ALT = "Post-Processing Dialog, Options tab, with the Postprocessor Properties group of the linuxcnc Post"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _dialog
    from PySide import QtWidgets

    # The Options tab has the object name tabOutput.
    post = _dialog.open_dialog(shot, "tabOutput")
    dialog = post.dialog
    groups = dialog.scrollContentsOutput.findChildren(QtWidgets.QGroupBox)
    group = [g for g in groups if g.title() == "Postprocessor Properties"][0]
    bar = dialog.scrollAreaOutput.verticalScrollBar()
    bar.setValue(min(group.y(), bar.maximum()))
    shot.widget(dialog)
    dialog.reject()
