from PySide2.QtGui import QColor
from typing import Optional
class CategoryData:
    """
    A small container class for handling the associated styling of a
    task's category. This will enable improved extensibility down the line
    compared to a tuple of the same items.
    """
    #: The foreground(text) Color the widget should render with
    foreground:Optional[QColor]
    #: The background color the widget should render with
    background:Optional[QColor]
    __slots__=('foreground','background')
    
    def __init__(self, foreground:QColor=None, background:QColor=None):
        self.foreground = foreground
        self.background = background

    def __setstate__(self,state):
        for slot, value in state.items():
            setattr(self,slot,value)

    def __getstate__(self):
        state = dict((slot, getattr(self, slot))
                     for slot in self.__slots__
                     if hasattr(self, slot))
        return state