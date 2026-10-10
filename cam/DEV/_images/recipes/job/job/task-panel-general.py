# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, tab: general."""
import os
import sys

PAGE = "job/job.adoc"
ALT = "Job task panel, General tab"


def capture(shot):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../recipes-lib"))
    import job_panel

    job_panel.capture_panel(shot, "general")
