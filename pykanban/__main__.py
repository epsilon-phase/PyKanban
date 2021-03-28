import pykanban.kanban as kanban
from pykanban.kanbanboardwindow import KanbanBoardWindow
import pykanban.default_settings as defaults
import pykanban.settingNames as settingNames
from PySide2.QtWidgets import *
from PySide2.QtCore import QSettings


def run():
    kbb = kanban.KanbanBoard()
    if bool(settings.value(settingNames.OPEN_LAST_USED_DOCUMENT)):
        val = settings.value(settingNames.LAST_DOCUMENT_USED)
        print(f"Found last document of {val}")
        try:
            if val is not None:
                kbb = kanban.KanbanBoard.load(val)
        except FileNotFoundError:
            pass
    henlo = KanbanBoardWindow(kbb)
    henlo.resize(640, 480)
    henlo.show()
    app.exec_()


if __name__ == '__main__':
    app = QApplication([])
    app.setOrganizationName("VioletWhite")
    app.setOrganizationDomain("github.com/epsilon-phase")
    app.setApplicationName("Pykanban")

    settings = QSettings()
    defaults.initialize_to_defaults()
    run()
