# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the Machine recipes of this page: a saved Machine, and a Job that uses it."""
NAME = "Shop Router"


def save_machine():
    """Write Shop_Router.fcm, a 3-axis Machine with the linuxcnc Post, into the asset folder."""
    from Machine.models.machine import Machine, MachineFactory

    machine = Machine.create_3axis_config()
    machine.name = NAME
    machine.postprocessor_file_name = "linuxcnc"
    MachineFactory.save_configuration(machine)


def job_with_operations(shot):
    doc = shot.open_model("drilling-1")
    job = shot.new_job([doc.getObject("Body")])
    shot.new_operation("Path.Op.Gui.Profile", job)
    shot.new_operation("Path.Op.Gui.Drilling", job)
    doc.recompute()
    return job
