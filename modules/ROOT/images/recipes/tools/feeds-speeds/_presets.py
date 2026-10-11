# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Feeds & Speeds recipes: the Toolbit Parameter Editor for the 5 mm Endmill of
the Default library with three Presets, open on the Feeds & Speeds tab."""
TOOL = "toolbit://5mm_Endmill"
TOOL_NO = 2                                        # its number in the Default library


def open_presets_tab():
    """Show the editor as the Toolbit Library Manager opens it, on the Feeds & Speeds tab.
    Returns the editor; the dialog is editor.form and the tab is editor.presets_tab."""
    from PySide import QtGui
    from Path.Tool.camassets import cam_assets
    from Path.Tool.FeedsSpeeds import make_preset, set_presets
    from Path.Tool.toolbit.ui.editor import ToolBitEditor

    # Short texts, so that the Notes column is in the dialog at its default size.
    presets = [
        make_preset(name="Rough", material_name="6061", op_type="pocket",
                    surface_speed=250.0, chipload=0.08),
        make_preset(name="Finish", material_name="6061", op_type="profile",
                    surface_speed=300.0, chipload=0.05, notes="Use coolant"),
        make_preset(name="Slot", material_name="1018", op_type="slot",
                    surface_speed=180.0, chipload=0.04),
    ]
    # The pointer of the off-screen display must not be on the dialog.
    QtGui.QCursor.setPos(0, 0)
    toolbit = cam_assets.get(TOOL)
    set_presets(toolbit.obj, presets)
    # ToolBitEditor.show() calls exec_(), which stops the capture. Show the dialog without the wait.
    editor = ToolBitEditor(toolbit, TOOL_NO)
    editor.form.show()
    editor.form.tabWidget.setCurrentIndex(editor.feeds_tab_idx)
    return editor


def select_preset(editor, name):
    """Select the row of the Preset with this name."""
    from PySide import QtCore

    table = editor.presets_tab.table
    table.selectRow(table.findItems(name, QtCore.Qt.MatchExactly)[0].row())
