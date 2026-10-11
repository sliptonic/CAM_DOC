# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolpath of a Profile operation around the outside of the model."""
PAGE = "operations/profile.adoc"
ALT = "Toolpath of a Profile operation around the outside of the model"


def capture(shot):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    shot.new_operation("Path.Op.Gui.Profile", job)
    shot.view(1200, 900)
