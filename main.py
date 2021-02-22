import src.kanban as kanban
import src.kanbanitemdialog as psy 
from src.kanbanboardwindow import KanbanBoardWindow
from PySide2.QtWidgets import *

app = QApplication([])
kbb = kanban.KanbanBoard()
window=psy.KanbanItemDialog(kbb=kbb)
def closed():
    if window.result()==QDialog.DialogCode.Accepted:
        print(f"Accepted {window.item}")
        window.item.print()
    else:
        print("rejected")

# window.accepted.connect(closed)
# window.rejected.connect(closed)
# window.show()
henlo=KanbanBoardWindow(kbb)
henlo.resize(640,480)
henlo.show()
app.exec_()
