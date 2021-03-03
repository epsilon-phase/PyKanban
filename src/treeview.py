from PySide2.QtWidgets import *
from PySide2.QtCore import Qt
from src.kanban import KanbanBoard, KanbanItem, ItemState
from src.kanbanwidget import KanbanWidget
class TreeView(QFrame):
    def __init__(self,parent:QWidget=None,board:KanbanBoard=None):
        super(TreeView,self).__init__(parent)
        self.board = board
        root = QFrame()
        root.setLayout(QVBoxLayout())

        headerFrame = QFrame()
        headerFrame.setLayout(QFormLayout())

        self.itemChoice=QComboBox()
        self.itemChoice.currentIndexChanged.connect(self.relayout)
        headerFrame.layout().addRow(self.tr("Root:"),self.itemChoice)
        headerFrame.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        root.layout().addWidget(headerFrame)

        display = QFrame()
        self.grd = QGridLayout()
        display.setLayout(self.grd)
        
        self.display=display

        display.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding))
        scrl = QScrollArea()
        scrl.setWidget(display)
        scrl.setWidgetResizable(True)
        root.layout().addWidget(scrl)
        
        self.setLayout(root.layout())
        

    def addKanbanItem(self,k:KanbanItem)->None:
        widget = KanbanWidget(self,k)
        self.grd.addWidget(widget,0,0,1,1)
        widget.setVisible(False)
        widget.setMinimumWidth(400)
        self.itemChoice.addItem(k.name,k)
        self.itemChoice.setItemData(self.itemChoice.count()-1,k,32)
        print(k)
        print(f"Length of children: {len(self.display.children())}")
        # self.relayout(self.itemChoice.currentIndex())

    def relayout(self,index):
        print(index)
        items = self.findChildren(KanbanWidget)
        print(len(items))
        self.board.resetPositions()
        for i in self.board.items:
            if i.position is not None:
                print("Fuck, missed an item D:")
        item = self.itemChoice.currentData(32)
        if item is None:
            return
        item.reposition()
        for i in items:
            show = i.item.position is not None
            i.setVisible(show)
            i.setEnabled(show)
            if show:
                self.grd.removeWidget(i)
                self.grd.addWidget(i,i.item.position[1],i.item.position[0],1,1)
            else:
                print(f"{i.item.name} is hidden")
        seen = set()
        for i in items:
            if i.item.name == 'Fix combobox suggestions':
                i.hide()
            if i.item.position is None:
                continue
            if i in seen:
                print("Found position with more than one widget D:")

            seen.add(i.item.position)


    def widgetChange(self,widget:KanbanWidget, fromState:ItemState,toState:ItemState):
        self.relayout(self.itemChoice.currentIndex())

    def filterChanged(self,text:str):
        for i in self.findChildren(KanbanWidget):
            i.setVisible(i.position is not None and i.item.matches(text))

    def updateCategories(self):
        for i in filter(lambda x:len(x.item.category)>0,self.findChildren(KanbanWidget)):
            i.updateDisplay()

    def tabName(self)->str:
        return "Tree"
