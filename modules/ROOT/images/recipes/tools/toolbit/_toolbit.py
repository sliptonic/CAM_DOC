# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Tool Bit recipes: the Toolbit Parameter Editor for the 5 mm Endmill of the
Default library, and a Job with Tool Bits from the library."""
TOOL = "toolbit://5mm_Endmill"
TOOL_NO = 2                                        # its number in the Default library


def open_editor(presets=None):
    """Show the editor as the Toolbit Library Manager opens it. Returns the editor; the dialog
    is editor.form."""
    from PySide import QtGui
    from Path.Tool.camassets import cam_assets
    from Path.Tool.FeedsSpeeds import set_presets
    from Path.Tool.toolbit.ui.editor import ToolBitEditor

    # The pointer of the off-screen display is on a row of the form, and the editor highlights
    # the dimension of this row. Move the pointer away from the dialog.
    QtGui.QCursor.setPos(0, 0)
    toolbit = cam_assets.get(TOOL)
    if presets:
        set_presets(toolbit.obj, presets)
    # ToolBitEditor.show() calls exec_(), which stops the capture. Show the dialog without the wait.
    editor = ToolBitEditor(toolbit, TOOL_NO)
    editor.form.show()
    return editor


def select_tab(editor, title):
    tabs = editor.form.tabWidget
    titles = [tabs.tabText(i).replace("&&", "&") for i in range(tabs.count())]
    tabs.setCurrentIndex(titles.index(title))


def add_tool(job, asset_id, number):
    """Add a Tool Controller with a Tool Bit of the library to the Job. Returns the Tool Bit object."""
    import Path.Tool.Controller as Controller
    from Path.Tool.camassets import cam_assets

    toolbit = cam_assets.get(f"toolbit://{asset_id}")
    tool = toolbit.attach_to_doc(job.Document)
    tool.ViewObject.Visibility = False
    job.Proxy.addToolController(Controller.Create(f"TC: {tool.Label}", tool, number))
    return tool
