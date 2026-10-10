# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor for a new Machine, Postprocessor tab, fanuc Post selected, moved down to the
properties of the fanuc Post."""
import os
import sys

PAGE = "output/posts/fanuc.adoc"
ALT = "Machine Editor, Postprocessor tab, moved down to the eight properties of the fanuc Post at their defaults"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _machine
    from PySide import QtWidgets
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    dialog.tabs.setCurrentWidget(dialog.postprocessor_tab)
    combo = dialog.post_processor_combo
    combo.setCurrentIndex(combo.findText(_machine.POST))
    shot.settle()
    # Program Number is the first property of the fanuc Post. Move it to the top of the area.
    first = dialog.post_properties_widgets["program_number"]
    scroll = dialog.postprocessor_tab.findChild(QtWidgets.QScrollArea)
    bar = scroll.verticalScrollBar()
    y = first.mapTo(scroll.widget(), first.rect().topLeft()).y()
    bar.setValue(min(y - 10, bar.maximum()))
    shot.widget(dialog)
    dialog.reject()
