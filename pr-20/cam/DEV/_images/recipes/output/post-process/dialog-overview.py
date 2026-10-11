# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Overview tab, for a Job with a saved Machine."""
import os
import sys

PAGE = "output/post-process.adoc"
ALT = "Post-Processing Dialog, Overview tab, with the Machine Shop Router selected and the Post Processor Parameters group"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _dialog

    post = _dialog.open_dialog(shot, "tabOverview")
    shot.widget(post.dialog)
    post.dialog.reject()
