# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Number In Use message: the Tool Number of a second Tool Controller set to the number
of the first, which has a different Tool Bit."""
import FreeCAD

PAGE = "job/job.adoc"
ALT = "Tool Number In Use message, which names the Tool Controller that has the number"


def capture(shot):
    from PySide import QtWidgets
    import Path.Tool.Gui.Controller as GuiController
    from Path.Tool.toolbit import ToolBit

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    drill = ToolBit.from_shape_id("drill.fcstd").attach_to_doc(doc=FreeCAD.ActiveDocument)
    job.Proxy.addToolController(GuiController.Create("TC: Drill", drill, 2))
    doc.recompute()

    # QMessageBox.warning() waits for the user, which stops the capture. Show the same
    # message without the wait.
    def warning(parent, title, text):
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, text,
                                    QtWidgets.QMessageBox.Ok, parent)
        box.show()
        shot.widget(box)
        box.close()

    QtWidgets.QMessageBox.warning = warning

    form = shot.job_panel(job, "Tools")
    form.toolControllerList.item(1, 1).setText("1")    # the Tool Number cell of TC: Drill
