# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Job task panel recipes: a Job with two Operations, and its task panel on one tab."""


def capture_panel(shot, tab):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    tc = job.Tools.Group[0]                       # feeds and speed, so that the Workplan shows times
    tc.HorizFeed = "600 mm/min"
    tc.VertFeed = "200 mm/min"
    tc.SpindleSpeed = 12000
    shot.new_operation("Path.Op.Gui.Profile", job)
    shot.new_operation("Path.Op.Gui.Drilling", job)
    doc.recompute()
    shot.widget(shot.job_panel(job, tab))
