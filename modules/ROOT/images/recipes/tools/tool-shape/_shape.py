# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Tool Shape recipes: the Toolbit Parameter Editor for the 5 mm Endmill of the
Default library, and the theme buttons of the first-start page."""
TOOL = "toolbit://5mm_Endmill"
TOOL_NO = 2                                        # its number in the Default library


def select_theme(shot, name):
    """Press the theme button of the first-start page, for example "FreeCAD Dark"."""
    import FreeCADGui
    from PySide import QtWidgets

    buttons = [b for b in FreeCADGui.getMainWindow().findChildren(QtWidgets.QAbstractButton)
               if b.text().replace("&", "") == name]
    if not buttons:
        raise RuntimeError(f"the first-start page has no theme button '{name}'")
    buttons[0].click()
    shot.settle(1000)


def open_editor():
    """Show the editor as the Toolbit Library Manager opens it. Returns the editor; the dialog
    is editor.form."""
    from PySide import QtGui
    from Path.Tool.camassets import cam_assets
    from Path.Tool.toolbit.ui.editor import ToolBitEditor

    # The pointer of the off-screen display is on a row of the form, and the editor highlights
    # the dimension of this row. Move the pointer away from the dialog.
    QtGui.QCursor.setPos(0, 0)
    # ToolBitEditor.show() calls exec_(), which stops the capture. Show the dialog without the wait.
    editor = ToolBitEditor(cam_assets.get(TOOL), TOOL_NO)
    editor.form.show()
    return editor
