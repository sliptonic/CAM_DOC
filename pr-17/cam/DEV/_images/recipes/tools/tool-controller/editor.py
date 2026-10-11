# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tool Controller Editor task panel of the Tool Controller of a new Job."""
import os
import sys

PAGE = "tools/tool-controller.adoc"
ALT = "Tool Controller Editor task panel, with the Controller Name, the feeds that include No-Engagement feed, the rapid rates and the Spindle group"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _controller

    job = _controller.new_job(shot)
    tc = job.Tools.Group[0]
    tc.HorizFeed = "600 mm/min"
    tc.VertFeed = "200 mm/min"
    tc.SpindleSpeed = 12000
    job.Document.recompute()
    shot.widget(_controller.open_editor(shot, tc))
