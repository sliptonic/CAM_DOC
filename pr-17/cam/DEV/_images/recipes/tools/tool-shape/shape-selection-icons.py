# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Shape Selection dialog, as the Toolbit Library Manager opens it for a new Tool Bit."""
PAGE = "tools/tool-shape.adoc"
ALT = "Toolbit Shape Selection dialog, with one button for each Tool Shape that shows the artwork without dimensions"


def capture(shot):
    from Path.Tool.shape.ui.shapeselector import ShapeSelector

    # ShapeSelector.show() calls exec(), which stops the capture. Show the dialog without the wait.
    selector = ShapeSelector()
    selector.form.show()
    shot.widget(selector.form)
    selector.form.reject()
