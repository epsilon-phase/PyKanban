from PySide2.QtWidgets import *
from PySide2.QtCore import Qt
from PySide2.QtGui import QPaintEvent,QPainter, QPainterPath
from src.kanban import KanbanBoard, KanbanItem, ItemState
from src.kanbanwidget import KanbanWidget
class TreeArea(QFrame):
    def __init__(self,parent=None,board=None):
        super(TreeArea,self).__init__(parent)
        self.board=board

    def paintEvent(self,event:QPaintEvent):
        from PySide2.QtCore import QPointF
        path = QPainterPath(QPointF(0,0))
        painter =QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i in self.board.items:
            widget:QWidget = i.widget_of(self)
            if not widget.isVisible():
                continue
            pos1 = widget.pos()
            pos1.setX(pos1.x()+widget.size().width()//2)
            pos1.setY(pos1.y()+widget.size().height())
            for d in i.depends_on:
                child:QWidget = d.widget_of(self)
                pos2 = child.pos()
                pos2.setX(pos2.x()+ child.size().width()//2)
                path.moveTo(pos1)
                path.lineTo(pos2)
        painter.drawPath(path)
        super(TreeArea,self).paintEvent(event)

class TreeView(QFrame):
    board:KanbanBoard 
    def __init__(self,parent:QWidget=None,board:KanbanBoard=None):
        super(TreeView,self).__init__(parent)
        self.board = board
        self.finishedAdding=False
        root = QFrame()
        root.setLayout(QVBoxLayout())

        headerFrame = QFrame()
        headerFrame.setLayout(QFormLayout())

        self.itemChoice=QComboBox()
        self.itemChoice.currentIndexChanged.connect(self.relayout)
        headerFrame.layout().addRow(self.tr("Root:"),self.itemChoice)
        headerFrame.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        root.layout().addWidget(headerFrame)

        display = TreeArea(self,board)
        self.grd = QGridLayout()
        self.grd.setVerticalSpacing(30)
        self.grd.setHorizontalSpacing(30)
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
        if self.finishedAdding:
            self.relayout(self.itemChoice.currentIndex())

    def relayout(self,index):
        items = self.findChildren(KanbanWidget)
        self.board.resetPositions()
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
        seen = set()
        for i in items:
            if i.item.position is None:
                continue
            if i in seen:
                print("Found position with more than one widget D:")

            seen.add(i.item.position)




    def widgetChange(self,widget:KanbanWidget, fromState:ItemState,toState:ItemState):
        self.relayout(self.itemChoice.currentIndex())

    def filterChanged(self,text:str):
        for i in self.findChildren(KanbanWidget):
            i.setVisible(i.item.position is not None and i.item.matches(text))

    def updateCategories(self):
        for i in filter(lambda x:len(x.item.category)>0,self.findChildren(KanbanWidget)):
            i.updateDisplay()

    def tabName(self)->str:
        return "Tree"

    def populate(self)->None:
        for i in self.board.items:
            self.addKanbanItem(i)
        self.relayout(self.itemChoice.currentIndex())
        self.finishedAdding=True

    def newBoard(self,board:KanbanBoard)->None:
        for i in self.findChildren(KanbanWidget):
            self.layout().removeWidget(i)
            i.deleteLater()
        self.finishedAdding=False
        self.populate()