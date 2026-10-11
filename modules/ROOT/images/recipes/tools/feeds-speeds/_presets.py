# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Feeds and Speeds recipes: the Toolbit Parameter Editor of the shipped 5mm
Endmill, with two Presets, on the Feeds && Speeds tab."""

# Two materials that Browse offers. Their names are short, so that the table shows whole in the
# dialog at its default size.
WOOD = "686e7021-2997-4b8e-92c3-d13f1a4ecf1e"
BRASS = "d7576c15-f8e8-43b1-9e56-2bf6b0f8338b"


def open_presets_tab(shot):
    """Open the Toolbit Parameter Editor and select the Feeds && Speeds tab. Returns the editor."""
    from Path.Tool.camassets import cam_assets
    from Path.Tool.FeedsSpeeds.presets import make_preset, set_presets
    from Path.Tool.Gui.MaterialPicker import lookup_material_name
    from Path.Tool.toolbit.ui import ToolBitEditor

    toolbit = cam_assets.get("toolbit://5mm_Endmill")
    # The Presets that a user adds with Add preset.
    set_presets(toolbit.obj, [
        make_preset(name="Wood", material_uuid=WOOD, material_name=lookup_material_name(WOOD),
                    op_type="slot", surface_speed=300.0, chipload=0.05, notes="Air blast"),
        make_preset(name="Brass", material_uuid=BRASS, material_name=lookup_material_name(BRASS),
                    surface_speed=120.0, chipload=0.03),
    ])
    # ToolBitEditor.show() opens the dialog with exec_(), which stops the capture. Show the
    # dialog of the editor without the wait.
    editor = ToolBitEditor(toolbit)
    editor.form.show()
    editor.form.tabWidget.setCurrentIndex(editor.feeds_tab_idx)
    shot.settle()
    return editor
