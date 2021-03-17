from __future__ import annotations
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt, QSettings, QTimer
from PySide2.QtGui import QKeySequence, QCloseEvent
from src.kanban import *
from src.kanbanwidget import KanbanWidget
from src.kanbanitemdialog import KanbanItemDialog
from src.categorylist import CategoryEditor
from src.treeview import TreeView
from typing import *
from pickle import PicklingError
from src.abstractview import AbstractView
from src.optioneditor import OptionDialog
from src.widgets.labeled_column import LabeledColumn


class StatusView(QFrame, AbstractView):
    """
    Organizes tasks by their status, i.e. if the task is available
    to be done, blocked, or completed.
    """
    kanbanWidgets: List[KanbanWidget]

    def __init__(self, parent=None, board: KanbanBoard = None):
        super(StatusView, self).__init__(None)
        self.kanbanWidgets = []
        self.board = board
        self.mainlayout = QHBoxLayout()
        self.setLayout(self.mainlayout)
        self.availableColumn = LabeledColumn(self.tr("Available"))
        self.completedColumn = LabeledColumn(self.tr("Completed"))
        self.blockedColumn = LabeledColumn(self.tr("Blocked"))
        self.mainlayout.addWidget(self.availableColumn)
        self.mainlayout.addWidget(self.completedColumn)
        self.mainlayout.addWidget(self.blockedColumn)
        self.matching = []
        self.last_filter = None
        self.search_index = 0

    def selectColumn(self, state: ItemState) -> LabeledColumn:
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

    def addKanbanItem(self, k: KanbanItem) -> None:
        state = k.state()
        widg = KanbanWidget(None, k)
        self.kanbanWidgets.append(widg)
        self.selectColumn(state).addWidget(widg)
        widg.updateDisplay()
        widg.changed.connect(self.widgetChange)
        self.setWindowModified(True)
        parent = self.window()
        if parent is not None:
            parent.setWindowModified(True)

    def removeFrom(self, widget: QWidget, state: ItemState) -> None:
        self.layout().removeWidget(widget)

    def addTo(self, widget: QWidget, state: ItemState) -> None:
        self.selectColumn(state).addWidget(widget)

    def widgetChange(self, widget: QWidget, fromState: ItemState, toState: ItemState) -> None:
        """
        Handle the aftermath of a kanbanwidget's update, move it to the 
        correct column, place it in the correct spot in the column, etc
        
        :param widget: The widget being changed
        :param fromState: The previous state of the widget
        :param toState: The new state of the widget
        """
        print(f"{widget.item.name}: {fromState}->{toState}")

        if fromState == toState:
            # Although the item may not have changed column,
            # the column may still need reordering
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

    def populate(self) -> None:
        if self.board is None:
            return
        for i in self.board.items:
            self.addKanbanItem(i)

    def updateCategories(self) -> None:
        for i in self.kanbanWidgets:
            if len(i.item.category) > 0:
                i.updateDisplay()

    def newBoard(self, board: KanbanBoard) -> None:
        """
        Initialize widget listing with items
        """
        for i in self.kanbanWidgets:
            self.layout().removeWidget(i)
            i.deleteLater()
        self.kanbanWidgets.clear()
        self.board = board
        self.populate()

    def tabName(self) -> str:
        return self.tr("Status")

    def scroll_to_result(self, item:KanbanWidget):
        self.selectColumn(item.item.state()).ensureWidgetVisible(item,0,0)


class QueueView(LabeledColumn, AbstractView):
    kanbanWidgets: List[KanbanWidget]

    def __init__(self, parent: QWidget = None, board: KanbanBoard = None):
        super(QueueView, self).__init__("", parent)
        self.kanbanWidgets = []
        self.board = board
        self.matching = []
        self.last_filter = None
        self.search_index = 0

    def tabName(self) -> str:
        return self.tr("Queue")

    def newBoard(self, board) -> None:
        for i in self.widgetArea.children():
            i.deleteLater()
            self.widgetArea.removeWidget(i)
        self.populate()

    def widgetChange(self, widget: KanbanWidget) -> None:
        widget.setVisible(not (widget.item.completed or widget.item.blocked()))

    def populate(self) -> None:
        if self.board is None:
            return
        for i in self.board.items:
            widget = KanbanWidget(self, i)
            widget.setVisible(not (widget.item.completed or widget.item.blocked()))
            self.addWidget(widget)

    def scroll_to_result(self, item:KanbanWidget):
        self.ensureWidgetVisible(item)

    def addKanbanItem(self, k: KanbanItem) -> None:
        widg = KanbanWidget(kbi=k)
        widg.setVisible(not (widg.item.completed or widg.item.blocked()))
        self.addWidget(widg)

    def updateCategories(self) -> None:
        for i in self.findChildren(KanbanWidget):
            if len(i.item.category) > 0:
                i.updateDisplay()

    def get_eligible_widgets(self) -> List[KanbanWidget]:
        return list(filter(lambda x: x.isVisible(), self.findChildren(KanbanWidget)))


class KanbanBoardWidget(QFrame):
    """
    Toplevel container for views into the board.
    """
    kanbanWidgets: List[KanbanWidget]
    #: A list of views that are populated from the 
    #: board and updated accordingly
    views: List[Union[TreeView, QueueView, StatusView]]

    def __init__(self, k: KanbanBoard):
        super(KanbanBoardWidget, self).__init__()

        self.views = []
        self.views.append(StatusView(self, k))
        self.views.append(QueueView(self, k))
        self.views.append(TreeView(self, k))

        utilityPanel = QFrame()
        utilityPanel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        utilityLayout = QVBoxLayout()
        utilityPanel.setLayout(utilityLayout)

        self.addItem = QPushButton(self.tr("Add new Item"))
        self.addItem.clicked.connect(self.openNewItem)
        utilityLayout.addWidget(self.addItem)

        self.categoryButton = QPushButton(self.tr("Edit Categories"))
        self.categoryButton.clicked.connect(self.openCategoryEditor)
        utilityLayout.addWidget(self.categoryButton)

        labelledLayout = QFormLayout()

        self.searchText = QLineEdit()
        self.searchText.textChanged.connect(self.filterChanged)
        self.searchText.textChanged.connect(self.update_search_indicators)
        self.searchText.returnPressed.connect(self.filterChanged)
        self.searchText.returnPressed.connect(self.update_search_indicators)
        self.searchText.setClearButtonEnabled(True)

        labelledLayout.addRow(self.tr("Search"), self.searchText)

        searchNext = QPushButton(self.tr("Next"))
        searchNext.clicked.connect(lambda: [i.advance_search() for i in self.views])
        searchNext.clicked.connect(self.update_search_indicators)
        searchPrevious = QPushButton(self.tr("Previous"))
        searchPrevious.clicked.connect(lambda: [i.rewind_search() for i in self.views])
        searchPrevious.clicked.connect(self.update_search_indicators)
        self.searchNext, self.searchPrevious = searchNext, searchPrevious

        hlayout = QHBoxLayout()
        hlayout.addWidget(searchNext)
        hlayout.addWidget(searchPrevious)
        buttonPanel = QFrame()
        buttonPanel.setLayout(hlayout)
        labelledLayout.addWidget(buttonPanel)
        utilityLayout.addLayout(labelledLayout)

        self.board = k
        self.kanbanWidgets = []
        self.tab_container = QTabWidget()
        for i in self.views:
            self.tab_container.addTab(i, i.tabName())

        splitter = QSplitter()
        splitter.addWidget(utilityPanel)
        splitter.addWidget(self.tab_container)
        self.splitter = splitter

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(splitter)
        self.populate()

    def addKanbanItem(self, k: KanbanItem) -> None:
        """
        Dispatch the addition of new kanbanitems
        to views.

        :param k: The kanbanitem being added
        """
        print(self.views)
        for i in self.views:
            i.addKanbanItem(k)

    def populate(self) -> None:
        for v in self.views:
            v.populate()

    def filterChanged(self):
        """
        Dispatch filterChanged to each view
        """
        query = self.searchText.text()
        # board.for_each_by_matching(lambda x,y: (x.setVisible(y) for i in x.widget),query)
        for i in self.views:
            i.filterChanged(query)

    def update_search_indicators(self):
        cv = self.views[self.tab_container.currentIndex()]
        additional = ""
        if cv.search_index != -1:
            additional = f"{cv.search_index}/{len(cv.matching)}"
        self.searchNext.setText(self.tr("Next ") + additional)

    def openNewItem(self, k: KanbanItem) -> None:
        dialog = KanbanItemDialog(self, None, kbb=self.board)
        dialog.NewItem.connect(self.addKanbanItem)
        dialog.show()

    def openCategoryEditor(self) -> None:
        c = CategoryEditor(self.board, self)
        c.show()
        c.finished.connect(self.updateCategories)

    def updateCategories(self) -> None:
        for i in self.views:
            i.updateCategories()

    def newBoard(self, board: KanbanBoard) -> None:
        for i in self.views:
            i.newBoard(board)


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

        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.selectSearchBar)

        other = mb.addMenu(self.tr("&Other"))
        open_options = other.addAction(self.tr("Open Options"))
        open_options.triggered.connect(self.open_settings)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(1000 * QSettings().value("Recovery/Interval", 120, int))
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start()
        # self.setWindowModified(True)
        self.updateTitle()
        self.prompt_to_recover()

    def prompt_to_recover(self):
        """
        Ask the user if they want to load the .bak'd up autosave of the current file
        :return:
        """
        import os
        if self.kanban.board.filename and os.path.isfile(self.kanban.board.filename + '.bak'):
            choice = QMessageBox.question(self, "Recovery", self.tr("Do you want to load from an autosave?"),
                                          QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.kanban.newBoard(KanbanBoard.load(self.kanban.board.filename + '.bak'))

    def open_settings(self):
        settings_dialog = OptionDialog(self)
        settings_dialog.finished.connect(self.handle_setting_changes)
        settings_dialog.show()

    def handle_setting_changes(self, code):
        if code == QDialog.Rejected:
            return
        self.autosave_timer.setInterval(1000 * QSettings().value("Recovery/Interval", 100, int))

    def updateTitle(self):
        """
        Update the window's title to indicate the open file(when available)
        """
        title = self.tr("Pykanban")
        if self.kanban.board.filename is not None:
            title += f": {self.kanban.board.filename}"
        else:
            title += ": Unsaved Document"
        title += '[*]'
        self.setWindowTitle(title)

    def selectSearchBar(self):
        if self.kanban.searchText.hasFocus():
            if self.kanban.searchText.selectionLength() > 0:
                self.kanban.searchText.setText("")
            self.kanban.searchText.selectAll()
        self.kanban.searchText.setFocus(Qt.ShortcutFocusReason)

    def getSaveFilename(self) -> str:
        thing = QFileDialog.getSaveFileName(filter="Kanban Boards (JSON) (*.kb.json);;Kanban Boards (*.kb)")
        print(thing)
        filename: str = thing[0]
        if filename == '':
            return filename

        if thing[1] == 'Kanban Boards (*.kb)' and not filename.endswith('.kb'):
            filename += ".kb"
        elif not filename.endswith('.kb.json'):
            filename += ".kb.json"
        print(filename)
        return filename

    def openSave(self):
        import os
        from src.settingNames import LAST_DOCUMENT_USED
        filename = self.kanban.board.filename
        if self.kanban.board.filename is None:
            filename = self.getSaveFilename()
            if filename == '':
                return
        settings = QSettings()
        settings.setValue(LAST_DOCUMENT_USED, filename)
        try:
            self.kanban.board.save(filename)
        except PicklingError:
            QErrorMessage.showMessage("Failed to save, sorry :(")

        if os.path.isfile(self.kanban.board.filename + '.bak'):
            os.remove(self.kanban.board.filename + '.bak')
        self.setWindowModified(False)
        self.updateTitle()

    def autosave(self):
        """
        Save the document if the document has changed and autosaving is enabled
        """
        import gc
        gc.collect()
        if self.isWindowModified() and bool(QSettings().value("Recovery/AutoSave", False, bool)):
            print("Autosaving :D")
            if self.kanban.board.filename is not None:
                try:
                    self.kanban.board.save(self.kanban.board.filename + '.bak', False)
                except PicklingError:
                    QErrorMessage.showMessage("Failed to save, sorry :(")
                print("Autosaved :)")

    def openSaveAs(self):
        from src.settingNames import LAST_DOCUMENT_USED

        filename = self.getSaveFilename()
        if filename == '':
            return
        settings = QSettings()
        try:
            self.kanban.board.save(filename)
            settings.setValue(LAST_DOCUMENT_USED, filename)
        except PicklingError:
            QErrorMessage.showMessage("Failed to save, sorry :(")
        self.updateTitle()

    def openLoad(self):
        from pickle import UnpicklingError
        thing = QFileDialog.getOpenFileName(filter="Kanban Boards JSON (*.kb.json);;Kanban Boards(*.kb)")
        if thing[0] == '':
            return
        try:
            self.prompt_to_recover()
            new_kanban = KanbanBoard.load(thing[0])
            self.kanban.newBoard(new_kanban)
            self.updateTitle()
        except UnpicklingError:
            print("Huh")

    def newBoard(self):
        """
        Make a new board and clear the old ones.
        :return:
        """
        kb = KanbanBoard()
        self.kanban.newBoard(kb)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.isWindowModified():
            print("Modified!")
            wants_save = QMessageBox.question(self, "Save", self.tr("Do you want to save?"),
                                              QMessageBox.Yes | QMessageBox.No)
            if wants_save == QMessageBox.Yes:
                self.openSave()
        event.accept()
