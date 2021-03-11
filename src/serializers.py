from src.kanban import KanbanBoard,KanbanItem
from src.taskcategory import CategoryData
from typing import *
from json import JSONEncoder
from PySide2.QtGui import QColor

def ColorToTuple(color:QColor)->Tuple[int,int,int,int]:
    return (color.red(),color.green(),color.blue(),color.alpha())

def ColorFromTuple(tuple)->QColor:
    return QColor(tuple[0],tuple[1],tuple[2],tuple[3])

def as_kanban_item(dct:dict):
    if '__kanbanitem__' in dct:
        result = KanbanItem(dct['name'],dct['description'],dct['priority'])
        result.category = set(dct['category'])
        result.depends_on = dct['depends_on']
        result.completed = dct['completed']
        return result
    else:
        return dct

def as_category_data(dct:dict)->CategoryData:
    result = CategoryData()
    if 'foreground' in dct:
        result.foreground=ColorFromTuple(dct['foreground'])
    if 'background' in dct:
        result.background=ColorFromTuple(dct['background'])
    return result

def as_kanban_board(dct:dict):
    if '__kanbanboard__' in dct:
        board = KanbanBoard()
        board.items = list(map(as_kanban_item,dct['items']))
        for i in board.items:
            i.board=board
        for name,cd in dct['category_data'].items():
            board.category_data[name]=as_category_data(cd)
        for i in board.items:
            for idx,val in enumerate(i.depends_on):
                i.depends_on[idx]=board.items[val]
        board.categories = set(dct['categories'])
        board.filename = dct['filename']

        return board
    else:
        return dct


class KanbanBoardEncoder(JSONEncoder):
    def encodeItem(self,item:KanbanItem,ids:Dict[KanbanItem,int])->Dict[str,Any]:
        result:Dict[str,Any] = {}
        result['id']=ids[item]
        result['category']=list(item.category)
        result['name']=item.name
        result['description']=item.description
        result['priority']=item.priority
        result['__kanbanitem__']=True
        result['depends_on']=list(map(lambda x:ids[x],item.depends_on))
        result['completed']=item.completed
        return result

    def encodeKanban(self, kanban:KanbanBoard) -> Dict:
        ids = {}
        # Assign IDs for each item
        for i,v in enumerate(kanban.items):
            ids[v]=i
        result:Dict[str,Any] = {}
        result['__kanbanboard__']=True
        result['items'] = list(map(lambda x:self.encodeItem(x,ids),kanban.items))
        category_data={}
        for (name,item) in kanban.category_data.items():
            data = {}
            if item.foreground is not None:
                data['foreground']=ColorToTuple(item.foreground)
            if item.background is not None:
                data['background'] = ColorToTuple(item.background)
            category_data[name]=data
        result['category_data']=category_data
        result['categories'] = list(kanban.categories)
        result['filename']=kanban.filename
        return result


    def default(self,obj):
        if isinstance(obj,KanbanBoard):
            return self.encodeKanban(obj)
        return JSONEncoder.default(self, obj)
