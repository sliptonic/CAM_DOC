# SPDX-License-Identifier: LGPL-2.1-or-later
"""Import Machine from MTConnect dialog, with the URL of an agent entered."""
PAGE = "output/machine.adoc"
ALT = "Import Machine from MTConnect dialog with the URL http://machine:5000/probe entered"


def capture(shot):
    import FreeCADGui
    from Machine.ui.mtconnect_import_dialog import MTConnectImportDialog

    dialog = MTConnectImportDialog(FreeCADGui.getMainWindow())
    dialog.show()
    dialog.source_edit.setText("http://machine:5000/probe")
    shot.widget(dialog)
    dialog.reject()
