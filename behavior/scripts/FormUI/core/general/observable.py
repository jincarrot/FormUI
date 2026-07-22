# -*- coding: utf-8 -*-
from ..utils.environment import *

class Observable:
    """
    可观测变量
    """
    
    def __init__(self, value, id):
        def temp(new):
            self.setValue(new)
        self.__id = id
        self.__v1 = value
        self._onUpdate = temp

    @property
    def _id(self):
        return self.__id
    
    def getValue(self):
        return self.__v1
    
    def setValue(self, v):
        self.__v1 = v
        if isServer():
            getServerSystem().observableManager.update(self._id, v)
        else:
            getClientSystem().observableManager.update(self._id, v)

    def onUpdate(self, callback):
        """
        当变量更新时触发。

        触发回调时，变量还未应用更新，可以通过.value属性获取更新前的旧值。
        """
        def temp(new):
            callback(new)
            self.setValue(new)
            
        self._onUpdate = temp
    
