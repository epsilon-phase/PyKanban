from PySide2.QtWidgets import *
from src.kanban import *
from src.kanbanitemdialog import *
from PySide2.QtCore import Signal
class KanbanWidget(QFrame):
    item:KanbanItem
    changed:Signal = Signal(QWidget,ItemState,ItemState)
    """
    Simple short display for kanban items :)
    """
    def __init__(self, parent=None,kbi:KanbanItem=None):
        super(KanbanWidget,self).__init__(parent)
        self.item=kbi
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.name = QLabel()
        layout.addWidget(self.name)
        self.description = QLabel()
        layout.addWidget(self.description)
        self.setFrameShape(QFrame.StyledPanel)

        self.editButton = QPushButton(self.tr("Edit"))
        self.editButton.clicked.connect(self.openEditingDialog)
        
        self.finished =QCheckBox(self.tr("Finished"))
        self.finished.setEnabled(False)
        
        layout.addWidget(self.finished)
        layout.addWidget(self.editButton)

        self.updateDisplay()

        

    def updateDisplay(self):
        self.name.setText(self.item.name)
        self.description.setText(self.item.description)
        self.finished.setChecked(self.item.completed)
        self.setFrameShadow(QFrame.Plain if not self.item.blocked() else QFrame.Sunken)

    def openEditingDialog(self):
        self.priorState=self.item.state()
        self.dialog = KanbanItemDialog(self,self.item,self.item.board)
        self.dialog.finished.connect(self.finishDialog)
        self.dialog.open()

    def finishDialog(self,code):
        if code==QDialog.Accepted:
            self.updateDisplay()
            self.changed.emit(self,self.priorState,self.item.state())
