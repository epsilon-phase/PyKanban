from __future__ import annotations
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt, QSettings, QTimer
from PySide2.QtGui import QKeySequence,QCloseEvent
from src.kanban import *
from src.kanbanwidget import KanbanWidget
from src.kanbanitemdialog import KanbanItemDialog
from src.categorylist import CategoryEditor
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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setWidget(frame)

    def toggleWidgetDisplay(self)->None:
        self.toggleButton.setText(self.tr("Expand") 
                                  if self.widgetPanel.isVisible() else self.tr("Collapse")
                                  )
        self.widgetPanel.setVisible(not self.widgetPanel.isVisible())

    def sort_widgets(self)->None:
        """
        Sort the kanbanwidgets by priority.
        """
        #At some point it would be a *very* good idea to rewrite this
        #so that it isn't O(n+nlog(n) complexity)
        widg = []
        for i in range(self.widgetArea.count()):
            i = self.widgetArea.itemAt(i).widget()
            if i is None:
                continue
            self.layout.removeWidget(i)
            widg.append(i)
        widg.sort(key=lambda x:x.item.priority)
        for i in widg:
            self.widgetArea.addWidget(i)

    def addWidget(self, widget: QWidget)->None:
        """
        Add a widget to the area under the label in the column.

        :param widget: The widget to add
        """
        self.widgetArea.addWidget(widget)
        self.sort_widgets()


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

        self.categoryButton = QPushButton(self.tr("Edit Categories"))
        self.categoryButton.clicked.connect(self.openCategoryEditor)
        utilityLayout.addWidget(self.categoryButton)

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
        widg = KanbanWidget(self, k)
        self.kanbanWidgets.append(widg)
        self.selectColumn(state).addWidget(widg)
        widg.updateDisplay()
        print(k.category)
        widg.changed.connect(self.widgetChange)
        self.setWindowModified(True)
        parent = self.window()
        if parent is not None:
            parent.setWindowModified(True)

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
        """
        Handle the aftermath of a kanbanwidget's update, move it to the 
        correct column, place it in the correct spot in the column, etc
        
        :param widget: The widget being changd
        :param fromState: The previous state of the widget
        :param toState: The new state of the widget
        """

        if fromState == toState:
            #Although the item may not have changed column,
            #the column may still need reordering
            self.selectColumn(fromState).sort_widgets()
            return
        self.removeFrom(widget, fromState)
        self.addTo(widget, toState)

        if toState == ItemState.COMPLETED:
            # AT some point it would be wise to accelerate this search somewhat, since it's linear time
            # Ofc, this is probably more than enough for most things :)
            for i in self.kanbanWidgets:
                if widget.item in i.item.depends_on:
                    self.widgetChange(i, ItemState.BLOCKED, i.item.state())


    def openNewItem(self, k: KanbanItem)->None:
        dialog = KanbanItemDialog(self, None, kbb=self.board)
        dialog.NewItem.connect(self.addKanbanItem)
        dialog.show()

    def openCategoryEditor(self)->None:
        c = CategoryEditor(self.board,self)
        c.show()
        c.finished.connect(self.updateCategories)

    def updateCategories(self)->None:
        for i in self.kanbanWidgets:
            if len(i.item.category)>0:
                i.updateDisplay()

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
        self.kanban.setParent(self)
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

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(1000*int(QSettings().value("Recovery/Interval")))
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start()
        # self.setWindowModified(True)
        self.updateTitle()

    def updateTitle(self):
        """
        Update the window's title to indicate the open file(when available)
        """
        title = self.tr("Pykanban")
        if self.kanban.board.filename is not None:
            title+=f": {self.kanban.board.filename}"
        else:
            title+=": Unsaved Document"
        title += '[*]'
        self.setWindowTitle(title)

    def selectSearchBar(self):
        if self.kanban.searchText.hasFocus():
            if self.kanban.searchText.selectionLength()>0:
                self.kanban.searchText.setText("")
            self.kanban.searchText.selectAll()
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
        from src.settingNames import LAST_DOCUMENT_USED
        filename = self.kanban.board.filename
        if self.kanban.board.filename is None:
            filename = self.getSaveFilename()
            if filename == '':
                return
        settings=QSettings()
        settings.setValue(LAST_DOCUMENT_USED,filename)
        self.kanban.board.save(filename)
        self.setWindowModified(False)
        self.updateTitle()

    def autosave(self):
        """
        Save the document if the document has changed and autosaving is enabled
        """
        print("Autosave :D")
        if self.isWindowModified() and bool(QSettings().value("Recovery/autosave")):
            if self.board.filename is not None:
                self.board.save()
                print("Autosaved :)")
                self.setWindowModified(False)

    def openSaveAs(self):
        from src.settingNames import LAST_DOCUMENT_USED
        filename = self.getSaveFilename()
        if filename=='':
            return
        settings=QSettings()
        self.kanban.board.save(filename)
        settings.setValue(LAST_DOCUMENT_USED,filename)
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

    def closeEvent(self, event:QCloseEvent)->None:
        if self.isWindowModified():
            print("Modified!")
            wants_save = QMessageBox.question(self, "Save", self.tr("Do you want to save?"),
                QMessageBox.Yes | QMessageBox.No)
            if wants_save == QMessageBox.Yes:
                self.openSave()
        event.accept()
