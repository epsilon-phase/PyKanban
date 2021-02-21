from __future__ import annotations
from PySide2.QtWidgets import *
from PySide2.QtCore import QCoreApplication,Qt
from src.kanban import *
from src.kanbanwidget import KanbanWidget 
from typing import *

class LabeledColumn(QWidget):
    label:QLabel
    layout:QVBoxLayout
    def __init__(self,text:str):
        super(LabeledColumn,self).__init__()
        self.layout=QVBoxLayout()
        label=QLabel(text)
        label.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.layout.addWidget(label)
        self.setLayout(self.layout)

    def removeWidget(self,widget:QWidget)->None:
        self.layout.removeWidget(widget)

    def addWidget(self,widget:QWidget)->None:
        self.layout.addWidget(widget)


class KanbanBoardWidget(QScrollArea):
    kanbanWidgets:List[KanbanWidget]

    def __init__(self,k:KanbanBoard):
        super(KanbanBoardWidget,self).__init__()
        
        self.layout = QHBoxLayout()
        self.availableColumn = LabeledColumn(self.tr("Available"))
        self.completedColumn = LabeledColumn(self.tr("Completed"))
        self.blockedColumn = LabeledColumn(self.tr("Blocked"))
        self.layout.addWidget(self.availableColumn)
        self.layout.addWidget(self.completedColumn)
        self.layout.addWidget(self.blockedColumn)
        self.board = k
        self.kanbanWidgets = []
        self.setLayout(self.layout)
        self.populate()


    def populate(self):
        for i in self.board.items:
            widg = KanbanWidget(None,i)
            self.kanbanWidgets.append(widg)
            state = i.state()
            if state == ItemState.BLOCKED:
                self.blockedColumn.addWidget(widg)
            elif state==ItemState.COMPLETED:
                self.completedColumn.addWidget(widg)
            else:
                self.availableColumn.addWidget(widg)
            widg.changed.connect(self.widgetChange)

    def selectColumn(self,state:ItemState)->LabeledColumn:
        selection=self.availableColumn
        if state==ItemState.COMPLETED:
            selection=self.completedColumn
        elif state==ItemState.BLOCKED:
            selection=self.blockedColumn
        return selection

    def removeFrom(self,widget:QWidget,state:ItemState)->None:
        self.selectColumn(state).removeWidget(widget)

    def addTo(self,widget:QWidget,state:ItemState)->None:
        self.selectColumn(state).addWidget(widget)

    def widgetChange(self,widget:QWidget,fromState:ItemState,toState:ItemState)->None:
        self.removeFrom(widget,fromState)
        self.addTo(widget,toState)
        if toState==ItemState.COMPLETED:
            # AT some point it would be wise to accelerate this search somewhat, since it's linear time
            # Ofc, this is probably more than enough for most things :)
            for i in self.kanbanWidgets:
                if widget.item in i.item.depends_on:
                    self.widgetChange(i,ItemState.BLOCKED,i.item.state)


class KanbanBoardWindow(QMainWindow):
    def __init__(self, kb:KanbanBoard=None):
        super(KanbanBoardWindow,self).__init__()

        self.setCentralWidget(KanbanBoardWidget(kb))
