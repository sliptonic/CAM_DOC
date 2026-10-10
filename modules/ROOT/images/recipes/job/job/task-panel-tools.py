# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, tab: tools."""
import os
import sys

PAGE = "job/job.adoc"
ALT = "Job task panel, Tools tab, with one Tool Controller"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _panel

    _panel.capture_panel(shot, "Tools")
