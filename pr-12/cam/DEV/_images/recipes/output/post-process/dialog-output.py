# SPDX-License-Identifier: LGPL-2.1-or-later
"""Post-Processing Dialog, Output tab, after a press of the Generate Output button."""
import os
import sys

PAGE = "output/post-process.adoc"
ALT = "Post-Processing Dialog, Output tab, after Generate Output, with one file in the list and its G-code"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _dialog

    post = _dialog.open_dialog(shot, "tabOverview")
    buttons = post.dialog.buttonBox.buttons()
    generate = [b for b in buttons if b.text().replace("&", "") == "Generate Output"][0]
    # The button selects the Output tab when the Post gives output.
    generate.click()
    shot.settle()
    shot.widget(post.dialog)
    post.dialog.reject()
