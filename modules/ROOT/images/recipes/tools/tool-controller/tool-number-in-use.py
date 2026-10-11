# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number In Use message: the Tool Number field of the editor of a second Tool Controller
set to the number of the first, which has a different Tool Bit."""
import os
import sys

PAGE = "tools/tool-controller.adoc"
ALT = "Tool Number In Use message with the text Tool number 1 is already used by TC: 5mm Endmill"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    from PySide import QtWidgets
    import Path.Tool.Gui.Controller as GuiController
    from Path.Tool.toolbit import ToolBit
    import _controller

    job = _controller.new_job(shot)
    drill = ToolBit.from_shape_id("drill.fcstd").attach_to_doc(doc=job.Document)
    drill_tc = GuiController.Create("TC: Drill", drill, 2)
    job.Proxy.addToolController(drill_tc)
    job.Document.recompute()

    # QMessageBox.warning() waits for the user, which stops the capture. Show the same
    # message without the wait.
    def warning(parent, title, text):
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, text,
                                    QtWidgets.QMessageBox.Ok, parent)
        box.show()
        shot.widget(box)
        box.close()

    QtWidgets.QMessageBox.warning = warning

    form = _controller.open_editor(shot, drill_tc)
    number = form.findChild(QtWidgets.QSpinBox, "tcNumber")
    number.setValue(1)                                 # the number of TC: 5mm Endmill
    number.editingFinished.emit()
