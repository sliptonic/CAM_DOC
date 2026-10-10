# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, tab: general."""
import os
import sys

PAGE = "job/job.adoc"
ALT = "Job task panel, General tab"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _panel

    _panel.capture_panel(shot, "General")
