from PySide2.QtCore import QSettings
from typing import *

defaults = {
	"Display":{
        "DescriptionLength":200
    }
}

def check_slash_set(settings:QSettings, configuration_path:List[str], currentItem:Dict[str,Any]):
    for key,value in currentItem.items():
        if isinstance(value, dict):
            check_slash_set(settings, configuration_path+[key], value)
        else:
            path = "/".join(configuration_path+[key])
            settings.setValue(path,value)

def initialize_to_defaults():
    settings=QSettings()
    check_slash_set(settings,[],defaults)