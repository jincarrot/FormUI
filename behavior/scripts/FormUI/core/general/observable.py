# -*- coding: utf-8 -*-
from ..utils.environment import *

class Observable:
    """
    可观测变量
    """
    
    def __init__(self, value, id):
        def onUpdate(new):
            for callback in self.__callbacks:
                callback(new)
        def temp(new):
            self.__v1 = new
            if isServer():
                getServerSystem().observableManager.update(self._id, new)
            else:
                getClientSystem().observableManager.update(self._id, new)
        self.__callbacks = [temp]
        self.__id = id
        self.__v1 = value
        self._onUpdate = onUpdate

    @property
    def _id(self):
        return self.__id
    
    def getValue(self):
        return self.__v1
    
    def setValue(self, v):
        if self.__v1 != v:
            self.__v1 = v
            self._onUpdate(v)
            if isServer():
                getServerSystem().observableManager.update(self._id, v)
            else:
                getClientSystem().observableManager.update(self._id, v)

    def subscribe(self, callback):
        """
        当变量更新时触发。

        触发回调时，变量还未应用更新，可以通过.value属性获取更新前的旧值。
        """
        self.__callbacks.append(callback)

    def unsubscribe(self, callback):
        """
        取消触发函数。
        """
        if callback in self.__callbacks:
            self.__callbacks.remove(callback)

    def __lt__(self, value):
        new = Observable(self.getValue() < value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue < value)
        return new
    
    def __le__(self, value):
        new = Observable(self.getValue() <= value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue <= value)
        return new

    def __gt__(self, value):
        new = Observable(self.getValue() > value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue > value)
        return new

    def __ge__(self, value):
        new = Observable(self.getValue() >= value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue >= value)
        return new

    def __eq__(self, value):
        new = Observable(self.getValue() == value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue == value)
        return new

    def __ne__(self, value):
        new = Observable(self.getValue() != value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue != value)
        return new

    # ---------- 算术运算符 ----------
    def __add__(self, value):
        new = Observable(self.getValue() + value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue + value)
        return new

    def __sub__(self, value):
        new = Observable(self.getValue() - value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue - value)
        return new

    def __mul__(self, value):
        new = Observable(self.getValue() * value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue * value)
        return new

    def __truediv__(self, value):
        new = Observable(self.getValue() / value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue / value)
        return new

    def __floordiv__(self, value):
        new = Observable(self.getValue() // value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue // value)
        return new

    def __mod__(self, value):
        new = Observable(self.getValue() % value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue % value)
        return new

    def __pow__(self, value, mod=None):
        # Python 的 pow 可带第三个参数，这里简化为两个参数
        new = Observable(pow(self.getValue(), value) if mod is None else pow(self.getValue(), value, mod))
        @self.subscribe
        def onChange(newValue):
            new.setValue(pow(newValue, value) if mod is None else pow(newValue, value, mod))
        return new

    # ---------- 位运算符（按需） ----------
    def __and__(self, value):
        new = Observable(self.getValue() & value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue & value)
        return new

    def __or__(self, value):
        new = Observable(self.getValue() | value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue | value)
        return new

    def __xor__(self, value):
        new = Observable(self.getValue() ^ value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue ^ value)
        return new

    def __lshift__(self, value):
        new = Observable(self.getValue() << value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue << value)
        return new

    def __rshift__(self, value):
        new = Observable(self.getValue() >> value)
        @self.subscribe
        def onChange(newValue):
            new.setValue(newValue >> value)
        return new
    
