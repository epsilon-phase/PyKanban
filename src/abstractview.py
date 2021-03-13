from src.kanban import KanbanBoard, KanbanItem
from PySide2.QtWidgets import QWidget
from src.kanbanwidget import KanbanWidget
from typing import *


class AbstractView(QWidget):
    board: KanbanBoard

    def __init__(self, parent=None):
        super(AbstractView,self).__init__(parent)
        self.board = None
        self.matching = []
        self.search_index = -1
        self.last_filter = None

    def filterChanged(self, text:str):
        if text != self.last_filter:
            self.matching.clear()
            for i in self.findChildren(KanbanWidget):
                if i.item.matches(text):
                    self.matching.append(i)
        if self.matching:
            self.advance_search()

    def scroll_to_result(self, item:KanbanWidget):
        raise NotImplementedError()

    def currentSearchResult(self)->Optional[KanbanWidget]:
        if not self.matching:
            return None
        return self.matching[self.search_index]

    def advance_search(self):
        if not self.matching:
            return
        self.search_index += 1
        self.search_index %= len(self.matching)
        self.scroll_to_result(self.currentSearchResult())

    def rewind_search(self):
        if not self.matching:
            return
        self.search_index -= 1
        self.search_index %= len(self.matching)
        self.scroll_to_result(self.currentSearchResult())
