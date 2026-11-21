# -*- coding: utf-8 -*-
from ..utils.type import copyContainers

class Control(object):
    """控件类"""

    def __init__(self, controlType, controlName, controlPath, options={}):
        self.__typeId = controlType
        self.__name = controlName
        self.__path = controlPath
        self.__options = copyContainers(options)

    @property
    def typeId(self):
        return self.__typeId
    
    @property
    def name(self):
        return self.__name
    
    @property
    def path(self):
        return self.__path
    
    @property
    def options(self):
        return self.__options
