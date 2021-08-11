import sys
import argparse

import pykanban.kanban as kanban
from pykanban.kanbanboardwindow import KanbanBoardWindow
import pykanban.default_settings as defaults
import pykanban.settingNames as settingNames
from PySide2.QtWidgets import *
from PySide2.QtCore import QSettings


def run(filename: str):
    kbb = kanban.KanbanBoard()
    if not filename and bool(settings.value(settingNames.OPEN_LAST_USED_DOCUMENT)):
        filename = settings.value(settingNames.LAST_DOCUMENT_USED)
        print(f"Found last document of {filename}")
    try:
        if filename is not None:
            kbb = kanban.KanbanBoard.load(filename)
    except FileNotFoundError:
        pass
    window = KanbanBoardWindow(kbb)
    window.resize(1000, 1000)
    window.show()
    app.exec_()


if __name__ == '__main__':
    app = QApplication([])
    app.setOrganizationName("VioletWhite")
    app.setOrganizationDomain("github.com/epsilon-phase")
    app.setApplicationName("Pykanban")

    settings = QSettings()
    defaults.initialize_to_defaults()
    parser = argparse.ArgumentParser("Run pykanban")
    parser.add_argument("File", metavar='N', default=None, nargs='?',
                        help="The file to open")
    run(parser.parse_args().File)
