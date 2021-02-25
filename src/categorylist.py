from PySide2.QtWidgets import *
from PySide2.QtGui import QColor
from src.kanban import *
class CategoryEditor(QDialog):
    board:KanbanBoard

    def __init__(self, board:KanbanBoard, parent:QWidget=None):
        super(CategoryEditor,self).__init__(parent)
        self.board = board
        self.grd = QGridLayout()

        self.listView = QListWidget()
        self.grd.addWidget(self.listView,1,0,1,1)
        self.setLayout(self.grd)

        self.categoryInput=QLineEdit()
        self.grd.addWidget(self.categoryInput,0,0,1,1)

        addCategory=QPushButton(self.tr("Add Category"))
        addCategory.clicked.connect(self.addCategory)
        self.grd.addWidget(addCategory,0,1,1,1)


        self.editbutton = QPushButton(self.tr("Edit category"))
        self.editbutton.clicked.connect(self.editCategory)
        self.grd.addWidget(self.editbutton,1,1,1,1)
        self.finished.connect(self.updateBoard)

        acceptButton = QPushButton(self.tr("Accept"))
        acceptButton.clicked.connect(self.accept)
        self.grd.addWidget(acceptButton,2,0,1,1)

        rejectButton = QPushButton(self.tr("Cancel"))
        rejectButton.clicked.connect(self.reject)
        self.grd.addWidget(rejectButton,2,1,1,1)

        self.populate()


    def populate(self)->None:
        """
        Fill the listview with categories from the kanbanboard
        and set their textcolors to reflect the category colors
        if assigned
        """
        print(self.board.categories)
        for i in self.board.categories:
            print(f"Found category {i}")
            item = QListWidgetItem(i,self.listView)
            if i in self.board.category_data.keys():
                color = self.board.category_data[i]
                item.setTextColor(color)
                item.setData(32,color)

    def addCategory(self)->None:
        """
        Handle the user clicking the "Add Category" button.

        Filters out empty input because, well, categories with no name
        set aren't useful for anyone
        """
        #Don't permit empty categories to be added, those aren't helpful
        if categoryInput.text() == "":
            return
        self.listView.addItem(self.categoryInput.text())
        self.categoryInput.setText("")


    def editCategory(self)->None:
        item = self.listView.selectedItems()[0]
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"Got valid color {color.red()}, {color.green()},{color.blue()}")
            item.setTextColor(color)
            item.setData(32,color)
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
            color = i.data(32)
            print("Category: "+name)

            if name not in self.board.categories:
                self.board.categories.add(name)
                print(f"Adding new category {name}")
            if color is None:
                continue
            self.board.category_data[name]=color
        
