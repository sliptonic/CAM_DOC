# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Operations tab, for a Job with two Operations."""
import os
import sys

PAGE = "output/post-process.adoc"
ALT = "Post-Processing Dialog, Operations tab, with a Profile and a Drilling Operation in the list"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _dialog

    post = _dialog.open_dialog(shot, "tabOperations")
    shot.widget(post.dialog)
    post.dialog.reject()
