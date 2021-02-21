from tkinter import *

import src.kanban as kanban
import src.kanbanitemdialog as psy 
from src.kanbanboardwindow import KanbanBoardWindow
from PySide2.QtWidgets import *

app = QApplication([])
kbb = kanban.KanbanBoard()
kbb.add_item(kanban.KanbanItem("hello","",kanban.Priority.MEDIUM))
kbi1 = kanban.KanbanItem("henlo2","",kanban.Priority.LOW)
kbi1.depends_on.append(kbb.items[0])
kbb.add_item(kbi1)
window=psy.KanbanItemDialog(kbb=kbb)
def closed():
    if window.result()==QDialog.DialogCode.Accepted:
        print(f"Accepted {window.item}")
        window.item.print()
    else:
        print("rejected")

window.accepted.connect(closed)
window.rejected.connect(closed)
window.show()
henlo=KanbanBoardWindow(kbb)
henlo.show()
app.exec_()
