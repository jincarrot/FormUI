# -*- coding: utf-8 -*-
from ..control import Control

class ControlManager:
    """
    Manager of forms.
    """

    def __init__(self):
        self.__controls = {} # type: dict[str, Control]

    def create(self, controlType, controlName, controlPath, options={}):
        v = Control(controlType, controlName, controlPath, options)
        self.__controls[controlName] = v
        return v

    def has(self, name):
        return name in self.__controls

    def get(self, name):
        return self.__controls[name] if self.has(name) else None

    def applyObservableUpdate(self, obId, value):
        from ...utils.type import updateWrappedObservable
        for control in self.__controls.values():
            if control.typeId == 'group':
                updateWrappedObservable(control.options['controls'], obId, value)

    def getRegisteredData(self):
        from copy import deepcopy
        return [{'type': control.typeId, 'name': control.name, 'path': control.path,
                 'options': deepcopy(control.options)} for control in self.__controls.values()]

