from PySide2.QtWidgets import *
from PySide2.QtGui import QBrush, QPixmap
from PySide2.QtCore import Qt
from pykanban.kanban import *
from pykanban.taskcategory import CategoryData


class CategoryEditor(QDialog):
    """
    List and edit categories in the current kanbanboard.

    Currently permits associating the category with a color.
    """
    #: The board populated from
    board: KanbanBoard

    def __init__(self, board:KanbanBoard, parent:QWidget=None):
        super(CategoryEditor,self).__init__(parent)
        self.board = board
        self.grd = QGridLayout()

        self.listView = QListWidget()
        self.listView.setSelectionMode(QListView.SingleSelection)
        self.grd.addWidget(self.listView,1,0,2,1)
        self.listView.itemSelectionChanged.connect(self.enable_disable_buttons)
        self.setLayout(self.grd)

        self.categoryInput=QLineEdit()
        self.grd.addWidget(self.categoryInput,0,0,1,1)

        addCategory=QPushButton(self.tr("Add Category"))
        addCategory.clicked.connect(self.addCategory)
        self.grd.addWidget(addCategory,0,1,1,1)


        self.editforeground = QPushButton(self.tr("Edit Foreground Color"))
        self.editforeground.clicked.connect(self.editCategoryForeground)
        self.grd.addWidget(self.editforeground,1,1,1,1)

        self.seticon = QPushButton(self.tr("Select Icon"))
        self.seticon.clicked.connect(self.setIconClicked)
        self.grd.addWidget(self.seticon,1,3,1,1)

        self.clearicon = QPushButton(self.tr("Clear Icon"))
        self.clearicon.clicked.connect(self.clearIconClicked)
        self.grd.addWidget(self.clearicon,2,3,1,1)

        self.editbackground = QPushButton(self.tr("Edit Background Color"))
        self.editbackground.clicked.connect(self.editCategoryBackground)
        self.grd.addWidget(self.editbackground,2,1,1,1)


        clearforeground = QPushButton(self.tr("Clear Foreground Color"))
        clearforeground.clicked.connect(self.clearForeground)
        self.grd.addWidget(clearforeground,1,2,1,1)
        self.clearforeground_button = clearforeground

        clearbackground = QPushButton(self.tr("Clear Background Color"))
        clearbackground.clicked.connect(self.clearBackground)
        self.grd.addWidget(clearbackground,2,2,1,1)
        self.clearbackground_button = clearbackground


        self.finished.connect(self.updateBoard)

        acceptButton = QPushButton(self.tr("Accept"))
        acceptButton.clicked.connect(self.accept)
        self.grd.addWidget(acceptButton,3,0,1,1)

        rejectButton = QPushButton(self.tr("Cancel"))
        rejectButton.clicked.connect(self.reject)
        self.grd.addWidget(rejectButton,3,1,1,1)

        self.populate()

    def enable_disable_buttons(self):
        enabled = len(self.listView.selectedItems())>0
        self.clearforeground_button.setEnabled(enabled)
        self.clearbackground_button.setEnabled(enabled)
        self.editbackground.setEnabled(enabled)
        self.editforeground.setEnabled(enabled)
        self.clearicon.setEnabled(enabled)
        self.seticon.setEnabled(enabled)

        if enabled:
            item = self.listView.selectedItems()[0]
            data = item.data(32)
            if data is not None:
                self.clearforeground_button.setEnabled(data.foreground is not None)
                self.clearbackground_button.setEnabled(data.background is not None)
                self.clearicon.setEnabled(data.icon is not None)
            else:
                self.clearforeground_button.setEnabled(False)
                self.clearbackground_button.setEnabled(False)
                self.clearicon.setEnabled(False)


    def populate(self)->None:
        """
        Fill the listview with categories from the kanbanboard
        and set their textcolors to reflect the category colors
        if assigned
        """
        from copy import copy
        print(self.board.categories)
        for i in self.board.categories:
            print(f"Found category {i}")
            item = QListWidgetItem(i,self.listView)
            if i in self.board.category_data.keys():
                data = copy(self.board.category_data[i])
                brush = QBrush()
                brush.setStyle(Qt.SolidPattern)
                if data.foreground is not None:
                    item.setTextColor(data.foreground)
                if data.background is not None:
                    brush.setColor(data.background)
                    item.setBackground(brush)
                item.setData(32,data)

    def addCategory(self)->None:
        """
        Handle the user clicking the "Add Category" button.

        Filters out empty input because, well, categories with no name
        set aren't useful for anyone
        """
        #Don't permit empty categories to be added, those aren't helpful
        if self.categoryInput.text() == "":
            return
        self.listView.addItem(self.categoryInput.text())
        self.categoryInput.setText("")



    def editCategoryForeground(self)->None:
        item = self.listView.selectedItems()[0]
        data = item.data(32)
        initialColor = None
        if data is not None:
            initialColor = data.foreground
        color = QColorDialog.getColor(initial=initialColor)
        if color.isValid():
            print(f"Got valid color {color.red()}, {color.green()},{color.blue()}")
            item.setTextColor(color)
            data = item.data(32)
            if data is None:
                data = CategoryData(color, None)
            data.foreground = color
            item.setData(32, data)
        else:
            print("Got invalid color :(")

    def clearForeground(self):
        if 0==len(self.listView.selectedItems()):
            return
        item = self.listView.selectedItems()[0]
        item.data(32).foreground=None
        item.setTextColor(self.palette().text().color())

    def clearBackground(self):
        if 0 == len(self.listView.selectedItems()):
            return
        item = self.listView.selectedItems()[0]
        item.data(32).background = None
        item.setBackground(QBrush())

    def setIconClicked(self)->None:
        item = self.listView.selectedItems()[0]
        file = QFileDialog.getOpenFileName(self,"Open Icon","", "Images (*.png *.jpg *.svg)")
        if file[0] == "":
            return
        if item.data(32) is None:
            item.setData(32,CategoryData())
        data=item.data(32)
        data.icon=QPixmap()
        data.icon.load(file[0])
        item.setData(32,data)

    def clearIconClicked(self):
        item = self.listView.selectedItems()[0]
        data = item.data(32)
        data.icon=None

    def editCategoryBackground(self)->None:

        item = self.listView.selectedItems()[0]
        initialColor=None
        data = item.data(32)
        if data is not None:
            initialColor=data.background
        color = QColorDialog.getColor(initial=initialColor)
        if color.isValid():
            print(f"Got valid color {color.red()}, {color.green()},{color.blue()}")
            brush:QBrush = QBrush()
            brush.setColor(color)
            brush.setStyle(Qt.SolidPattern)
            data = item.data(32)
            if data is None:
                data = CategoryData(None, color)
            data.background=color
            item.setData(32,data)
            item.setBackground(brush)
        else:
            print("Got invalid color :(")

    def updateBoard(self,code:int)->None:
        """
        Called when the user closes the dialog.

        When the user accepts the changes the board is updated
        to reflect the new state.

        :param code: The reason for why the dialog has closed, generally Accepted or Rejected
        """
        if code!=self.Accepted:
            return
        for i in range(self.listView.count()):
            i = self.listView.item(i)
            name = i.text()
            data = i.data(32)
            print("Category: "+name)

            if name not in self.board.categories:
                self.board.categories.add(name)
                print(f"Adding new category {name}")
            if data is None:
                continue
            #Clean up unassociated color data.
            if data.foreground is None and data.background is None and data.icon is None:
                del self.board.category_data[name]
            else:
                self.board.category_data[name]=data
        
