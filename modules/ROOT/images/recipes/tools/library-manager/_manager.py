# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Library Manager recipes: the Library Manager dialog with the Default library
selected, and Tool Bits with Drill subtypes in that library."""
LIBRARY = "Default"
DRILL = "toolbit://5mm_Drill"
SUBTYPES = {"jobber": "5mm Jobber Drill", "stub": "5mm Stub Drill", "spot": "5mm Spot Drill"}


def add_drill_subtypes():
    """Add one Tool Bit for each Drill subtype to the Default library. A user does this with
    the Adds a toolbit button and the type field of the Toolbit Parameter Editor."""
    from Path.Tool.camassets import cam_assets, ensure_assets_initialized
    from Path.Tool.toolbit import ToolBit

    ensure_assets_initialized(cam_assets)
    library = cam_assets.get(f"toolbitlibrary://{LIBRARY}", depth=1)
    attrs = cam_assets.get(DRILL).to_dict()
    for subtype, label in SUBTYPES.items():
        attrs.update({"id": label.replace(" ", "_"), "name": label, "shape-type": subtype})
        bit = ToolBit.from_dict(dict(attrs))
        cam_assets.add(bit)
        library.add_bit(bit)
    cam_assets.add(library)


def open_manager(shot):
    """Show the dialog as the Toolbit Library Manager command opens it, and select the Default
    library in the library list. Returns the LibraryEditor; the dialog is editor.form."""
    from PySide import QtCore, QtGui
    from Path.Tool.library.ui.editor import LibraryEditor

    # The pointer of the off-screen display must not highlight a row of the dialog.
    QtGui.QCursor.setPos(0, 0)
    # LibraryEditor.open() calls exec_(), which stops the capture. Show the dialog without the wait.
    editor = LibraryEditor()
    editor.form.show()
    shot.settle()
    libraries = editor.form.TableList
    row = libraries.model().match(libraries.model().index(0, 0), QtCore.Qt.DisplayRole, LIBRARY,
                                  1, QtCore.Qt.MatchExactly)[0]
    libraries.setCurrentIndex(row)
    libraries.clicked.emit(row)                    # what a click on the entry does
    shot.settle()
    return editor
