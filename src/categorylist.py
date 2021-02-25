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
        self.grd.addWidget(self.listView)
        self.setLayout(self.grd)

        self.editbutton = QPushButton(self.tr("Edit category"))
        self.editbutton.clicked.connect(self.editCategory)
        self.grd.addWidget(self.editbutton,0,1,1,1)
        self.finished.connect(self.updateBoard)

        acceptButton = QPushButton(self.tr("Accept"))
        acceptButton.clicked.connect(self.accept)
        self.grd.addWidget(acceptButton,1,0,1,1)

        self.populate()


    def populate(self):
        print(self.board.categories)
        for i in self.board.categories:
            print(f"Found category {i}")
            item = QListWidgetItem(i,self.listView)
            if i in self.board.category_data.keys():
                color = self.board.category_data[i]
                item.setTextColor(color)
                item.setData(32,color)

    def editCategory(self)->None:
        item = self.listView.selectedItems()[0]
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"Got valid color {color.red()}, {color.green()},{color.blue()}")
            item.setTextColor(color)
            item.setData(32,color)
        else:
            print("Got invalid color :(")
        

    def updateBoard(self,code)->None:
        if code!=self.Accepted:
            return
        for i in range(self.listView.count()):
            i = self.listView.item(i)
            name = i.text()
            color = i.data(32)
            if color is None:
                continue
            self.board.category_data[name]=color
            print(self.board.category_data)
