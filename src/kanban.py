from __future__ import annotations
from typing import *
from enum import IntEnum,Enum,auto
import pickle


class Priority(IntEnum):
    """
    The priority of a task
    """
    HIGH=auto()
    MEDIUM=auto()
    LOW=auto()


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
    __slots__=('completed','board','priority','name','depends_on','description','assigned','widget', 'category','position')
    __weakref__=('widget')

    def __init__(self, name, description,board:KanbanBoard=None,priority=Priority.MEDIUM):
        self.priority=priority
        self.name=name
        self.description=description
        self.depends_on = []
        self.priority=priority
        self.completed = False
        self.assigned = None
        self.board = board
        self.widget = None
        self.position = (0,0)
        self.category = set()

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

    def print(self,complete:bool=False,level:int=0)->None:
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
                i.print(complete,level+1)

    def state(self)->ItemState:
        """
        Return the completion state of the item

        :returns: If the item is Blocked, Completed, or Available to be done
        """
        if self.blocked():
            return ItemState.BLOCKED
        if self.completed:
            return ItemState.COMPLETED
        return ItemState.AVAILABLE

    def add_category(self,category:str)->None:
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

    def remove_category(self,category:str)->None:
        if category in self.category:
            self.category.remove(category)

    def update_category(self,category:str,state:bool)->None:
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
        self.widget=None
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
        self.position = (0,0)


    # def reposition(self, depth:int=0, x = 0)->int:
    #     """
    #     Reposition the current item and its children so that it may 
    #     be drawn as a tree.

    #     :param depth: The depth of the current item
    #     :param x: The lateral position of the current item
    #     """
    #     ox = x
    #     for i in self.depends_on:
    #         diff = i.reposition(depth+1, x)
    #         print(f"diff={diff}")
    #         x+=diff
    #     else:
    #         self.position=(x,depth)
    #         return 1
    #     if len(self.depends_on) > 1:
    #         avg = sum(map(lambda x:x.position[0],self.depends_on))
    #         avg /= len(self.depends_on)
    #         self.position=(avg,depth)
    #         diff = self.depends_on[-1].position[0] - self.depends_on[0].position[0]
    #         if diff == 0:
    #             print("0 Position increment D:")
    #         print(f"{diff} position increment")
    #         return x-ox
    #     else:
    #         self.position=(self.depends_on[0].position[0],depth)
    #         return 1

    def reposition(self,x:int=0,depth:int=0):
        if self.position is not None:
            print(f"double visited: {self.name}")
            return x+1
        if self.depends_on == []:
            self.position=(x,depth)
            return x+1


        if len(self.depends_on)==1:
            if self.depends_on[0].position is None:
                x=self.depends_on[0].reposition(x,depth+1)
                self.position=(self.depends_on[0].position[0],depth)
            else:
                self.position=(x,depth)
            return x+1
        else:
            avgpos = 0 
            avgcount = 0
            for i in self.depends_on:
                if i.position is not None:
                    continue
                x=i.reposition(x,depth+1)
                avgpos += i.position[0]
                avgcount+=1
            avgpos //= avgcount
            self.position = (avgpos,depth)
            return self.depends_on[-1].position[0]+2



        

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

    def dependents_of(self,item:KanbanItem)->List[KanbanItem]:
        """
        Returns the items that depend on the given item directly
        
        :param item: The item that is depended on.
        :returns: A list of items that depend on item
        """
        return list(filter(lambda x:item in x.depends_on,self.items))

    def add_item(self,item:KanbanItem)->None:
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

    def resetPositions(self):
        for i in self.items:
            i.position = None

    def trim_unused_categories(self)->Set[str]:
        """
        Remove categories that don't appear in any items.
        
        :returns: A list of removed categories.
        """
        seen:Set[str] = set()
        for item in self.items:
            seen = seen.union(item.category)
        not_used = self.categories.difference(seen)
        for i in not_used:
            if i in self.category_data.keys():
                del self.category_data[i]
            self.categories.remove(i)
        return not_used

    def save(self, filename:str)->None:
        """
        Save the kanban board to a file
        
        :param filename: The file that will be dumped to
        """
        if filename is not None:
            self.filename = filename
        else:
            filename = self.filename
        with open(filename,'wb') as f:
            pickle.dump(self,f)

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


    @staticmethod
    def load(filename:str)->KanbanBoard:
        """
        Load a kanbanboard from a file
        
        :param filename: The filename to load the kanban board from
        """
        with open(filename,'rb') as f:
            c=pickle.load(f)
            c._fix_missing()
            return c
