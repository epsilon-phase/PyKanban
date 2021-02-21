from PySide2.QtWidgets import *
from src.kanban import *
from src.kanbanitemdialog import *
from PySide2.QtCore import Signal,QEvent,Qt
from PySide2.QtGui import QMouseEvent,QCursor
from typing import Callable
class ClickableLabel(QLabel):
    clicked = Signal()
    def __init__(self,text:str="", parent:QLabel=None):
        super(ClickableLabel,self).__init__(text,parent)
        self.setAttribute(Qt.WA_Hover,True)
    
    def hoverEnter(self):
        font = self.font()
        font.setWeight(font.Bold)
        font.setUnderline(True)
        self.setFont(font)
        self.setCursor(Qt.PointingHandCursor)

    def hoverLeave(self):
        font = self.font()
        font.setWeight(font.Normal)
        font.setUnderline(False)
        self.setFont(font)
        self.setCursor(Qt.ArrowCursor)
        

    def event(self,event:QEvent)->None:
        
        if event.type()==QEvent.HoverEnter:
            self.hoverEnter()
        elif event.type()==QEvent.HoverLeave:
            self.hoverLeave()
        else:
            return super(ClickableLabel,self).event(event)
        return True

    def mouseMoveEvent(self,event:QMouseEvent)->None:
        if event.type()==QEvent.HoverEnter:
            self.hoverEnter()
        elif event.type()==QEvent.HoverLeave:
            self.hoverLeave()
            

    def mousePressEvent(self,event:QMouseEvent)->None:
        from PySide2.QtCore import Qt 
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super(ClickableLabel,self).mousePressEvent(event)

class KanbanWidget(QFrame):
    item:KanbanItem
    changed:Signal = Signal(QWidget,ItemState,ItemState)
    description: QLabel
    name:ClickableLabel
    # editButton:QPushButton
    finished:QCheckBox
    """
    Simple short display for kanban items :)
    """
    def __init__(self, parent:QWidget=None, kbi:KanbanItem=None):
        """
        :param parent: The parent widget
        :param kbi: The KanbanItem displayed
        """
        super(KanbanWidget,self).__init__(parent)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum,QSizePolicy.MinimumExpanding))
        self.setFrameShape(QFrame.StyledPanel)
        self.item=kbi
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.name = ClickableLabel()
        self.name.setToolTip(self.tr("Edit"))
        self.name.clicked.connect(self.openEditingDialog)
        layout.addWidget(self.name)
        
        self.description = QLabel()
        layout.addWidget(self.description)
        self.description.setWordWrap(True)

        self.finished =QCheckBox(self.tr("Finished"))
        self.finished.setEnabled(False)
        layout.addWidget(self.finished)

        self.editButton = QPushButton(self.tr("Edit"))
        self.editButton.clicked.connect(self.openEditingDialog)
        layout.addWidget(self.editButton)

        self.updateDisplay()




    def updateDisplay(self):
        self.name.setText(self.item.name)
        self.description.setText(self.item.description)
        self.finished.setChecked(self.item.completed)
        self.setFrameShadow(QFrame.Plain if not self.item.blocked() else QFrame.Sunken)

    def openEditingDialog(self)->None:
        self.priorState=self.item.state()
        self.dialog = KanbanItemDialog(self,self.item,self.item.board)
        self.dialog.finished.connect(self.finishDialog)
        self.dialog.open()

    def finishDialog(self,code):
        if code==QDialog.Accepted:
            self.updateDisplay()
            self.changed.emit(self,self.priorState,self.item.state())
