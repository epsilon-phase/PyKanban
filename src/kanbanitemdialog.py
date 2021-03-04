from src.kanban import KanbanItem, Priority, KanbanBoard
from PySide2.QtWidgets import *
from PySide2.QtCore import Signal, Qt
from typing import *

class CategorySelectDialog(QDialog):
    categories_selected = Signal(dict)
    categoryInput:QLineEdit
    categorySelector:QListWidget
    def __init__(self,k:KanbanItem,parent:QWidget=None):
        super(CategorySelectDialog,self).__init__(parent)
        self.item=k
        gridlayout=QGridLayout()

        self.categoryInput = QLineEdit()
        gridlayout.addWidget(self.categoryInput,0,0,1,1)
        self.categoryInput.returnPressed.connect(self.addCategory)

        addCategory = QPushButton(self.tr("Add Category"))
        addCategory.clicked.connect(self.addCategory)
        gridlayout.addWidget(addCategory,0,1,1,1)

        self.categorySelector = QListWidget()
        self.categorySelector.itemActivated.connect(self.changeItem)
        gridlayout.addWidget(self.categorySelector,1,0,1,2)

        acceptButton = QPushButton(self.tr("Accept"))
        acceptButton.clicked.connect(self.accept)
        gridlayout.addWidget(acceptButton,2,0,1,1)

        cancelButton=QPushButton(self.tr("Cancel"))
        cancelButton.clicked.connect(self.reject)
        gridlayout.addWidget(cancelButton,2,1,1,1)

        self.setLayout(gridlayout)

        self.finished.connect(self.acceptChanges)

        self.populate()

    def populate(self):
        """
        Grab the categories that exist and add them to the listviewwidget,
        checking them if they are in the current object's set
        """
        for i in self.item.board.categories:
            item = QListWidgetItem(i,self.categorySelector)
            item.setCheckState(Qt.Checked if i in self.item.category else Qt.Unchecked)

    def addCategory(self):
        cat = self.categoryInput.text()
        if cat == '':
            return
        item = QListWidgetItem(cat,self.categorySelector)
        item.setCheckState(Qt.Checked)
        self.categoryInput.setText("")

    def changeItem(self,item:QListWidgetItem):
        item.setCheckState(Qt.Unchecked if item.checkState()==Qt.Checked else Qt.Checked)

    def acceptChanges(self, code):
        if code!=self.Accepted:
            return
        result:Dict[str,bool] = dict()
        for i in range(self.categorySelector.count()):
            item = self.categorySelector.item(i)
            result[item.text()] = item.checkState()==Qt.Checked
        self.categories_selected.emit(result)


class KanbanItemDialog(QDialog):
    item: KanbanItem
    board: KanbanBoard
    #: Whether or not the dialog will append the new item to the board when 
    #: it is finished
    addAtEnd: bool
    #: Passes on the information that a new item was created by the dialog,
    #: probably indicating that the other UI needs updating to reflect that
    NewItem = Signal(KanbanItem)

    def updateFromItem(self)->None:
        """
        Update the control values from the item
        """
        self.nameEdit.setText(self.item.name)
        
        self.descEdit.setText(self.item.description)
        self.completed.setChecked(self.item.completed)
        for i in range(self.prioritySelect.count()):
            if self.prioritySelect.itemData(i)==self.item.priority:
                self.prioritySelect.setCurrentIndex(i)
                break

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
            "", "", kbb, Priority.MEDIUM,)
        self.board = kbb
        self.category_changeset = None
        layout = QFormLayout()

        self.setWindowTitle(self.tr("Editing: ")+(self.item.name if self.item.name !='' else self.tr("New Item")))


        self.nameEdit = QLineEdit("")
        layout.addRow(self.tr("Name"), self.nameEdit)

        self.descEdit = QTextEdit("")
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
        self.add_dependency_button.setToolTip(self.tr("Add dependency"))
        grdLayout.addWidget(self.add_dependency_button, 0, 1, 1, 1)
        self.add_dependency_button.clicked.connect(self.add_dependsOn)

        self.remove_dependency_button = QPushButton("-")
        self.remove_dependency_button.setToolTip(self.tr("Remove dependency"))
        self.remove_dependency_button.setEnabled(False)
        self.remove_dependency_button.clicked.connect(
            self.remove_button_clicked)
        grdLayout.addWidget(self.remove_dependency_button, 1, 1, 1, 1)

        self.dependencyList = QListWidget()
        self.dependencyList.setSelectionMode(QListWidget.SingleSelection)
        self.dependencyList.itemSelectionChanged.connect(
            self.updateSelectedList)
        self.dependencyList.setAlternatingRowColors(True)
        grdLayout.addWidget(self.dependencyList, 1, 0, 1, 1)



        container.setLayout(grdLayout)

        tabby = QTabWidget()
        tabby.addTab(container,self.tr("Depends On"))

        container2 = QFrame()

        grd2 = QGridLayout()

        self.dependentsOfChoice = QComboBox()
        grd2.addWidget(self.dependentsOfChoice,0,0,1,1)

        self.dependentsOfList = QListWidget()
        grd2.addWidget(self.dependentsOfList,1,0,1,1)

        dependentsOfAdd = QPushButton(self.tr("Add as dependent"))
        dependentsOfAdd.clicked.connect(self.add_dependent_of)
        grd2.addWidget(dependentsOfAdd,0,1,1,1)

        remove_dependent_button = QPushButton(self.tr("Remove dependent"))
        remove_dependent_button.clicked.connect(self.remove_dependent_of)
        grd2.addWidget(remove_dependent_button,1,1,1,1)

        container2.setLayout(grd2)

        tabby.addTab(container2,self.tr("Dependents of"))

        layout.addRow(self.tr("Dependencies"), tabby)

        self.completed = QCheckBox(self.tr("Completed"))
        layout.addRow("", self.completed)

        editCategory=QPushButton(self.tr("Edit categories"))
        editCategory.clicked.connect(self.openCategorySelector)
        layout.addWidget(editCategory)

        self.accept_button = QPushButton(self.tr("Accept"))
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.delete_button = QPushButton(self.tr("Delete"))
        self.accept_button.clicked.connect(self.updateItem)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.delete_button.clicked.connect(self.deleteItem)
        # self.delete_button.clicked.connect(self.reject)


        container = QFrame()
        hlayout = QHBoxLayout()

        hlayout.addWidget(self.accept_button)
        hlayout.addWidget(self.cancel_button)
        hlayout.addWidget(self.delete_button)
        container.setLayout(hlayout)

        layout.addWidget(container)

        self.setWindowModality(Qt.NonModal)
        self.setModal(False)
        self.updateFromItem()
        self.populateDependsOn()

    def deleteItem(self)->None:
        wanted = QMessageBox.question(self, "Delete", self.tr("Do you want to delete this item?"), 
            QMessageBox.Yes|QMessageBox.No)
        if wanted == QMessageBox.No:
            return
        if self.addAtEnd:
            return
        self.board.remove_item(self.item)
        self.reject()

    def hasChanged(self)->bool:
        i = self.item
        return i.name!= self.nameEdit.text() \
               or i.description!= self.descEdit.toPlainText() \
               or self.addAtEnd \
               or i.completed != (self.completed.checkState()==Qt.Checked)

    def updateItem(self)->None:
        """
        Update the KanbanItem from the widget values
        """
        if self.hasChanged():
            self.parent().window().setWindowModified(True)
        item = self.item
        item.name = self.nameEdit.text()
        item.description = self.descEdit.toPlainText()
        item.priority = self.prioritySelect.itemData(
            self.prioritySelect.currentIndex())
        item.depends_on.clear()
        for i in range(self.dependencyList.count()):
            item.depends_on.append(self.dependencyList.item(i).data(32))
        dependentsOf = map(lambda x:x.data(32), [self.dependentsOfList.item(i) for i in range(self.dependentsOfList.count())])
        dependentsOf = list(dependentsOf)

        for i in self.board.dependents_of(self.item):
            if item not in dependentsOf:
                i.depends_on.remove(item)

        for i in dependentsOf:
            if item not in i.depends_on:
                i.depends_on.append(item)

        from PySide2.QtCore import Qt
        item.completed = self.completed.checkState() == Qt.Checked

        if self.category_changeset is not None:
            print(self.category_changeset)
            item.category.clear()
            for cat,val in self.category_changeset.items():
                item.update_category(cat,val)
        if self.addAtEnd:
            self.board.add_item(item)
            self.NewItem.emit(item)
        self.accept()

    def add_dependsOn(self)->None:
        """
        Handle adding an item as selected in the combobox to the item's 
        dependencies
        """
        thing = self.dependsOnCombo.currentData()
        self.dependsOnCombo.removeItem(self.dependsOnCombo.currentIndex())
        item = QListWidgetItem(thing.short_name(), self.dependencyList)
        item.setText(thing.short_name())
        item.setData(32, thing)
        item.setCheckState(Qt.Checked if thing.completed else Qt.Unchecked)

    def add_dependent_of(self)->None:
        """
        Handle adding this item to the selected thing
        """
        thing = self.dependentsOfChoice.currentData()
        self.dependentsOfChoice.removeItem(self.dependentsOfChoice.currentIndex())
        item = QListWidgetItem(thing.short_name(), self.dependentsOfList)
        item.setText(thing.short_name())
        item.setData(32, thing)
        item.setCheckState(Qt.Checked if thing.completed else Qt.Unchecked)

    def remove_dependent_of(self)->None:
        thing = self.dependentsOfList.selectedItems()[0]
        self.dependentsOfList.takeItem(self.dependentsOfList.selectedIndexes()[0].row())
        thing = thing.data(32)
        self.dependentsOfChoice.addItem(thing.name,thing)

    def populateDependsOn(self)->None:
        """
        Populate available dependencies and trim existing ones
        """
        self.dependencyList.clear()
        self.dependsOnCombo.clear()
        self.dependentsOfList.clear()
        self.dependentsOfChoice.clear()
        for i in self.item.depends_on:
            item = QListWidgetItem(i.short_name())
            item.setData(32, i)
            item.setCheckState(Qt.Checked if i.completed else Qt.Unchecked)
            self.dependencyList.addItem(item)

        if self.board is None:
            return
        for i in self.board.items:
            if i.completed:
                continue
            if i in self.item.depends_on or i is self.item:
                continue
            if self.item in i.depends_on:
                item =QListWidgetItem(i.name)
                item.setData(32, i)
                self.dependentsOfList.addItem(item)
                continue
            else:
                self.dependentsOfChoice.addItem(i.name, i)
            self.dependsOnCombo.addItem(i.short_name(), i)

    def dependency_selector_changed_index(self, _)->None:
        """
        Update whether or not the add-dependency button is enabled
        based on whether or not the selected index is valid
        """
        self.add_dependency_button.setEnabled(
            self.dependsOnCombo.currentIndex() != -1)

    def updateSelectedList(self)->None:
        """
        Enable the remove-dependency button based on whether 
        or not there are items selected in the listbox
        """
        self.remove_dependency_button.setEnabled(
            len(self.dependencyList.selectedIndexes()) > 0)

    def remove_button_clicked(self)->None:
        """
        Handle actually removing the selected items from the selected dependencies
        """
        items = self.dependencyList.selectedItems()
        for i in items:
            self.dependencyList.takeItem(self.dependencyList.row(i))
            self.dependsOnCombo.addItem(i.data(32).short_name(), i.data(32))

    def openCategorySelector(self)->None:
        a=CategorySelectDialog(self.item,self)
        a.show()
        a.categories_selected.connect(self.updateCategories)

    def updateCategories(self,categories:Dict[str,bool])->None:
        self.category_changeset=categories
