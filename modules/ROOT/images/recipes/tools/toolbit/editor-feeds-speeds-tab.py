# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbit Parameter Editor, Feeds & Speeds tab, for a Tool Bit that stores one Preset."""
import os
import sys

PAGE = "tools/toolbit.adoc"
ALT = "Toolbit Parameter Editor, Feeds & Speeds tab, with one Preset that has a note"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _toolbit
    from Path.Tool.FeedsSpeeds import make_preset

    # Short texts, so that the Notes column is in the dialog at its default size.
    preset = make_preset(name="Finish", material_name="6061", op_type="profile",
                         surface_speed=300.0, chipload=0.05, notes="Use coolant")
    editor = _toolbit.open_editor([preset])
    _toolbit.select_tab(editor, "Feeds & Speeds")
    shot.widget(editor.form)
    editor.form.reject()
