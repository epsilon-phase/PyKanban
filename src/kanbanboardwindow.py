from __future__ import annotations
from PySide2.QtWidgets import *
from PySide2.QtCore import QCoreApplication, Qt, Slot
from PySide2.QtGui import QKeySequence
from src.kanban import *
from src.kanbanwidget import KanbanWidget
from src.kanbanitemdialog import KanbanItemDialog
from typing import *


class LabeledColumn(QScrollArea):
    label: QLabel
    layout: QVBoxLayout

    def __init__(self, text: str):
        super(LabeledColumn, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(label)

        self.toggleButton = QPushButton(self.tr("Collapse"))
        self.toggleButton.clicked.connect(self.toggleWidgetDisplay)
        self.layout.addWidget(self.toggleButton)
        
        frame = QFrame()
        frame.setLayout(self.layout)

        self.widgetArea = QVBoxLayout()
        self.widgetPanel = QFrame()
        self.widgetPanel.setLayout(self.widgetArea)
        self.layout.addWidget(self.widgetPanel)

        self.setWidgetResizable(True)

        self.setWidget(frame)

    def toggleWidgetDisplay(self)->None:
        self.toggleButton.setText(self.tr("Expand") 
                                  if self.widgetPanel.isVisible() else self.tr("Collapse")
                                  )
        self.widgetPanel.setVisible(not self.widgetPanel.isVisible())

    def addWidget(self, widget: QWidget)->None:
        self.widgetArea.addWidget(widget)


class KanbanBoardWidget(QFrame):
    kanbanWidgets: List[KanbanWidget]

    def __init__(self, k: KanbanBoard):
        super(KanbanBoardWidget, self).__init__()

        self.mainlayout = QHBoxLayout()

        mainpanel = QFrame()
        mainpanel.setLayout(self.mainlayout)

        utilityPanel = QFrame()
        utilityLayout = QVBoxLayout()
        utilityPanel.setLayout(utilityLayout)
        
        self.addItem = QPushButton(self.tr("Add new Item"))
        self.addItem.clicked.connect(self.openNewItem)
        utilityLayout.addWidget(self.addItem)

        self.searchText= QLineEdit()
        utilityLayout.addWidget(self.searchText)
        self.searchText.textChanged.connect(self.filterChanged)



        self.availableColumn = LabeledColumn(self.tr("Available"))
        self.completedColumn = LabeledColumn(self.tr("Completed"))
        self.blockedColumn = LabeledColumn(self.tr("Blocked"))
        self.mainlayout.addWidget(self.availableColumn)
        self.mainlayout.addWidget(self.completedColumn)
        self.mainlayout.addWidget(self.blockedColumn)
        # self.root = QFrame()
        # self.root.setLayout(self.layout)
        # self.setWidgetResizable(True)
        self.board = k
        self.kanbanWidgets = []
        
        splitter = QSplitter()
        splitter.addWidget(utilityPanel)
        splitter.addWidget(mainpanel)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(splitter)
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
        """
        Obtain the appropriate column for a widget to end up in given its item state
        :param state: The state of the kanbanitem the widget contains
        """
        selection = self.availableColumn
        if state == ItemState.COMPLETED:
            selection = self.completedColumn
        elif state == ItemState.BLOCKED:
            selection = self.blockedColumn
        return selection

    def filterChanged(self):
        query = self.searchText.text()
        self.board.for_each_by_matching(lambda x,y:x.widget.setVisible(y),query)

    def removeFrom(self, widget: QWidget, state: ItemState)->None:
        self.layout().removeWidget(widget)

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
                    self.widgetChange(i, ItemState.BLOCKED, i.item.state())

    def openNewItem(self, k: KanbanItem)->None:
        dialog = KanbanItemDialog(self, None, self.board)
        dialog.NewItem.connect(self.addKanbanItem)
        dialog.open()

    def newBoard(self, board: KanbanBoard)->None:
        for i in self.kanbanWidgets:
            self.layout().removeWidget(i)
            i.deleteLater()
        self.kanbanWidgets.clear()
        self.board = board
        self.populate()


class KanbanBoardWindow(QMainWindow):
    kanban: KanbanBoardWidget

    def __init__(self, kb: KanbanBoard = None):
        super(KanbanBoardWindow, self).__init__()
        
        self.kanban = KanbanBoardWidget(kb)
        self.setCentralWidget(self.kanban)

        mb = self.menuBar()
        filemenu = mb.addMenu(self.tr("File"))

        new = filemenu.addAction(self.tr("New"))
        new.triggered.connect(self.newBoard)
        
        save = filemenu.addAction(self.tr("Save"))
        save.triggered.connect(self.openSave)
        save.setShortcut(QKeySequence("Ctrl+S"))

        saveAs = filemenu.addAction(self.tr("Save As"))
        saveAs.triggered.connect(self.openSaveAs)
        saveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))

        load = filemenu.addAction(self.tr("Load"))
        load.triggered.connect(self.openLoad)

        boardmenu = mb.addMenu(self.tr("Board"))

        addItem = boardmenu.addAction(self.tr("add item"))
        addItem.triggered.connect(self.kanban.openNewItem)
        addItem.setShortcut(QKeySequence("Ctrl+a"))

        search_shortcut = QShortcut(QKeySequence("Ctrl+F"),self)
        search_shortcut.activated.connect(self.selectSearchBar)

        self.updateTitle()

    def updateTitle(self):
        title = self.tr("Pykanban")
        if self.kanban.board.filename is not None:
            title+=f": {self.kanban.board.filename}"
        self.setWindowTitle(title)

    def selectSearchBar(self):
        self.kanban.searchText.setFocus(Qt.ShortcutFocusReason)

    def getSaveFilename(self)->str:
        thing = QFileDialog.getSaveFileName(filter="Kanban Boards (*.kb)")
        print(thing)
        filename: str = thing[0]
        if filename == '':
            return filename
        if not filename.endswith(".kb"):
            filename += ".kb"
        return filename

    def openSave(self):
        filename = self.kanban.board.filename
        if self.kanban.board.filename is None:
            filename = self.getSaveFilename()
            if filename == '':
                return
        self.kanban.board.save(filename)
        self.updateTitle()


    def openSaveAs(self):
        filename = self.getSaveFilename()
        if filename=='':
            return
        self.kanban.board.save(filename)
        self.updateTitle()

    def openLoad(self):
        from pickle import UnpicklingError
        thing = QFileDialog.getOpenFileName(filter="Kanban Boards(*.kb)")
        if thing[0] == '':
            return
        try:
            new_kanban = KanbanBoard.load(thing[0])
            self.kanban.newBoard(new_kanban)
            self.updateTitle()
        except UnpicklingError:
            print("Huh")

    def newBoard(self):
        kb = KanbanBoard()
        self.kanban.newBoard(kb)
