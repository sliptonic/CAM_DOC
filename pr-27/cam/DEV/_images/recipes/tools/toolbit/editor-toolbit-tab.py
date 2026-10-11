# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor on the Toolbit tab, for the 5 mm Endmill that FreeCAD supplies."""
PAGE = "tools/toolbit.adoc"
ALT = "Toolbit Parameter Editor on the Toolbit tab, with the properties and the shape drawing of an endmill"


def capture(shot):
    from Path.Tool.camassets import cam_assets
    from Path.Tool.toolbit.ui.editor import ToolBitEditor

    # ToolBitEditor.show() opens the dialog with exec_(), which stops the capture. Show the
    # form of the editor without the wait.
    editor = ToolBitEditor(cam_assets.get("toolbit://5mm_Endmill"))
    editor.form.show()
    shot.widget(editor.form)
    editor.form.reject()
