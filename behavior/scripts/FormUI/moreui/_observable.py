# -*- coding: utf-8 -*-
from ..lib import Observable as FormObservable
from ..core.general.observable import Observable as NativeObservable
from ..core.utils.ui import STRING_TYPES

try:
    _INTEGERS = (int, long)
except NameError:
    _INTEGERS = (int,)

_NOT_NOTIFYING = object()


def optionsDict(options):
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise TypeError('options must be a dict')
    return dict(options)


def binding(value):
    return value._binding if isinstance(value, Observable) else value


def current(value):
    if isinstance(value, Observable):
        return value.getData()
    if isinstance(value, NativeObservable):
        return value.getValue()
    return value


class Observable(object):
    """【已废弃】MoreUI 数据绑定。新代码使用 FormUI.lib.Observable。"""

    def __init__(self, data, options=None):
        if type(data) not in (bool, float) + _INTEGERS and not isinstance(data, STRING_TYPES):
            raise TypeError('MoreUI Observable expects a number, boolean or string')
        self._options = optionsDict(options)
        self._options.setdefault('clientWritable', False)
        if not isinstance(current(self._options['clientWritable']), bool):
            raise TypeError('clientWritable must be a bool')
        self._type = type(data)
        self._binding = FormObservable.create(data)
        self._binding._onUpdate = self._onClientUpdate
        self._callbacks = []
        self._notifying = _NOT_NOTIFYING

    @staticmethod
    def create(data, options=None):
        return Observable(data, options)

    @property
    def typeId(self):
        return self._type

    def getData(self):
        return self._binding.getValue() if self._notifying is _NOT_NOTIFYING else self._notifying

    def setData(self, data, bit=False):
        if data == self.getData():
            return
        if isinstance(self.getData(), STRING_TYPES):
            if self._type is str and isinstance(data, STRING_TYPES) and not isinstance(data, str):
                data = data.encode('utf-8')
            else:
                data = self._type(data)
        elif self._type is bool:
            data = bool(data)
        elif self._type in _INTEGERS + (float,) and type(data) in _INTEGERS + (float,):
            data = self._type(data)
        if type(data) is not self._type:
            raise TypeError('Observable expects %s, got %s' % (self._type.__name__, type(data).__name__))
        self._binding.setValue(data)

    def _onClientUpdate(self, data):
        if current(self._options['clientWritable']):
            self.setData(data)

    def _notify(self, data):
        self._notifying = data
        try:
            for callback in tuple(self._callbacks):
                callback(data)
        finally:
            self._notifying = _NOT_NOTIFYING

    def subscribe(self, callback):
        if not callable(callback):
            raise TypeError('callback must be callable')
        if callback not in self._callbacks:
            if not self._callbacks:
                self._binding.subscribe(self._notify)
            self._callbacks.append(callback)

    def unsubscribe(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            if not self._callbacks:
                self._binding.unsubscribe(self._notify)
