# SPDX-License-Identifier: LGPL-2.1-or-later
"""CAM preferences, Assets page, with one saved Machine in the Machines list."""
PAGE = "reference/preferences.adoc"
ALT = "Assets page of the CAM preferences, with the Machines list and the buttons Add, Import..., Edit and Delete"


def capture(shot):
    from PySide import QtWidgets
    from Machine.models.machine import Machine, MachineFactory
    from Path.Tool.assets.ui.preferences import AssetPreferencesPage

    # One Machine in the asset folder, so that the list is not empty.
    machine = Machine.create_3axis_config()
    machine.name = "Shop Router"
    MachineFactory.save_configuration(machine)

    # The Preferences Editor is modal. Show the page that it contains in a plain dialog.
    page = AssetPreferencesPage()
    page.loadSettings()
    host = QtWidgets.QDialog()
    QtWidgets.QVBoxLayout(host).addWidget(page.form)
    # A plain dialog makes the first button its default button; the Preferences Editor does not.
    for button in page.form.findChildren(QtWidgets.QPushButton):
        button.setAutoDefault(False)
    host.show()
    shot.widget(host)
    host.reject()
