from PySide2.QtCore import QSettings
from typing import *

_defaults_ = {
	"Display":{
        "DescriptionLines":3
    },
    "Usability":{
        "OpenLastDocument":True
    },
    "UseRecord":{
        "LastDocument":None
    },
    "Recovery":{
        "AutoSave":True,
        "Interval":120
    }
}

def check_slash_set(settings:QSettings, configuration_path:List[str], currentItem:Dict[str,Any]):
    """
    Initializes QSettings based on the contents of currentItem
    
    :param settings: The QSettings instance
    :param configuration_path: The path of the setting information
    :param currentItem: The current section of the default dictionary to initialize
    """
    for key,value in currentItem.items():
        if isinstance(value, dict):
            check_slash_set(settings, configuration_path+[key], value)
        else:
            path = "/".join(configuration_path+[key])
            if not settings.contains(path):
                settings.setValue(path,value)

def initialize_to_defaults():
    settings=QSettings()
    check_slash_set(settings,[],_defaults_)