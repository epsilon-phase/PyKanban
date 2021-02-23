from __future__ import annotations
from typing import *
from enum import Enum,auto
import pickle


class Priority(Enum):
    HIGH=auto()
    MEDIUM=auto()
    LOW=auto()

class ItemState(Enum):
    COMPLETED=auto()
    BLOCKED=auto()
    AVAILABLE=auto()

class KanbanItem:
    depends_on:List[KanbanItem]
    name:str
    priority:Priority
    description:str
    completed:bool
    board:KanbanBoard
    __slots__=('completed','board','priority','name','depends_on','description','assigned')

    def __init__(self, name, description,board:KanbanBoard=None,priority=Priority.MEDIUM):
        self.priority=priority
        self.name=name
        self.description=description
        self.depends_on = []
        self.completed=False
        self.assigned=None
        self.board=board

    def matches(self,text:str)->bool:
        text = text.lower()
        return text in self.name.lower() or text in self.description.lower()

    def short_name(self)->str:
        return self.name

    def blocked(self)->bool:
        """
        Returns true if all tasks this depends on are completed.
        """
        if self.completed:
            return False
        return not all(map(lambda x:x.completed,self.depends_on))

    def getBlockers(self)->List[KanbanItem]:
        """
        Returns the list of items responsible for this item being blocked
        """
        result = []
        for i in self.depends_on:
            if i.blocked():
                result+=i.getBlockers()
            if not i.completed:
                result+=[i]
        return result

    def hasCycle(self, seen:Set[KanbanItem]=None, path:List[KanbanItem]=None)->bool:
        """
        Returns true if there is a cycle in the dependencies of an item.
        """
        seen = set() if seen is none else seen
        path = [] if path is None else path
        if self in path:
            return True
        if self in seen:
            return False
        seen.add(self)
        path.append(self)
        for i in self.depends_on():
            if i.hasCycle(seen,path):
                path.pop()
                return True
        path.pop()
        return False

    def print(self,complete:bool=False,level:int=0)->None:
        depth = '\t'*level
        print(f"{depth}Name:{self.name}")
        print(f"{depth}Description:'{self.description}'")
        print(f"{depth}completed: {self.completed}")
        print(f"{depth}Depends on:")
        for i in self.depends_on:
            if not complete:
                print(f"\t{depth}{i.short_name()}")
            else:
                i.print(complete,level+1)

    def state(self)->ItemState:
        if self.blocked():
            return ItemState.BLOCKED
        if self.completed:
            return ItemState.COMPLETED
        return ItemState.AVAILABLE

class KanbanBoard:
    items: List[KanbanItem]
    filename: str

    def __init__(self):
        self.items=[]
        self.filename=None

    def find_matching(self,text:str)->List[KanbanItem]:
        """
        Return items that contain specified text in either the name or description
        :param text: The text to search for
        :returns: A list of items that match the text
        """
        matches = []
        for i in filter(lambda x:x.matches(text),self.items):
            matches.append(i)
        return matches

    def add_item(self,item:KanbanItem)->None:
        self.items.append(item)
        item.board=self

    def remove_item(self, item:KanbanItem)->None:
        """
        Remove an item in the kanbanboard, including all dependency lists.
        :param item: The kanban item being removed
        """
        if item not in self.items:
            return
        item_dx=self.items.index(item)
        del self.items[item_dx]
        for i in self.items:
            if item not in i.depends_on:
                continue
            item_dx = i.depends_on.index(item)
            del i.depends_on[item_dx]

    def save(self, filename:str)->None:
        if filename is not None:
            self.filename = filename
        else:
            filename = self.filename
        with open(filename,'wb') as f:
            pickle.dump(self,f)

    def load(filename:str)->KanbanBoard:
        with open(filename,'rb') as f:
            return pickle.load(f)

