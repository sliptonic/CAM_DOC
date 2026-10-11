# SPDX-License-Identifier: LGPL-2.1-or-later
"""Property editor of the 45 degree Chamfer Tool Bit of the Default library in a Job."""
import FreeCADGui
from PySide import QtCore, QtWidgets

PAGE = "tools/tool-shape.adoc"
ALT = "Property editor of a Chamfer Tool Bit, Shape group, with the read-only Diameter property"


def capture(shot):
    import Path.Tool.Controller as Controller
    from Path.Tool.camassets import cam_assets

    # The property list is longer than the property editor of the default window.
    FreeCADGui.getMainWindow().resize(1600, 1500)
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    tool = cam_assets.get("toolbit://45degree_chamfer").attach_to_doc(doc)
    tool.ViewObject.Visibility = False
    job.Proxy.addToolController(Controller.Create(f"TC: {tool.Label}", tool, 10))
    doc.recompute()
    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(tool)
    shot.settle()

    mw = FreeCADGui.getMainWindow()
    editors = [w for w in mw.findChildren(QtWidgets.QTreeView)
               if w.metaObject().className() == "Gui::PropertyEditor::PropertyEditor" and w.isVisible()]
    editor = editors[0]
    rows = editor.model().match(editor.model().index(0, 0), QtCore.Qt.DisplayRole, "Diameter", 1,
                                QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
    editor.scrollTo(rows[0], QtWidgets.QAbstractItemView.PositionAtCenter)
    # Make the panel wider, as a user drags its edge, so that the property names are complete.
    dock = editor.parent()
    while not isinstance(dock, QtWidgets.QDockWidget):
        dock = dock.parent()
    mw.resizeDocks([dock], [420], QtCore.Qt.Horizontal)
    shot.settle()
    editor.resizeColumnToContents(0)
    shot.widget(editor)
