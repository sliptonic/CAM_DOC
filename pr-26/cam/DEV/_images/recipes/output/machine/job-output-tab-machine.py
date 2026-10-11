# SPDX-License-Identifier: LGPL-2.1-or-later
"""Job task panel, Output tab, with a saved Machine selected in the Machine list."""
import os
import sys

PAGE = "output/machine.adoc"
ALT = "Job task panel, Output tab, with the Machine Shop Router selected and no Processor and Arguments rows"


def capture(shot):
    sys.path.insert(0, os.path.dirname(__file__))
    import _machine

    _machine.save_machine()
    job = _machine.job_with_operations(shot)
    panel = shot.job_panel(job, "Output")
    combo = job.ViewObject.Proxy.taskPanel.form.jobMachine
    combo.setCurrentIndex(combo.findText(_machine.NAME))
    shot.widget(panel)
