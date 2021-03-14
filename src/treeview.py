from PySide2.QtWidgets import *
from PySide2.QtGui import QPaintEvent, QPainter, QPainterPath, QColor
from PySide2.QtCore import Signal, QTimer, Qt, QEvent
from src.kanban import KanbanBoard, KanbanItem, ItemState
from src.kanbanwidget import KanbanWidget
from src.abstractview import AbstractView
from typing import *


class TreeArea(QFrame):
    def __init__(self, parent=None, board=None):
        super(TreeArea, self).__init__(parent)
        self.board = board
        self.lastLen = 0
        self.widgets = {}
        self.active = None
        self.setAttribute(Qt.WA_Hover, True)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            self.active = None
            for i in self.findChildren(KanbanWidget):
                if i.underMouse():
                    if self.active == i.parent():
                        self.active = None
                    else:
                        self.active = i.parent()
                        return True
                    self.repaint()
        return super(TreeArea, self).event(event)

    def paintEvent(self, event: QPaintEvent):
        """
        Draw lines to denote each item's parents/children
        """
        from PySide2.QtCore import QPointF
        path = QPainterPath(QPointF(0, 0))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        offset = 5.0
        if len(self.board.items) != self.lastLen:
            self.board.items[0].widget_of(self)
            self.widgets = {x: x.widget_of(self) for x in self.board.items}
            self.lastLen = len(self.board.items)
        else:
            pass
        widgets = self.widgets
        active = QPainterPath()
        for i in self.board.items:
            widget = widgets[i]
            widget = widget.parent()
            if not widget.parent().isVisible():
                continue
            x1, y1 = widget.pos().x(), widget.pos().y()
            x1 = x1 + widget.size().width() // 2
            y1 = y1 + widget.size().height()
            # Offset each edge by a different amount for each child
            offmod = 0
            for d in i.depends_on:
                child: QWidget = widgets[d]
                child = child.parent()
                if not child.isVisible():
                    continue
                x2, y2 = child.pos().x(), child.pos().y()
                x2 = x2 + child.size().width() // 2
                # if widget.underMouse() or child.underMouse() \
                if widget == self.active or child == self.active or widget.underMouse() or child.underMouse():
                    active.moveTo(x1, y1)
                    active.lineTo(x1, y1 + offset + offmod)
                    active.lineTo(x2, y1 + offset + offmod)
                    active.lineTo(x2, y2 - offset + offmod)
                    active.lineTo(x2, y2)
                    if x1 != x2:
                        active.moveTo((x2 + x1) // 2, y1 + offset + offmod + 5)
                        dir = 1 if x1 < x2 else -1
                        active.lineTo((x2 + x1) // 2 + 5 * dir, y1 + offset + offmod)
                        active.moveTo((x2 + x1) // 2, y1 - 5 + offset + offmod)
                        active.lineTo((x2 + x1) // 2 + 5 * dir, y1 + offset + offmod)
                    active.addEllipse(x2 - 2.5, y2 - 2.5, 5, 5)
                else:
                    path.moveTo(x1, y1)
                    path.lineTo(x1, y1 + offset + offmod)
                    path.lineTo(x2, y1 + offset + offmod)
                    path.lineTo(x2, y2 - offset + offmod)
                    path.lineTo(x2, y2)
                    path.addEllipse(x2 - 2.5, y2 - 2.5, 5, 5)
                offmod += 2
                offmod %= 30
        p = painter.pen()
        p.setWidthF(1.5)
        painter.setPen(p)
        painter.drawPath(path)
        p.setColor(Qt.darkYellow)
        painter.setPen(p)
        painter.drawPath(active)
        print(active.length())
        super(TreeArea, self).paintEvent(event)


class Collapser(QFrame):
    #: Emitted whenever the user clicks on the collapse button
    collapseToggle = Signal(QFrame)

    def __init__(self, parent=None):
        super(Collapser, self).__init__(parent)

        self.collapseButton = QPushButton(self.tr("Collapse"))
        self.collapseButton.clicked.connect(self.toggle)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.collapseButton)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.layout().setMargin(0)

    def toggle(self):
        if self.collapseButton.text() == self.tr("Collapse"):
            self.collapseButton.setText(self.tr("Expand"))
        else:
            self.collapseButton.setText(self.tr("Collapse"))
        self.collapseToggle.emit(self)

    def event(self, event: QEvent):
        if event.type() == QEvent.LayoutRequest and self.layout().count() == 1:
            self.deleteLater()
            self.parent().layout().removeWidget(self)
            p = self
            while not isinstance(p, TreeView):
                p = p.parent()
            p.relayout()
            return True
        return super(Collapser, self).event(event)

    def toggleButtonShown(self, show):
        self.collapseButton.setVisible(show)


class TreeView(AbstractView):
    board: KanbanBoard
    #: Association between each kanbanitem and the position assigned by the
    #: layout item
    positions: Dict[KanbanItem, Tuple[int, int]]
    #: The set of all kanbanitems whose children should not be considered in laying out the tree
    collapsed: Set[KanbanItem]
    #: The set of all kanbanitems considered completed for the sake of hiding
    completed: Set[KanbanItem]
    #: The combobox uses to select the root of the tree being shown
    itemChoice: QComboBox
    #: The checkbox which is used to control whether or not completed items
    #: are shown
    hiding_completed: QCheckBox
    #: The checkbox used to determine if the extra-aggressive space saving
    #: layout is used.
    extraCompactCheckbox: QCheckBox

    def __init__(self, parent: QWidget = None, board: KanbanBoard = None):
        super(TreeView, self).__init__(parent)
        assert board is not None
        self.board = board
        self.finishedAdding = False
        root = QFrame()
        root.setLayout(QVBoxLayout())

        headerFrame = QFrame()
        headerFrame.setLayout(QFormLayout())

        self.itemChoice = QComboBox()
        self.itemChoice.currentIndexChanged.connect(self.relayout)
        self.itemChoice.setEditable(True)
        self.itemChoice.setInsertPolicy(QComboBox.NoInsert)
        headerFrame.layout().addRow(self.tr("Root:"), self.itemChoice)

        self.hiding_completed = QCheckBox(self.tr("Hide Completed tasks"))
        self.hiding_completed.stateChanged.connect(self.relayout)
        headerFrame.layout().addWidget(self.hiding_completed)
        headerFrame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.extraCompactCheckbox = QCheckBox(self.tr("Extra Compact"))
        self.extraCompactCheckbox.stateChanged.connect(lambda _: self.relayout())
        self.extraCompactCheckbox.setToolTip(
            self.tr("Make the tree more compact, potentially at the cost of readability"))
        headerFrame.layout().addWidget(self.extraCompactCheckbox)

        root.layout().addWidget(headerFrame)

        display = TreeArea(self, board)
        self.grd = QGridLayout()
        self.grd.setVerticalSpacing(30)
        self.grd.setHorizontalSpacing(30)
        display.setLayout(self.grd)

        self.display = display
        print(display)

        display.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        scrl = QScrollArea()
        scrl.setWidget(display)
        scrl.setWidgetResizable(True)
        self.scrl = scrl
        root.layout().addWidget(scrl)

        self.setLayout(root.layout())

        self.positions = {}
        self.collapsed = set()
        self.completed = set()

    def get_eligible_widgets(self) -> List[KanbanWidget]:
        return list(filter(lambda x: x.parent().isVisible(), self.findChildren(KanbanWidget)))

    @property
    def hide_completed(self) -> bool:
        return self.hiding_completed.isChecked()

    @property
    def extraCompact(self) -> bool:
        """
        Returns true if the extra compact checkbox is checked.
        """
        return self.extraCompactCheckbox.isChecked()

    def addKanbanItem(self, k: KanbanItem) -> None:
        container = Collapser(self)
        widget = KanbanWidget(container, k)
        container.layout().addWidget(widget)
        self.grd.addWidget(container, 0, 0, 1, 1)
        container.setVisible(False)
        container.collapseToggle.connect(self.collapse)
        widget.setMinimumWidth(400)
        self.itemChoice.addItem(k.name, k)
        self.itemChoice.setItemData(self.itemChoice.count() - 1, k, 32)
        if self.finishedAdding:
            self.relayout(self.itemChoice.currentIndex())

    def collapse(self, collapser: Collapser):
        """
        Handle a widget signalling that it should be collapsed,
        that is:

        1. Add the widget's kanbanitem to the collapsed set
        2. Reassign the positions of each item
        3. Queue a timer event to ensure that the recently collapsed
           widget is still in the viewport
        """
        from functools import partial
        item = collapser.layout().itemAt(1).widget().item
        if item in self.collapsed:
            self.collapsed.remove(item)
        else:
            self.collapsed.add(item)
        self.relayout(self.itemChoice.currentIndex())
        # Due to the way that widget size/position are calculated, this
        # is, unfortunately, necessary.
        QTimer.singleShot(1, partial(self.scrl.ensureWidgetVisible, collapser))

    def determine_efficiency(self):
        max_x = 0
        max_y = 0
        for (x, y) in self.positions.values():
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        if max_x == 0 or max_y == 0:
            return
        print(f"Layout Efficiency: {100 * (len(self.positions) / (max_x * max_y))}%")

    def reposition_multi_child(self, k: KanbanItem, completed: bool, x: int, depth: int) -> Tuple[
        Tuple[int, int], Tuple[int, bool]]:
        """
        Single case of reposition, for when the task has more than one dependency

        :param k: The kanbanitem being considered
        :param completed: Whether it is possible for this to be completed for the purposes of layout
        :param x: The horizontal coordinate to be considered initially
        :param depth: The current vertical coordinate to be considered

        :returns: The resulting position of the task, the next x coordinate, 
            and whether or not the task should be considered completed for the
            purposes of layout
        """
        # Variables for centering the parent node over the children
        avgpos = 0
        avgcount = 0
        largest = 0
        viable = list(filter(lambda item: item not in self.positions and not (
                    item.state() == ItemState.COMPLETED and self.hide_completed), k.depends_on))
        non_viable = filter(lambda item: item in self.positions and item.depends_on == [], k.depends_on)
        if self.extraCompact:
            for z in range(x, max(0, x - len(viable) // 2), -1):
                if (z, depth + 1) in self.positions.values():
                    break
                x = z
        for i in viable:
            x2, c = self.reposition(i, x, depth + 1)
            if i not in self.positions:
                continue
            x = max(x2, x)
            completed = completed and c
            avgpos += self.positions[i][0]
            avgcount += 1
            largest = x
        if avgcount == 0:
            self.positions[k] = (x, depth)
            currentpos = x, depth
            ret = x + 1, completed
        else:
            avgpos //= avgcount
            currentpos = (avgpos, depth)
            ret = largest + 1, completed
        for i in non_viable:
            pos = self.positions[i][0], max(self.positions[i][1], depth + 1)
            if pos not in self.positions.values():
                self.positions[i] = pos
        return currentpos, ret

    def reposition(self, k: KanbanItem, x: int = 0, depth: int = 0) -> Tuple[int, bool]:
        """

        See :doc:`dag_layout` for a more intensive discussion of the issues
        at play here.
        
        Iterate across the graph comprising the kanbanboard,
        setting each item's position.

        :param k: The current item being positions
        :param x: The horizontal coordinate currently being assigned
        :param depth: The vertical coordinate currently being assigned
        :returns: The next available horizontal coordinate
        """
        currentpos = None
        ret: Tuple[int, bool] = 0, False
        completed = False
        if k.state() == ItemState.COMPLETED:
            completed = True
        if k in self.positions:
            print(f"double visited: {self.name}")
            ret = (x + 1, completed)
        elif k.depends_on == [] or k in self.collapsed or (completed and self.hide_completed):
            if k.depends_on == [] and completed and self.hide_completed:
                pass
            else:
                currentpos = (x, depth)
            ret = x + 1, completed
        elif len(k.depends_on) == 1:
            if k.depends_on[0] not in self.positions:
                x, c = self.reposition(k.depends_on[0], x, depth + 1)
                if completed and c:
                    self.completed.add(k)
                currentpos = (self.positions[k.depends_on[0]][0], depth)
                ret = currentpos[0] + 1, completed
            else:
                currentpos = x, depth
                self.positions[k] = (x, depth)
                ret = x + 1, completed
        else:  # Multiple children
            currentpos, (x, completed) = self.reposition_multi_child(k, completed, x, depth)
            ret = x, completed
        # Nudge the item a space over if necessary. Should, in general, avoid issues.
        if currentpos is not None:
            while currentpos in self.positions.values():
                print("Nudging")
                currentpos = currentpos[0] + 1, currentpos[1]
            self.positions[k] = currentpos
        if completed:
            self.completed.add(k)
        return ret

    def check_overlap(self) -> None:
        seen = set()
        for item, pos in self.positions.items():
            if pos in seen:
                print(f"Found doubled up position {item.name}")
            seen.add(pos)

    def remove_deleted(self):
        items = self.findChildren(Collapser)
        items = filter(lambda x: x.layout().count() == 1, items)
        for i in items:
            self.layout().removeWidget(i)
            i.deleteLater()

    def relayout(self, index=None):
        if index is None:
            index = self.itemChoice.currentIndex()
        items: List[KanbanWidget] = self.findChildren(KanbanWidget)
        self.remove_deleted()
        self.positions.clear()
        self.completed.clear()
        item = self.itemChoice.currentData(32)
        if item is None:
            return
        self.reposition(item)
        self.check_overlap()
        # Just in case the update takes a long time,
        # Don't draw during this time
        self.display.setUpdatesEnabled(False)
        for i in items:
            show = i.item in self.positions
            i.parent().setVisible(show)
            i.setEnabled(show)
            if show:
                self.grd.removeWidget(i.parent())
                pos = self.positions[i.item]
                self.grd.addWidget(i.parent(), pos[1], pos[0], 1, 1)
                i.parent().toggleButtonShown(len(i.item.depends_on) > 0)
        self.display.setUpdatesEnabled(True)
        self.display.update()
        self.determine_efficiency()
        self.positions.clear()

    def widgetChange(self, widget: KanbanWidget, fromState: ItemState, toState: ItemState):
        # Don't updating the layout unless the widget is visible
        if widget.item not in self.positions:
            return
        self.relayout(self.itemChoice.currentIndex())

    def scroll_to_result(self, widget: KanbanWidget):
        self.scrl.ensureWidgetVisible(widget)

    def updateCategories(self):
        for i in filter(lambda x: len(x.item.category) > 0, self.findChildren(KanbanWidget)):
            i.updateDisplay()

    def tabName(self) -> str:
        return "Tree"

    def populate(self) -> None:
        for i in self.board.items:
            self.addKanbanItem(i)
        self.relayout(self.itemChoice.currentIndex())
        self.finishedAdding = True

    def newBoard(self, board: KanbanBoard) -> None:
        for i in self.findChildren(KanbanWidget):
            self.layout().removeWidget(i)
            i.deleteLater()
        self.finishedAdding = False
        self.populate()
