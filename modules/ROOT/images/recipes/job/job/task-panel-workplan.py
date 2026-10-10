# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, tab: workplan."""
import os
import sys

PAGE = "job/job.adoc"
ALT = "Job task panel, Workplan tab, with a Profile and a Drilling Operation"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _panel

    _panel.capture_panel(shot, "Workplan")
