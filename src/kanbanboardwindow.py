from __future__ import annotations
from PySide2.QtWidgets import *
from PySide2.QtCore import QCoreApplication, Qt, Slot
from src.kanban import *
from src.kanbanwidget import KanbanWidget
from src.kanbanitemdialog import KanbanItemDialog
from typing import *


class LabeledColumn(QWidget):
    label: QLabel
    layout: QVBoxLayout

    def __init__(self, text: str):
        super(LabeledColumn, self).__init__()
        self.layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(label)
        self.setLayout(self.layout)

    def removeWidget(self, widget: QWidget)->None:
        self.layout.removeWidget(widget)

    def addWidget(self, widget: QWidget)->None:
        self.layout.addWidget(widget)


class KanbanBoardWidget(QScrollArea):
    kanbanWidgets: List[KanbanWidget]

    def __init__(self, k: KanbanBoard):
        super(KanbanBoardWidget, self).__init__()

        self.layout = QHBoxLayout()
        self.addItem = QPushButton(self.tr("Add new Item"))
        self.addItem.clicked.connect(self.openNewItem)
        self.layout.addWidget(self.addItem)
        self.availableColumn = LabeledColumn(self.tr("Available"))
        self.completedColumn = LabeledColumn(self.tr("Completed"))
        self.blockedColumn = LabeledColumn(self.tr("Blocked"))
        self.layout.addWidget(self.availableColumn)
        self.layout.addWidget(self.completedColumn)
        self.layout.addWidget(self.blockedColumn)
        self.root = QFrame()
        self.root.setLayout(self.layout)
        self.setWidgetResizable(True)
        self.board = k
        self.kanbanWidgets = []
        self.setWidget(self.root)
        self.populate()

    def addKanbanItem(self, k: KanbanItem)->None:
        state = k.state()
        widg = KanbanWidget(None, k)
        self.kanbanWidgets.append(widg)
        self.selectColumn(state).addWidget(widg)
        widg.changed.connect(self.widgetChange)

    def populate(self)->None:
        for i in self.board.items:
            self.addKanbanItem(i)

    def selectColumn(self, state: ItemState)->LabeledColumn:
        selection = self.availableColumn
        if state == ItemState.COMPLETED:
            selection = self.completedColumn
        elif state == ItemState.BLOCKED:
            selection = self.blockedColumn
        return selection

    def removeFrom(self, widget: QWidget, state: ItemState)->None:
        self.selectColumn(state).removeWidget(widget)

    def addTo(self, widget: QWidget, state: ItemState)->None:
        self.selectColumn(state).addWidget(widget)

    def widgetChange(self, widget: QWidget, fromState: ItemState, toState: ItemState)->None:
        self.removeFrom(widget, fromState)
        self.addTo(widget, toState)
        if toState == ItemState.COMPLETED:
            # AT some point it would be wise to accelerate this search somewhat, since it's linear time
            # Ofc, this is probably more than enough for most things :)
            for i in self.kanbanWidgets:
                if widget.item in i.item.depends_on:
                    self.widgetChange(i, ItemState.BLOCKED, i.item.state)

    def openNewItem(self, k: KanbanItem)->None:
        dialog = KanbanItemDialog(self, None, self.board)
        dialog.NewItem.connect(self.addKanbanItem)
        dialog.open()

    def newBoard(self, board: KanbanBoard)->None:
        for i in self.kanbanWidgets:
            for column in [self.availableColumn, self.blockedColumn, self.completedColumn]:
                column.removeWidget(i)
            i.deleteLater()
        self.kanbanWidgets.clear()
        self.board = board
        self.populate()


class KanbanBoardWindow(QMainWindow):
    kanban: KanbanBoardWidget

    def __init__(self, kb: KanbanBoard = None):
        super(KanbanBoardWindow, self).__init__()
        mb = self.menuBar()
        filemenu = mb.addMenu(self.tr("File"))
        new = filemenu.addAction(self.tr("New"))
        new.triggered.connect(self.newBoard)
        save = filemenu.addAction(self.tr("Save"))
        save.triggered.connect(self.openSave)
        load = filemenu.addAction(self.tr("Load"))
        load.triggered.connect(self.openLoad)
        self.kanban = KanbanBoardWidget(kb)
        self.setCentralWidget(self.kanban)
        self.setWindowTitle(self.tr("PyKanban"))

    def openSave(self):
        thing = QFileDialog.getSaveFileName(filter="Kanban Boards (*.kb)")
        print(thing)
        if thing[0] == "":
            return
        filename: str = thing[0]
        if not filename.endswith(".kb"):
            filename += ".kb"
        self.kanban.board.save(filename)

    def openLoad(self):
        from pickle import UnpicklingError
        thing = QFileDialog.getOpenFileName(filter="Kanban Boards(*.kb)")
        if thing[0] == '':
            return
        try:
            new_kanban = KanbanBoard.load(thing[0])
            self.kanban.newBoard(new_kanban)
        except UnpicklingError:
            print("Huh")

    def newBoard(self):
        kb = KanbanBoard()
        self.kanban.newBoard(kb)
        print("Should be cleared now")
        print(f"kanban board has {len(self.kanban.board.items)} items")
