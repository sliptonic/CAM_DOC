# SPDX-License-Identifier: LGPL-2.1-or-later
"""Warning message that the Output tab shows after you select an output file."""
PAGE = "job/job.adoc"
ALT = "Warning message with the text This will replace filename template, and the Ok and Cancel buttons"


def capture(shot):
    from PySide import QtWidgets

    # The file dialog and the message wait for the user, which stops the capture. Give the
    # file name without the dialog, and show the message without the wait.
    QtWidgets.QFileDialog.getSaveFileName = lambda *args: ("/tmp/part.nc", "")
    QtWidgets.QMessageBox.exec = lambda box: (box.show(), shot.widget(box))

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    form = shot.job_panel(job, "Output")
    form.postProcessorSetOutputFile.click()
