# SPDX-License-Identifier: LGPL-2.1-or-later
"""Runs inside FreeCAD. Started by gypsy/capture.py; do not run it directly.

Applies the STYLE.md §10.3 capture preferences, runs one recipe, writes a JSON result, quits.
The recipe gets a Shot object:

    shot.settle(ms)          let the GUI process events
    shot.widget(w)           capture a dialog or panel whole, without the window frame
    shot.open_model(name)    open a copy of the model `name` of models/models.json; returns the document
    shot.new_job(models)     create a Job for the model objects, without the task panel
    shot.new_operation(m, j) create the operation of GUI module m in Job j, without the task panel
    shot.view(w, h)          capture the 3D view: isometric, fitted, plain background
"""
import contextlib
import io
import json
import os
import shutil
import tempfile
import traceback

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

RECIPE = os.environ["GYPSY_RECIPE"]
OUT = os.environ["GYPSY_OUT"]
RESULT = os.environ["GYPSY_RESULT"]
REPO = os.environ["GYPSY_REPO"]


def set_preferences():
    """STYLE.md §10.3: axis cross off, navigation cube hidden, plain background, English, metric."""
    view = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
    view.SetBool("CornerCoordSystem", False)
    view.SetBool("Gradient", False)
    view.SetBool("RadialGradient", False)
    view.SetBool("Simple", True)
    view.SetUnsigned("BackgroundColor", 0xFFFFFFFF)
    view.SetBool("ShowNaviCube", False)
    view.SetBool("UseAutoRotation", False)
    FreeCAD.ParamGet("User parameter:BaseApp/Preferences/NaviCube").SetBool("ShowNaviCube", False)
    FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General").SetString("Language", "English")
    FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").SetInt("UserSchema", 0)
    # No animation: a capture must not catch a view half-way through a move.
    view.SetBool("UseNavigationAnimations", False)


def first_start():
    """A new profile opens the first-start page. Select the light theme there, as a new user
    does, and close the page; this is what applies the theme's style sheet."""
    mw = FreeCADGui.getMainWindow()
    for text in ("FreeCAD Light", "Done"):
        for button in mw.findChildren(QtWidgets.QAbstractButton):
            if button.text().replace("&", "") == text and button.isVisible():
                button.click()
                QtWidgets.QApplication.processEvents()
                break


class Shot:
    def __init__(self, out):
        self.out = out
        self.saved = False
        self.model = None

    def settle(self, ms=400):
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(ms, loop.quit)
        loop.exec_()

    def widget(self, w):
        self.settle()
        # No keyboard focus in a figure: no text cursor and no selected text.
        focus = QtWidgets.QApplication.focusWidget()
        if focus is not None:
            if isinstance(focus, QtWidgets.QLineEdit):
                focus.deselect()
            focus.clearFocus()
            self.settle(100)
        if not w.grab().save(self.out, "PNG"):
            raise RuntimeError(f"cannot write {self.out}")
        self.saved = True

    def open_model(self, name):
        """Open a copy of the test model `name`, an entry in models/models.json."""
        with open(os.path.join(REPO, "models", "models.json"), encoding="utf-8") as fh:
            models = json.load(fh)
        if name not in models:
            raise KeyError(f"no such model in models/models.json: {name}")
        src = os.path.join(REPO, "models", models[name]["file"])
        # Work on a copy, so a recipe cannot change the committed model.
        work = os.path.join(tempfile.mkdtemp(prefix="gypsy-model-"), models[name]["file"])
        shutil.copy(src, work)
        self.model = name
        doc = FreeCAD.openDocument(work)
        self.settle()
        return doc

    def new_job(self, models):
        """Create a Job as the Job command does, without its task panel."""
        import Path.Main.Gui.Job as GuiJob

        job = GuiJob.Create(models, openTaskPanel=False)
        self.settle()
        return job

    def new_operation(self, gui_module, job):
        """Create an operation with its view provider, as the toolbar command does, without
        the task panel. gui_module is the dotted name, for example "Path.Op.Gui.Profile"."""
        import importlib
        import Path.Op.Gui.Base as GuiBase

        res = importlib.import_module(gui_module).Command.res
        res.job = job
        op = res.objFactory(res.name, obj=None, parentJob=job)
        op.ViewObject.Proxy = GuiBase.ViewProvider(op.ViewObject, res)
        op.ViewObject.Proxy.deleteOnReject = False
        op.ViewObject.Visibility = True
        op.Document.recompute()
        self.settle()
        return op

    def view(self, width=1200, height=900, fit=None):
        """Capture the 3D view, isometric, fitted to `fit` (default: the Stock of the first Job,
        else everything)."""
        gui_doc = FreeCADGui.ActiveDocument
        if gui_doc is None:
            raise RuntimeError("no document is open; call shot.open_model() first")
        view = gui_doc.ActiveView
        if fit is None:
            stocks = [o.Stock for o in gui_doc.Document.Objects if getattr(o, "Stock", None)]
            fit = stocks[0] if stocks else None
        view.viewIsometric()
        FreeCADGui.Selection.clearSelection()
        if fit is not None:
            FreeCADGui.Selection.addSelection(fit)
            FreeCADGui.SendMsgToActiveView("ViewSelection")
            FreeCADGui.Selection.clearSelection()
        else:
            FreeCADGui.SendMsgToActiveView("ViewFit")
        self.settle(800)
        view.saveImage(self.out, width, height, "Current")
        if not os.path.exists(self.out):
            raise RuntimeError(f"cannot write {self.out}")
        self.saved = True


def run():
    result = {"ok": False, "freecad": FreeCAD.Version(), "user_dir": FreeCAD.getUserAppDataDir(),
              "user_cfg": FreeCAD.ConfigGet("UserParameter")}
    output = io.StringIO()
    try:
        first_start()
        set_preferences()
        FreeCADGui.activateWorkbench("CAMWorkbench")
        scope = {"__file__": RECIPE, "__name__": "gypsy_recipe"}
        with open(RECIPE, encoding="utf-8") as fh:
            exec(compile(fh.read(), RECIPE, "exec"), scope)
        shot = Shot(OUT)
        shot.settle(1000)
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            scope["capture"](shot)
        if not shot.saved:
            raise RuntimeError("the recipe did not capture an image")
        result.update(ok=True, model=shot.model,
                      page=scope.get("PAGE"), alt=scope.get("ALT"))
    except Exception:
        result["error"] = traceback.format_exc()
    result["output"] = output.getvalue()
    with open(RESULT, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    # Leave without the "save changes?" prompts of a normal close.
    os._exit(0)


QtCore.QTimer.singleShot(3000, run)
