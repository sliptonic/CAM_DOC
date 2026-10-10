# SPDX-License-Identifier: LGPL-2.1-or-later
"""Shared by the recipes of this page: the name of the Post, and a saved Machine that uses it."""
POST = "fanuc"
NAME = "Fanuc Mill"


def save_machine():
    """Write Fanuc_Mill.fcm, a 3-axis Machine with the fanuc Post, into the asset folder."""
    from Machine.models.machine import Machine, MachineFactory

    machine = Machine.create_3axis_config()
    machine.name = NAME
    machine.postprocessor_file_name = POST
    MachineFactory.save_configuration(machine)
