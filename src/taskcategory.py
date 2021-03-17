from PySide2.QtCore import QBuffer, QByteArray, QIODevice
from PySide2.QtGui import QColor, QPixmap
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
    icon:Optional[QPixmap]
    __slots__=('foreground','background','icon')
    
    def __init__(self, foreground:QColor=None, background:QColor=None, icon:QPixmap=None):
        self.foreground = foreground
        self.background = background
        self.icon=icon

    def __setstate__(self,state):
        for slot, value in state.items():
            setattr(self, slot, value)
        if 'icon' in state and state['icon']:
            print(state)
            ba = QByteArray.fromBase64(QByteArray(state['icon'].encode()))
            buffer = QBuffer(ba)
            buffer.open(QIODevice.ReadOnly)
            pix = QPixmap()
            pix.loadFromData(ba, 'PNG')
            self.icon = pix

    def __getstate__(self):
        state = dict((slot, getattr(self, slot))
                     for slot in self.__slots__
                     if hasattr(self, slot))
        if self.icon:
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            self.icon.save(buffer, "PNG")
            state['icon'] = bytes(ba.toBase64()).decode()

        return state
