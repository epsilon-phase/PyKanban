import src.kanban as kanban
from src.kanbanboardwindow import KanbanBoardWindow
import src.default_settings as defaults
import src.settingNames as settingNames
from PySide2.QtWidgets import *
from PySide2.QtCore import QSettings

app = QApplication([])
app.setOrganizationName("VioletWhite")
app.setOrganizationDomain("github.com/epsilon-phase")
app.setApplicationName("Pykanban")

settings = QSettings()
defaults.initialize_to_defaults()
kbb = kanban.KanbanBoard()
if bool(settings.value(settingNames.OPEN_LAST_USED_DOCUMENT)):
    val=settings.value(settingNames.LAST_DOCUMENT_USED)
    print(f"Found last document of {val}")
    if val is not None:
        kbb=kanban.KanbanBoard.load(val)


henlo=KanbanBoardWindow(kbb)
henlo.resize(640,480)
henlo.show()
app.exec_()
