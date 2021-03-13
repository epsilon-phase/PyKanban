from src.kanban import KanbanBoard, KanbanItem
from PySide2.QtWidgets import QWidget, QFrame
from src.kanbanwidget import KanbanWidget
from typing import *


class AbstractView(QWidget):
    """
    Provides a basic infrastructure for searching for matching
    KanbanItems and focusing on them :)
    """
    matching: List[KanbanWidget]

    def __init__(self, parent=None):
        super(AbstractView, self).__init__(parent)
        self.matching = []
        self.search_index = -1
        self.last_filter = None

    def get_eligible_widgets(self) -> List[KanbanWidget]:
        """
        Retrieve tasks that are eligible for being focused upon.

        Primarily of interest in implementing anything that does not, as a rule
        show all the items in the board, such as the QueueView or Treeview

        :return: The list of eligible KanbanWidgets
        """
        return self.findChildren(KanbanWidget)

    def filterChanged(self, text: str) -> None:
        """
        Update the filter, change the matching items, focus on them, etc
        Handles things like incremental searching(that is, only checking the items that match)

        :param text: The query text
        """

        # In general, if the text is empty, then marking the widget as being the matching item isn't desirable
        if text == '':
            if self.currentSearchResult():
                self.currentSearchResult().set_selected(False)
            self.last_filter = ''
            return
        # Things to consider here if it ever proves too slow. There are a couple of improvements that can be
        # applied relatively easily:
        # 1. Make self.matching a set
        # 2. If self.last_filter is a prefix of text, then you can search the current results instead
        if text != self.last_filter:
            if self.matching:
                self.apply_unselected_styling(self.currentSearchResult())
            if self.last_filter and text.startswith(self.last_filter):
                r = []
                for i in self.matching:
                    if i.item.matches(text):
                        r.append(i)
                self.matching = r
            else:
                self.matching.clear()
                for i in self.get_eligible_widgets():
                    if i.item.matches(text):
                        self.matching.append(i)
            self.last_filter = text
            self.search_index = -1
        if self.matching:
            self.advance_search()

    def scroll_to_result(self, item: KanbanWidget) -> None:
        """
        Ensure the relevant widget is in the view

        :param item: The widget to search for
        """
        raise NotImplementedError()

    def currentSearchResult(self) -> Optional[KanbanWidget]:
        """
        Get the current search result
        :return: The search result at the current index, or None, if there isn't one
        """
        if not self.matching:
            return None
        return self.matching[self.search_index]

    @staticmethod
    def apply_selected_styling(widget: KanbanWidget) -> None:
        widget.set_selected(True)

    @staticmethod
    def apply_unselected_styling(widget: KanbanWidget) -> None:
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

    def rewind_search(self) -> None:
        """
        Focus on the previous search result
        """
        if not self.matching:
            return
        prev = self.matching[self.search_index]
        self.apply_unselected_styling(prev)
        self.search_index -= 1
        self.search_index %= len(self.matching)
        self.apply_selected_styling(self.currentSearchResult())
        self.scroll_to_result(self.currentSearchResult())
