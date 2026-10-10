# -*- coding: utf-8 -*-
from collections import deque
import operator
from ..utils.environment import *

ObId = 0 if isServer() else -1

class Observable(object):
    """
    可观测变量。运算返回已注册的Observable，并随参与运算的变量更新。
    bool转换读取当前值；获取运算结果的原始值请使用getValue()。
    """
    
    def __init__(self, value):
        global ObId
        self.__callbacks = []
        self.__pendingValues = deque()
        self.__updating = False
        self.__id = ObId
        if isServer():
            ObId += 1
        else:
            ObId -= 1
        self.__v1 = value
        self.identifier = ""
        """变量标识符，可以用于区分变量。"""

    def getData(self):
        return self.__v1

    def setData(self, v):
        self.setValue(v)

    @property
    def _id(self):
        return self.__id
    
    def getValue(self):
        return self.__v1
    
    def setValue(self, v):
        self.__pendingValues.append(v)
        if self.__updating:
            return
        self.__updating = True
        try:
            while self.__pendingValues:
                new = self.__pendingValues.popleft()
                if self.__v1 != new:
                    try:
                        for callback in tuple(self.__callbacks):
                            callback(new)
                    finally:
                        self.__v1 = new
                        if isServer():
                            getServerSystem().observableManager.update(self._id, new)
                        else:
                            getClientSystem().observableManager.update(self._id, new)
        finally:
            self.__updating = False
            self.__pendingValues.clear()

    def _onUpdate(self, v):
        self.setValue(v)

    def subscribe(self, callback):
        """
        当变量更新时触发。

        触发回调时，变量还未应用更新，可以通过getValue获取更新前的旧值。
        回调内再次调用setValue时，会在本次更新完成后依次处理。
        """
        self.__callbacks.append(callback)

    def unsubscribe(self, callback):
        """
        取消触发函数。
        """
        if callback in self.__callbacks:
            self.__callbacks.remove(callback)

    def __bool__(self):
        return bool(self.getValue())

    __nonzero__ = __bool__

    def __derive(self, operation, *operands):
        operands = (self,) + operands
        values = []
        sources = {}
        for index, operand in enumerate(operands):
            if isinstance(operand, Observable):
                values.append(operand.getValue())
                key = id(operand)
                if key not in sources:
                    sources[key] = (operand, [])
                sources[key][1].append(index)
            else:
                values.append(operand)
        system = getServerSystem() if isServer() else getClientSystem()
        result = system.observableManager.create(operation(*values))

        def subscribeSource(source, indices):
            def onChange(newValue):
                # 回调期间源对象仍保留旧值，计算时使用回调传入的新值。
                for index in indices:
                    values[index] = newValue
                result.setValue(operation(*values))
            source.subscribe(onChange)

        for source, indices in sources.values():
            subscribeSource(source, indices)
        return result

    def __lt__(self, value):
        return self.__derive(operator.lt, value)

    def __le__(self, value):
        return self.__derive(operator.le, value)

    def __gt__(self, value):
        return self.__derive(operator.gt, value)

    def __ge__(self, value):
        return self.__derive(operator.ge, value)

    def __eq__(self, value):
        return self.__derive(operator.eq, value)

    def __ne__(self, value):
        return self.__derive(operator.ne, value)

    # ---------- 算术运算符 ----------
    def __add__(self, value):
        return self.__derive(operator.add, value)

    def __radd__(self, value):
        return self.__derive(lambda left, right: right + left, value)

    def __sub__(self, value):
        return self.__derive(operator.sub, value)

    def __rsub__(self, value):
        return self.__derive(lambda left, right: right - left, value)

    def __mul__(self, value):
        return self.__derive(operator.mul, value)

    def __rmul__(self, value):
        return self.__derive(lambda left, right: right * left, value)

    def __truediv__(self, value):
        return self.__derive(operator.truediv, value)

    def __rtruediv__(self, value):
        return self.__derive(lambda left, right: operator.truediv(right, left), value)

    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __floordiv__(self, value):
        return self.__derive(operator.floordiv, value)

    def __rfloordiv__(self, value):
        return self.__derive(lambda left, right: right // left, value)

    def __mod__(self, value):
        return self.__derive(operator.mod, value)

    def __rmod__(self, value):
        return self.__derive(lambda left, right: right % left, value)

    def __pow__(self, value, mod=None):
        if mod is None:
            return self.__derive(pow, value)
        return self.__derive(pow, value, mod)

    def __rpow__(self, value, mod=None):
        if mod is None:
            return self.__derive(lambda left, right: pow(right, left), value)
        return self.__derive(lambda left, right, modulus: pow(right, left, modulus), value, mod)

    # ---------- 位运算符 ----------
    def __and__(self, value):
        return self.__derive(operator.and_, value)

    def __rand__(self, value):
        return self.__derive(lambda left, right: right & left, value)

    def __or__(self, value):
        return self.__derive(operator.or_, value)

    def __ror__(self, value):
        return self.__derive(lambda left, right: right | left, value)

    def __xor__(self, value):
        return self.__derive(operator.xor, value)

    def __rxor__(self, value):
        return self.__derive(lambda left, right: right ^ left, value)

    def __lshift__(self, value):
        return self.__derive(operator.lshift, value)

    def __rlshift__(self, value):
        return self.__derive(lambda left, right: right << left, value)

    def __rshift__(self, value):
        return self.__derive(operator.rshift, value)

    def __rrshift__(self, value):
        return self.__derive(lambda left, right: right >> left, value)
