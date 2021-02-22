from src.kanban import KanbanItem, Priority, KanbanBoard
from PySide2.QtWidgets import *
from PySide2.QtCore import QCoreApplication, Signal
translate = QCoreApplication.translate


class KanbanItemDialog(QDialog):
    item: KanbanItem
    board: KanbanBoard
    addAtEnd: bool
    NewItem: Signal = Signal(KanbanItem)

    def updateFromItem(self)->None:
        self.nameEdit.setText(self.item.name)
        self.descEdit.setText(self.item.description)
        self.prioritySelect.setCurrentIndex(self.item.priority)
        self.completed.setChecked(self.item.completed)
        self.populateDependsOn()

    def __init__(self, parent=None, kbI: KanbanItem = None, kbb: KanbanBoard = None):
        """
        Create a new KanbanItemDialog
        :param parent: The parent widget
        :param kbI: The KanbanItem(Not modified )
        :param kbb: The KanbanBoard that will draw data from
        """

        super(KanbanItemDialog, self).__init__(parent)
        self.addAtEnd = kbI is None
        self.item = kbI if kbI is not None else KanbanItem(
            "", "", Priority.MEDIUM, kbb)
        self.board = kbb
        layout = QFormLayout()

        self.nameEdit = QLineEdit(self.item.name)
        layout.addRow(self.tr("Name"), self.nameEdit)

        self.descEdit = QTextEdit(self.item.description)
        layout.addRow(self.tr('Description'), self.descEdit)

        self.prioritySelect = QComboBox()
        self.prioritySelect.addItem(self.tr("Low"), Priority.LOW)
        self.prioritySelect.addItem(self.tr("Medium"), Priority.MEDIUM)
        self.prioritySelect.addItem(self.tr("High"), Priority.HIGH)
        self.prioritySelect.setCurrentIndex(1)

        layout.addRow(self.tr("Priority"), self.prioritySelect)

        self.setLayout(layout)

        container = QFrame()
        grdLayout = QGridLayout()
        container.setLayout(grdLayout)

        self.dependsOnCombo = QComboBox()
        self.dependsOnCombo.currentIndexChanged.connect(
            self.dependency_selector_changed_index)
        grdLayout.addWidget(self.dependsOnCombo, 0, 0, 1, 1)

        self.add_dependency_button = QPushButton("+")
        grdLayout.addWidget(self.add_dependency_button, 0, 1, 1, 1)
        self.add_dependency_button.clicked.connect(self.add_dependsOn)

        self.remove_dependency_button = QPushButton("-")
        self.remove_dependency_button.setEnabled(False)
        self.remove_dependency_button.clicked.connect(
            self.remove_button_clicked)
        grdLayout.addWidget(self.remove_dependency_button, 1, 1, 1, 1)

        self.dependencyList = QListWidget()
        self.dependencyList.itemSelectionChanged.connect(
            self.updateSelectedList)
        self.dependencyList.setAlternatingRowColors(True)
        grdLayout.addWidget(self.dependencyList, 1, 0, 1, 1)

        self.populateDependsOn()

        container.setLayout(grdLayout)
        layout.addRow(self.tr("Dependencies"), container)

        self.completed = QCheckBox(self.tr("Completed"))
        layout.addRow("", self.completed)

        self.accept_button = QPushButton(self.tr("Accept"))
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.accept_button.clicked.connect(self.updateItem)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        container = QFrame()
        hlayout = QHBoxLayout()

        hlayout.addWidget(self.accept_button)
        hlayout.addWidget(self.cancel_button)
        container.setLayout(hlayout)

        layout.addWidget(container)

    def updateItem(self)->None:
        """
        Update the KanbanItem from the widget values
        """
        item = self.item
        item.name = self.nameEdit.text()
        item.description = self.descEdit.toPlainText()
        item.priority = self.prioritySelect.itemData(
            self.prioritySelect.currentIndex())
        item.depends_on.clear()
        for i in range(self.dependencyList.count()):
            item.depends_on.append(self.dependencyList.item(i).data(32))
        from PySide2.QtCore import Qt
        item.completed = self.completed.checkState() == Qt.Checked
        if self.addAtEnd:
            self.board.add_item(item)
            self.NewItem.emit(item)
        self.accept()

    def add_dependsOn(self)->None:
        thing = self.dependsOnCombo.currentData()
        self.dependsOnCombo.removeItem(self.dependsOnCombo.currentIndex())
        self.item.depends_on.append(thing)
        item = QListWidgetItem(thing.short_name(), self.dependencyList)
        item.setText(thing.short_name())
        item.setData(32, thing)

    def populateDependsOn(self)->None:
        self.dependencyList.clear()
        self.dependsOnCombo.clear()
        for i in self.item.depends_on:
            item = QListWidgetItem(i.short_name())
            item.setData(32, i)
            self.dependencyList.addItem(item)

        if self.board is None:
            return
        for i in self.board.items:
            if i in self.item.depends_on:
                continue
            self.dependsOnCombo.addItem(i.short_name(), i)

    def dependency_selector_changed_index(self, _)->None:
        self.add_dependency_button.setEnabled(
            self.dependsOnCombo.currentIndex() != -1)

    def updateSelectedList(self)->None:
        self.remove_dependency_button.setEnabled(
            len(self.dependencyList.selectedIndexes()) > 0)

    def remove_button_clicked(self)->None:
        items = self.dependencyList.selectedItems()
        for i in items:
            self.dependencyList.takeItem(self.dependencyList.row(i))
            self.dependsOnCombo.addItem(i.data(32).short_name(), i.data(32))
