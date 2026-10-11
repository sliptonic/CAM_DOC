# SPDX-License-Identifier: LGPL-2.1-or-later
"""Library Manager dialog with the Default library selected in the library list."""
import os
import sys

PAGE = "tools/library-manager.adoc"
ALT = "Library Manager dialog with the Default Tool Library selected in the left pane and its Tool Bits in the right pane"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _manager

    editor = _manager.open_manager(shot)
    shot.widget(editor.form)
    editor.form.reject()
