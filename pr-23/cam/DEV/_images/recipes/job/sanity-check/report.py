# SPDX-License-Identifier: LGPL-2.1-or-later
"""Sanity Check report of a Job with one Profile operation, as the web browser shows it."""
PAGE = "job/sanity-check.adoc"
ALT = "Setup Report for CAM Job: Job, with the Run Summary table and the Squawks section"


def capture(shot):
    import os
    import tempfile
    import webbrowser

    import FreeCADGui
    from PySide import QtCore, QtWidgets
    from PySide6 import QtWebEngineWidgets

    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    shot.new_operation("Path.Op.Gui.Profile", job)

    # The file dialog waits for the user, and the command opens the report in the web browser
    # of the system. Give the file name without the dialog, and keep the path of the report.
    target = os.path.join(tempfile.mkdtemp(prefix="gypsy-sanity-"), "report.html")
    written = []
    QtWidgets.QFileDialog.getSaveFileName = lambda *args: (target, "")
    webbrowser.open_new_tab = written.append

    # The capture runs on an X11 display. The session of the person who runs it can be Wayland,
    # and then the report has no images.
    os.environ["XDG_SESSION_TYPE"] = "x11"

    FreeCADGui.Selection.clearSelection()
    FreeCADGui.Selection.addSelection(job)
    FreeCADGui.runCommand("CAM_Sanity")
    shot.settle(1000)

    # Show the report in a browser widget that is as high as the report, to capture it whole.
    browser = QtWebEngineWidgets.QWebEngineView()
    browser.resize(1100, 800)
    browser.show()
    browser.load(QtCore.QUrl.fromLocalFile(written[0]))
    shot.settle(4000)
    height = []
    browser.page().runJavaScript("document.documentElement.scrollHeight", 0, height.append)
    shot.settle(1000)
    browser.resize(1100, int(height[0]))
    shot.settle(3000)
    shot.widget(browser)
