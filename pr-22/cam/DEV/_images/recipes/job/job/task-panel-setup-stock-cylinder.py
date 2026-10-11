# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, tab: setup, with the Stock source set to Create cylinder."""
PAGE = "job/job.adoc"
ALT = "Job task panel, Setup tab, with the Stock set to Create cylinder and the Axis, Radius and Height controls"


def capture(shot):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    form = shot.job_panel(job, "Setup")
    stock = form.stock
    stock.setCurrentIndex(stock.findText("Create cylinder"))
    shot.widget(form)
