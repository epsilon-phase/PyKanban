from src.kanban import KanbanBoard, KanbanItem
from PySide2.QtWidgets import QWidget, QFrame
from src.kanbanwidget import KanbanWidget
from typing import *


class AbstractView(QWidget):
    matching: List[KanbanWidget]

    def __init__(self, parent=None):
        super(AbstractView,self).__init__(parent)
        self.matching = []
        self.search_index = -1
        self.last_filter = None

    def filterChanged(self, text: str):
        if text != self.last_filter:
            if self.matching:
                self.apply_unselected_styling(self.currentSearchResult())
            self.matching.clear()
            for i in self.findChildren(KanbanWidget):
                if i.item.matches(text):
                    self.matching.append(i)
        if self.matching:
            self.advance_search()

    def scroll_to_result(self, item: KanbanWidget) -> None:
        """
        Ensure the relevant widget is in the view

        :param item: The widget to search for
        """
        raise NotImplementedError()

    def currentSearchResult(self) -> Optional[KanbanWidget]:
        if not self.matching:
            return None
        return self.matching[self.search_index]

    def apply_selected_styling(self, widget: KanbanWidget) -> None:
        widget.set_selected(True)

    def apply_unselected_styling(self, widget: KanbanWidget) -> None:
        widget.set_selected(False)

    def advance_search(self) -> None:
        """
        Move onto the next search result, if it exists.
        """
        if not self.matching:
            return
        prev = self.matching[self.search_index]
        self.apply_unselected_styling(prev)
        self.search_index += 1
        self.search_index %= len(self.matching)
        self.apply_selected_styling(self.currentSearchResult())
        self.scroll_to_result(self.currentSearchResult())

    def rewind_search(self):
        if not self.matching:
            return
        prev = self.matching[self.search_index]
        self.apply_unselected_styling(prev)
        self.search_index -= 1
        self.search_index %= len(self.matching)
        self.apply_selected_styling(self.currentSearchResult())
        self.scroll_to_result(self.currentSearchResult())
