# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Preset recipes of this page: the editor of a library Tool Bit that has two
Presets, on the Feeds & Speeds tab."""


def open_presets_tab(shot):
    """Open the editor of the 5 mm Endmill that FreeCAD supplies, with two Presets, and select
    the Feeds & Speeds tab. Returns the ToolBitEditor; its `form` is the widget for
    shot.widget() and its `presets_tab` is the tab."""
    from Path.Tool.FeedsSpeeds import make_preset, set_presets
    from Path.Tool.camassets import cam_assets
    from Path.Tool.toolbit.ui.editor import ToolBitEditor

    toolbit = cam_assets.get("toolbit://5mm_Endmill")
    # The Notes column is narrow at the default size of the editor: short notes show in full.
    set_presets(toolbit.obj, [
        make_preset(name="Alu profile", material_name="Aluminum", op_type="profile",
                    surface_speed=300.0, chipload=0.05,
                    notes="Air blast"),
        make_preset(name="General", surface_speed=120.0, chipload=0.03,
                    notes="First cut"),
    ])
    # ToolBitEditor.show() opens the dialog with exec_(), which stops the capture. Show the
    # form of the editor without the wait.
    editor = ToolBitEditor(toolbit)
    editor.form.show()
    shot.settle()
    editor.form.tabWidget.setCurrentIndex(editor.feeds_tab_idx)
    shot.settle()
    return editor
