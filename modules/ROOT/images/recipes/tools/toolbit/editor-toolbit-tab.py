# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor as it opens for the shipped 5mm Endmill, Toolbit tab."""
PAGE = "tools/toolbit.adoc"
ALT = "Toolbit Parameter Editor, Toolbit tab, for the 5mm Endmill, with the Properties list and the shape drawing"


def capture(shot):
    from Path.Tool.camassets import cam_assets
    from Path.Tool.toolbit.ui import ToolBitEditor

    toolbit = cam_assets.get("toolbit://5mm_Endmill")
    # ToolBitEditor.show() opens the dialog with exec_(), which stops the capture. Show the
    # dialog of the editor without the wait.
    editor = ToolBitEditor(toolbit)
    editor.form.show()
    shot.widget(editor.form)
    editor.form.reject()
