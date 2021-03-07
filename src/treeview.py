from PySide2.QtWidgets import *
from PySide2.QtGui import QPaintEvent,QPainter, QPainterPath
from PySide2.QtCore import Signal
from src.kanban import KanbanBoard, KanbanItem, ItemState
from src.kanbanwidget import KanbanWidget
from typing import *

class TreeArea(QFrame):
    def __init__(self,parent=None,board=None):
        super(TreeArea,self).__init__(parent)
        self.board=board
        self.lastLen=0
        self.widgets={}

    def paintEvent(self,event:QPaintEvent):
        """
        Draw lines to denote each item's parents/children
        """
        from PySide2.QtCore import QPointF
        path = QPainterPath(QPointF(0,0))
        painter =QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        offset = QPointF(0, 5.0)
        if len(self.board.items)!=self.lastLen:
            self.widgets = {x:x.widget_of(self) for x in self.board.items}
            self.lastLen=len(self.board.items)
        widgets=self.widgets
        for i in self.board.items:
            widget = widgets[i]
            widget = widget.parent()
            if not widget.parent().isVisible():
                continue
            pos1 = widget.pos()
            pos1.setX(pos1.x()+widget.size().width()//2)
            pos1.setY(pos1.y()+widget.size().height())
            for d in i.depends_on:
                child:QWidget = widgets[d]
                child=child.parent()
                if not child.isVisible():
                    continue
                pos2 = child.pos()
                pos2.setX(pos2.x()+ child.size().width()//2)
                path.moveTo(pos1)
                path.lineTo(QPointF(pos1.x(),pos1.y()+offset.y()))
                path.lineTo(QPointF(pos2.x(),pos2.y()-offset.y()))
                path.lineTo(pos2)
                pos = path.currentPosition()
                path.addEllipse(pos.x()-2.5,pos.y()-2.5,5,5)
        p = painter.pen()
        p.setWidthF(1.5)
        painter.setPen(p)
        painter.drawPath(path)
        super(TreeArea,self).paintEvent(event)

class Collapser(QFrame):
    collapseToggle = Signal(QFrame)
    def __init__(self,parent=None):
        super(Collapser,self).__init__(parent)

        self.collapseButton = QPushButton(self.tr("Collapse"))
        self.collapseButton.clicked.connect(self.toggle)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.collapseButton)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)

    def toggle(self):
        if self.collapseButton.text() == self.tr("Collapse"):
            self.collapseButton.setText(self.tr("Expand"))
        else:
            self.collapseButton.setText(self.tr("Collapse"))
        self.collapseToggle.emit(self)


class TreeView(QFrame):
    board:KanbanBoard
    positions:Dict[KanbanItem,Tuple[int,int]]
    collapsed:Set[KanbanItem]
    def __init__(self,parent:QWidget=None,board:KanbanBoard=None):
        super(TreeView,self).__init__(parent)
        assert board is not None
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
        self.scrl = scrl
        root.layout().addWidget(scrl)

        
        self.setLayout(root.layout())

        self.positions = {}
        self.collapsed = set()
        

    def addKanbanItem(self,k:KanbanItem)->None:
        container = Collapser(self)
        widget = KanbanWidget(container,k)
        container.layout().addWidget(widget)
        self.grd.addWidget(container,0,0,1,1)
        container.setVisible(False)
        container.collapseToggle.connect(self.collapse)
        widget.setMinimumWidth(400)
        self.itemChoice.addItem(k.name,k)
        self.itemChoice.setItemData(self.itemChoice.count()-1,k,32)
        print(k)
        print(f"Length of children: {len(self.display.children())}")
        if self.finishedAdding:
            self.relayout(self.itemChoice.currentIndex())

    def collapse(self,collapser:Collapser):
        item = collapser.layout().itemAt(1).widget().item
        print(item)
        print(self.collapsed)
        if item in self.collapsed:
            self.collapsed.remove(item)
        else:
            self.collapsed.add(item)
        self.relayout(self.itemChoice.currentIndex())
        self.scrl.ensureWidgetVisible(collapser.layout().itemAt(1).widget())

    def reposition(self, k:KanbanItem,x:int=0,depth:int=0):
        if k in self.positions:
            print(f"double visited: {self.name}")
            return x+1
        if k.depends_on == [] or k in self.collapsed:
            self.positions[k]=(x,depth)
            return x+1
        if len(k.depends_on)==1:
            if k.depends_on[0] not in self.positions and k not in self.collapsed:
                x=self.reposition(k.depends_on[0],x,depth+1)
                self.positions[k]=(self.positions[k.depends_on[0]][0],depth)
            else:
                self.positions[k]=(x, depth)
            return x+1
        else:
            avgpos = 0 
            avgcount = 0
            largest = 0 
            for i in k.depends_on:
                if i in self.positions :
                    if i.depends_on == []:
                        self.positions[i] = (self.positions[i][0],
                                             max(self.positions[i][1],depth+1))
                    continue
                x=self.reposition(i,x,depth+1)
                avgpos += self.positions[i][0]
                avgcount += 1
                largest = x
            avgpos //= avgcount
            self.positions[k] = (avgpos,depth)
            return largest+1


    def relayout(self,index):
        items = self.findChildren(KanbanWidget)
        self.positions.clear()
        item = self.itemChoice.currentData(32)
        if item is None:
            return
        self.reposition(item)
        for i in items:
            show = i.item in self.positions
            i.parent().setVisible(show)
            i.setEnabled(show)
            if show:
                self.grd.removeWidget(i.parent())
                self.grd.addWidget(i.parent(),self.positions[i.item][1],self.positions[i.item][0],1,1)
        self.display.repaint()
        self.positions.clear()




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