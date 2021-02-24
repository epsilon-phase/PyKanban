import src.kanban as kanban
import src.kanbanitemdialog as psy 
from src.kanbanboardwindow import KanbanBoardWindow
import src.default_settings as defaults
from PySide2.QtWidgets import *
from PySide2.QtCore import QSettings

app = QApplication([])
app.setOrganizationName("VioletWhite")
app.setOrganizationDomain("github.com/epsilon-phase")
app.setApplicationName("Pykanban")

settings = QSettings()
defaults.initialize_to_defaults()

kbb = kanban.KanbanBoard()
henlo=KanbanBoardWindow(kbb)
henlo.resize(640,480)
henlo.show()
app.exec_()
