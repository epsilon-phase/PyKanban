from PySide2.QtWidgets import *
from src.kanban import *
from src.kanbanitemdialog import *
import src.settingNames as settingNames
from PySide2.QtCore import Signal,QEvent,Qt,QSettings
from PySide2.QtGui import QMouseEvent, QCursor, QPalette, QPixmap, QPaintEvent, QPainter
from typing import Callable
import re


class ClickableLabel(QLabel):
    """
    A QLabel that handles clicked and hover events.
    """
    clicked = Signal()
    def __init__(self,text:str="", parent:QLabel=None):
        super(ClickableLabel,self).__init__(text,parent)
        self.setAttribute(Qt.WA_Hover,True)
    
    def hoverEnter(self):
        font = self.font()
        font.setWeight(font.Bold)
        font.setUnderline(True)
        self.setFont(font)
        self.setCursor(Qt.PointingHandCursor)

    def hoverLeave(self):
        font = self.font()
        font.setWeight(font.Normal)
        font.setUnderline(False)
        self.setFont(font)
        self.setCursor(Qt.ArrowCursor)
        

    def event(self,event:QEvent)->bool:
        if event.type()==QEvent.HoverEnter:
            self.hoverEnter()
        elif event.type()==QEvent.HoverLeave:
            self.hoverLeave()
        else:
            return super(ClickableLabel,self).event(event)
        return True

    def mouseMoveEvent(self,event:QMouseEvent)->None:
        if event.type()==QEvent.HoverEnter:
            self.hoverEnter()
        elif event.type()==QEvent.HoverLeave:
            self.hoverLeave()
            
    def paintEvent(self,event:QPaintEvent):
        pix = self.pixmap()
        if pix is not None:
            p = QPainter(self)
            p.drawPixmap(0,0,pix)
        else:
            print("No pixmap :(")
        super(ClickableLabel,self).paintEvent(event)
    def mousePressEvent(self,event:QMouseEvent)->None:
        from PySide2.QtCore import Qt 
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super(ClickableLabel,self).mousePressEvent(event)


class KanbanWidget(QFrame):
    """
    Simple short display for kanban items :)
    """

    item:KanbanItem
    changed:Signal = Signal(QWidget,ItemState,ItemState)
    description: QTextEdit
    name:ClickableLabel
    finished:QCheckBox
    
    
    def __init__(self, parent:QWidget=None, kbi:KanbanItem=None):
        """
        :param parent: The parent widget
        :param kbi: The KanbanItem displayed
        """
        super(KanbanWidget,self).__init__(parent)
        if kbi is None:
            raise ValueError()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.MinimumExpanding))
        self.setFrameShape(QFrame.StyledPanel)
        self.item=kbi
        if self.item.widget is None:
            self.item.widget=[]

        self.item.widget.append(self)
        

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        name_ctr = QWidget()
        hbox =QHBoxLayout()
        hbox.setAlignment(Qt.AlignLeft)
        name_ctr.setLayout(hbox)

        self.icon = QLabel(name_ctr)
        name_ctr.layout().addWidget(self.icon)
        self.icon.setPixmap(self.style().standardPixmap(QStyle.SP_DesktopIcon).scaled(32, 32, Qt.KeepAspectRatio))

        self.name = ClickableLabel()
        self.name.setToolTip(self.tr("Edit"))
        self.name.clicked.connect(self.openEditingDialog)



        fn = self.name.font()
        # fn.setPointSizeF(1.2*fn.pointSizeF())
        self.name.setFont(fn)
        # self.name.setWordWrap(True)
        self.name.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        name_ctr.layout().addWidget(self.name,alignment=Qt.AlignTop|Qt.AlignLeft)

        layout.addWidget(name_ctr)
        
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        s=QSettings()

        line_count=int(str(s.value(settingNames.MAX_DESCRIPTION_LENGTH, 3)))
        self.description.setMaximumHeight(self.description.fontMetrics().height()*line_count)
        
        layout.addWidget(self.description,alignment=Qt.AlignTop)
        

        self.finished =QCheckBox(self.tr("Finished"))
        self.finished.setEnabled(False)
        layout.addWidget(self.finished)

        self.editButton = QPushButton(self.tr("Edit"))

        buttonContainer =QFrame()
        buttonContainer.setLayout(QHBoxLayout())
        self.editButton.clicked.connect(self.openEditingDialog)
        buttonContainer.layout().addWidget(self.editButton)

        createChildButton = QPushButton(self.tr("Add"))
        createChildButton.setToolTip(self.tr("Create Child task"))
        createChildButton.clicked.connect(self.createChildTask)

        complete = QPushButton(self.tr("Uncomplete" if self.item.completed else "Complete"))
        complete.clicked.connect(self.complete)
        self.completeButton = complete


        buttonContainer.layout().addWidget(createChildButton)
        buttonContainer.layout().addWidget(complete)

        layout.addWidget(buttonContainer)

        self.updateDisplay()



    def complete(self):
        self.item.completed=not self.item.completed
        self.updateDisplay()
        self.changed.emit(self, Priority.INVALID, self.item.state())
        self.completeButton.setText(self.tr("Uncomplete" if self.item.completed else "Complete"))

    def updateDisplay(self):
        """
        Update the displayed information from the KanbanItem associated with the
        widget.
        """
        self.name.setText(self.item.name + f"<br/> <small>[{','.join(self.item.category)}]</small>")
        self.name.updateGeometry()
        self.description.setText(self.item.description)
        self.finished.setChecked(self.item.completed)
        blocked = self.item.blocked()
        self.setFrameShadow(QFrame.Plain if not blocked else QFrame.Sunken)
        if blocked:
            self.setToolTip(self.tr('Blocked by') + "\n" + "\n".join(map(lambda x:x.short_name(),self.item.getBlockers())))
        if self.item.category is not None and len(self.item.category)>0:
            category = None
            for i in self.item.category:
                if i in self.item.board.category_data.keys():
                    category=i
                    break
            if category in self.item.board.category_data.keys():
                data = self.item.board.category_data[category]
                palette = self.palette()
                if data.foreground is not None:
                    foreground:QColor = data.foreground
                    palette.setColor(QPalette.Text, foreground)
                if data.background is not None:
                    background = data.background
                    palette.setColor(QPalette.Window,background)
                if data.icon is not None:
                    self.icon.setPixmap(data.icon)
            # self.setStyleSheet(stylesheet)
                self.setPalette(palette)
            self.setAutoFillBackground(True)

        self.updateGeometry()

    def openEditingDialog(self)->None:
        """
        Handle opening the editing dialog
        """
        self.priorState=self.item.state()
        #The reason we don't use this widget as the parent is because it causes
        #the dialog to adopt the background styling it currently has.
        #It honestly looks kinda nice, and might be worth doing, 
        #but for now it's a bug
        parent = self.parent
        if bool(QSettings().value(settingNames.USE_CATEGORY_STYLING)):
            parent = self
        self.dialog = KanbanItemDialog(parent, self.item,self.item.board)
        if bool(QSettings().value(settingNames.USE_CATEGORY_STYLING)):
            self.dialog.setPalette(self.palette())
        self.dialog.finished.connect(self.finishDialog)
        self.dialog.show()

    def createChildTask(self)->None:
        self.priorState = self.item.state()
        dialog = KanbanItemDialog(self, None, self.item.board)
        lw = QListWidgetItem(self.item.name,dialog.dependentsOfList)
        lw.setData(32,self.item)
        dialog.dependentsOfList.addItem(lw)
        dialog.NewItem.connect(self.window().kanban.addKanbanItem)
        dialog.finished.connect(self.finishDialog)
        dialog.show()

    def finishDialog(self,code):
        """
        Handle the editing dialog being closed, if it's accepted
        then it must also update the widget displays and emit a
        'changed' signal

        :param code: The way that this dialog finished, Accepted, Rejected, etc
        """
        if code==QDialog.Accepted:
            self.item.markChanged()

