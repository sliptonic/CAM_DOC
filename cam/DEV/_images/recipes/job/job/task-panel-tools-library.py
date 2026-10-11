# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Library dialog that Add on the Tools tab opens, with the All Tools view."""
PAGE = "job/job.adoc"
ALT = "Tool Library dialog with the All Tools view selected"


def capture(shot):
    from PySide import QtCore, QtWidgets
    from Path.Tool.library.ui.dock import ToolBitLibraryDock

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    shot.job_panel(job, "Tools")
    # Add opens the dialog with exec_(), which stops the capture. Create the same dialog and
    # show it without the wait.
    dock = ToolBitLibraryDock(job)
    dock.form.show()
    shot.settle()
    libraries = dock.browser_widget._library_combo
    libraries.setCurrentIndex(libraries.findText("All Tools"))
    # The pointer is on the dialog and highlights a row. Tell the list that the pointer left.
    tools = dock.browser_widget._tool_list_widget
    QtWidgets.QApplication.sendEvent(tools.viewport(), QtCore.QEvent(QtCore.QEvent.Leave))
    shot.widget(dock.form)
    dock.form.reject()
