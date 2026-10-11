# SPDX-License-Identifier: LGPL-2.1-or-later
"""Machine Editor, Machine tab, with the Rotation Strategy list open."""
PAGE = "output/machine-configuration.adoc"
ALT = "Machine Editor, Machine tab, Kinematics group with the Rotation Strategy list open"


def capture(shot):
    from PySide import QtWidgets
    from Machine.ui.editor.machine_editor import MachineEditorDialog

    dialog = MachineEditorDialog()
    dialog.show()
    dialog.name_edit.deselect()
    dialog.rotation_strategy_combo.showPopup()
    shot.settle(800)
    # The open list is a window of its own, so shot.widget(dialog) does not show it.
    # Capture the area of the dialog from the screen.
    area = dialog.geometry()
    image = QtWidgets.QApplication.primaryScreen().grabWindow(
        0, area.x(), area.y(), area.width(), area.height())
    if not image.save(shot.out, "PNG"):
        raise RuntimeError(f"cannot write {shot.out}")
    shot.saved = True
    dialog.rotation_strategy_combo.hidePopup()
    dialog.reject()
