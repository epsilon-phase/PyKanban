from __future__ import annotations
from typing import *
from enum import Enum,auto

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
        return not all(map(lambda x:x.completed,self.depends_on))

    def print(self,complete=False,level=0):
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
    def __init__(self):
        self.items=[]

    def find_matching(self,text:str)->List[KanbanItem]:
        matches = []
        for i in filter(lambda x:x.matches(text),self.items):
            matches.append(i)
        return matches

    def add_item(self,item:KanbanItem)->None:
        self.items.append(item)
        item.board=self

    def remove_item(self, item:KanbanItem)->None:
        "Remove an item in the kanbanboard, including all dependencies."
        if item not in self.items:
            return
        item_dx=self.items.index(item)
        del self.items[item_dx]
        for i in self.items:
            if item not in i.depends_on:
                continue
            item_dx = i.depends_on.index(item)
            del i.depends_on[item_dx]



