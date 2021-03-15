from __future__ import annotations
from typing import *
from enum import IntEnum, Enum, auto

import pickle
import json
from PySide2.QtWidgets import QWidget

class Priority(IntEnum):
    """
    The priority of a task
    """
    HIGH=auto()
    MEDIUM=auto()
    LOW=auto()
    INVALID=auto()


class ItemState(Enum):
    """
    The status of a task
    """
    #: The task is completed
    COMPLETED=auto()
    #: The task is blocked
    BLOCKED=auto()
    #: The task is Available for completion
    AVAILABLE=auto()

class KanbanItem:
    """
    A task on a kanban board.
    """
    #: The list of tasks this task depends on to be completed
    depends_on:List[KanbanItem]
    #: The name of the task
    name:str
    #: The task's priority
    priority:Priority
    #: The description of a task
    description:str
    #: Whether or not the task is completed
    completed:bool
    #: The parent board
    board:KanbanBoard
    #:The parent widget, will be None until initialized
    widget: List[QWidget]
    position : Optional[Tuple[int,int]]
    #: The set of categories this task is under
    category: Set[str]
    __slots__=('completed','board','priority','name','depends_on','description','assigned','widget', 'category')
    def __init__(self, name, description,board:KanbanBoard=None,priority=Priority.MEDIUM):
        self.priority=priority
        self.name=name
        self.description=description
        self.depends_on = []
        self.priority=priority
        self.completed = False
        self.assigned = None
        self.board = board
        self.category = set()
        self.widget = []

    def category_matches(self,text:str)->bool:
        """
        Determine if a category is matched by the string

        :param text: The text to search for.
        :returns: If any category in this task partially matches the string
        """
        for i in self.category:
            if text in i:
                return True
        return False

    def matches(self,text:str)->bool:
        """
        Determine if this item matches a search string

        :param text: The text to search for
        """
        text = text.lower()
        return text in self.name.lower() or text in self.description.lower() \
               or self.category_matches(text)

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

    def hasCycle(self, path:Set[KanbanItem]=None)->bool:
        """
        Returns true if there is a cycle in the dependencies of an item.
        """
        path = path if path is not None else set()
        if self in path:
            return True
        path.add(self)
        for i in self.depends_on:
            if i.hasCycle(path):
                return True
        path.remove(self)
        return False

    def print(self, complete:bool=False, level:int=0)->None:
        depth = '\t'*level
        print(f"{depth}----")
        print(f"{depth}Name:{self.name}")
        print(f"{depth}Description:'{self.description}'")
        print(f"{depth}completed: {self.completed}")
        print(f"{depth}Depends on:")
        for i in self.depends_on:
            if not complete:
                print(f"\t{depth}{i.short_name()}")
            else:
                i.print(complete, level + 1)

    def state(self) -> ItemState:
        """
        Return the completion state of the item

        :returns: If the item is Blocked, Completed, or Available to be done
        """
        if self.blocked():
            return ItemState.BLOCKED
        if self.completed:
            return ItemState.COMPLETED
        return ItemState.AVAILABLE

    def add_category(self, category:str)->None:
        """
        Add a category to the item, since this requires ensuring that
        it also exists in the board, it is best handled as a setter type
        of function

        :param category: The name of the category
        """
        self.category.add(category)
        if self.board is not None:
            self.board.categories.add(category)
            print(f"Adding category to board {category}")
        else:
            print(f"Not adding category to board {category}")

    def remove_category(self, category:str)->None:
        if category in self.category:
            self.category.remove(category)

    def update_category(self, category:str,state:bool)->None:
        """
        Convenience to add or remove a category based on a bool.

        :param category: The name of the category
        :param state: Should it add (if true) or remove (if false)
        """
        if state:
            self.add_category(category)
        else:
            self.remove_category(category)

    def __getstate__(self):
        state = dict((slot,getattr(self,slot))
            for slot in self.__slots__
            if hasattr(self,slot))
        del state['widget']
        if 'position' in state.keys():
            del state['position']
        return state

    def __setstate__(self, state):
        for slot,value in state.items():
            setattr(self,slot,value)
        self.widget = []
        self._fill_in_missing()

    def _fill_in_missing(self):
        """
        Since categories were added later on, and presumably additional 
        things may be added to the structure here, it may be useful to keep
        this around for good luck
        """
        if not hasattr(self,'category'):
            setattr(self,'category',set())
            print(f"Setting category to {self.category}")
        if self.category is None:
            self.category = set()
            print("Filled in missing category set")
        if isinstance(self.category,list):
            self.category=set(self.category)

    def widget_of(self,widget:QWidget)->QWidget:
        for i in self.widget:
            if i.parent().parent() == widget or i.parent()== widget:
                return i

    def markChanged(self):
        for i in self.widget:
            i.updateDisplay()
            i.changed.emit(i,Priority.INVALID,self.state())


class KanbanBoard:
    """
    A container that keeps track of a set of KanbanItems and their categories
    """
    #: The list of tasks in the board
    items: List[KanbanItem]
    #: The place where, by default, this will be saved to
    filename: str
    #: A set of categories that exist in the items of the board
    categories: Set[str]
    #: Association between the category and the optional styling data that
    #: may be associated to it.
    category_data: Dict[str, CategoryData]

    def __init__(self):
        self.items=[]
        self.filename=None
        self.categories=set()
        self.category_data=dict()

    def for_each_by_matching(self,func:Callable[[KanbanItem,bool],None],query:str)->None:
        """
        Call a function on each item, also passing in a bool indicating its matchiness

        :param func: The function to call
        :param query: The query to match against
        """
        for i in self.items:
            func(i,i.matches(query))

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

    def dependents_of(self, item:KanbanItem) -> List[KanbanItem]:
        """
        Returns the items that depend on the given item directly
        
        :param item: The item that is depended on.
        :returns: A list of items that depend on item
        """
        return list(filter(lambda x: item in x.depends_on, self.items))

    def add_item(self, item:KanbanItem) -> None:
        """
        Add an item to the kanbanboard, setting its parent slot to the board
        
        :param item: The item to add
        """
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
        if item.widget is not None:
            for i in item.widget:
                i.parent().layout().removeWidget(i)
                i.deleteLater()
        for i in self.items:
            if item not in i.depends_on:
                continue
            item_dx = i.depends_on.index(item)
            del i.depends_on[item_dx]

    def trim_unused_categories(self)->Set[str]:
        """
        Remove categories that don't appear in any items.
        
        :returns: A list of removed categories.
        """
        seen: Set[str] = set()
        for item in self.items:
            seen = seen.union(item.category)
        not_used = self.categories.difference(seen)
        for i in not_used:
            if i in self.category_data.keys():
                del self.category_data[i]
            self.categories.remove(i)
        return not_used

    def save(self, filename: str, update_stored: bool = True) -> None:
        """
        Save the kanban board to a file
        
        :param filename: The file that will be dumped to
        """
        if filename is not None:
            self.filename = filename
        else:
            if update_stored:
                filename = self.filename
        if filename.endswith('.json') or filename.endswith('.json.bak'):
            self.export(filename)
            return
        with open(filename, 'wb') as f:
            thing = pickle.dumps(self)
            f.write(thing)

    def export(self, filename:str) -> None:
        if KanbanBoard.Encoder is None:
            from src.serializers import KanbanBoardEncoder
            KanbanBoard.Encoder = KanbanBoardEncoder
        js = json.dumps(self,cls=KanbanBoard.Encoder)
        with open(filename, 'w') as f:
            f.write(js)

    def _fix_missing(self)->None:
        """
        This ended up being necessary to get categories working 
        in older save files. This may continue to be necessary, or it may 
        not.

        In either case, it provides some way of enabling new features on
        old saves, so that's quite nice.
        """
        from src.taskcategory import CategoryData
        from PySide2.QtGui import QColor
        if not hasattr(self,'categories'):
            self.categories=set()
            self.category_data=dict()
        for name,val in self.category_data.items():
            if isinstance(val,QColor):
                self.category_data[name]=CategoryData(val,None)
        seen = set()
        for i in self.items:
            if id(i) in seen:
                print("Found duplicate")
                del i

            seen.add(id(i))

        stack = list(self.items)
        while len(stack)>0:
            item = stack.pop()
            if item not in self.items:
                print("Found disconnected item")
            for i in item.depends_on:
                stack.append(i)

    Encoder = None
    Decoder = None

    @staticmethod
    def load(filename:str)->KanbanBoard:
        """
        Load a kanbanboard from a file
        
        :param filename: The filename to load the kanban board from
        """
        if filename.endswith(".json") or filename.endswith('.json.bak'):
            return KanbanBoard.loadJson(filename)
        else:
            with open(filename,'rb') as f:
                c = pickle.load(f)
                c._fix_missing()
                return c

    @staticmethod
    def loadJson(filename:str):
        if KanbanBoard.Decoder is None:
            from src.serializers import as_kanban_board
            KanbanBoard.Decoder = as_kanban_board
        with open(filename,'r') as f:
            return json.load(f,object_hook=KanbanBoard.Decoder)

    def toGraphViz(self)->str:
        """
        Create a directed graph based on the current item tree.

        :returns: The a string with the dot language 
        corresponding to the kanbanboard
        """
        lines = ["digraph G{"]
        ids = {v:idx for idx,v in enumerate(self.items)}
        for i in self.items:
            desc = i.description.replace("\n","<br/>")
            color=""
            if i.completed:
                color='green'
            elif i.state() == ItemState.BLOCKED:
                color='red'

            if color != '':
                color=f"bgcolor=\"{color}\""
            table = f"<TABLE {color}><tr><td>{i.name}</td></tr>"
            if i.description != "":
                table+=f"<tr><td>{desc}</td></tr>"
            table+="</TABLE>"
            declaration = f"""
            \t{ids[i]}[shape=none,label=<{table}>]
            """
            lines.append(declaration)
        for i in self.items:
            edges = f"{ids[i]} -> {{{','.join([str(ids[j]) for j in i.depends_on])}}};"
            lines.append(edges)
        lines+=["}"]
        return "\n".join(lines)
