from typing import Optional

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QScrollArea, QLabel, QVBoxLayout, QWidget, QPushButton, QFrame

from src.kanbanwidget import KanbanWidget


class LabeledColumn(QScrollArea):
    """
    Provide a column with a label, a scrollbar, a hide button, and,
    more usefully, a kanban priority sorting thing.
    """
    #: Displays whatever label is assigned
    label: QLabel
    vlayout: QVBoxLayout

    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super(LabeledColumn, self).__init__(parent)
        self.setObjectName("LabeledColumn: " + text)
        self.vlayout = QVBoxLayout()
        self.vlayout.setAlignment(Qt.AlignTop)
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.vlayout.addWidget(label)

        self.toggleButton = QPushButton(self.tr("Collapse"))
        self.toggleButton.clicked.connect(self.toggleWidgetDisplay)
        self.vlayout.addWidget(self.toggleButton)
        self.vlayout.setMargin(0)

        frame = QFrame()
        frame.setLayout(self.vlayout)

        self.widgetArea = QVBoxLayout()
        self.widgetPanel = QFrame()
        self.widgetPanel.setLayout(self.widgetArea)
        self.vlayout.addWidget(self.widgetPanel)
        self.widgetArea.setContentsMargins(0, 5, 0, 5)
        self.widgetPanel.setContentsMargins(0, 0, 0, 0)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setWidget(frame)

    def toggleWidgetDisplay(self) -> None:
        self.toggleButton.setText(self.tr("Expand")
                                  if self.widgetPanel.isVisible() else self.tr("Collapse")
                                  )
        self.widgetPanel.setVisible(not self.widgetPanel.isVisible())

    def sort_widgets(self) -> None:
        """
        Sort the kanbanwidgets by priority.
        """
        # At some point it would be a *very* good idea to rewrite this
        # so that it isn't O(n+nlog(n) complexity)
        widg = self.findChildren(KanbanWidget)
        for i in widg:
            self.vlayout.removeWidget(i)
        widg.sort(key=lambda x: x.item.priority)
        for i in widg:
            self.widgetArea.addWidget(i)

    def addWidget(self, widget: QWidget) -> None:
        """
        Add a widget to the area under the label in the column.

        :param widget: The widget to add
        """
        self.widgetArea.addWidget(widget)
        self.sort_widgets()
