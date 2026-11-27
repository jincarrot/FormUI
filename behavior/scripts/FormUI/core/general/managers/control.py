# -*- coding: utf-8 -*-
from ..control import Control
from ...utils.bindings import WrappedBindings

class ControlManager:
    """
    Manager of forms.
    """

    def __init__(self):
        self.__controls = {} # type: dict[str, Control]
        self.__groupBindings = {}
        self.__observableGroups = {}
        self.create('panel', 'fui:panel', 'fui.panel')

    def create(self, controlType, controlName, controlPath, options={}):
        v = Control(controlType, controlName, controlPath, options)
        old = self.__groupBindings.pop(controlName, None)
        if old is not None:
            for obId in old.byId:
                names = self.__observableGroups[obId]
                names.discard(controlName)
                if not names:
                    del self.__observableGroups[obId]
        if controlType == 'group':
            bindings = WrappedBindings(v.options['controls'])
            self.__groupBindings[controlName] = bindings
            for obId in bindings.byId:
                self.__observableGroups.setdefault(obId, set()).add(controlName)
        self.__controls[controlName] = v
        return v

    def has(self, name):
        return name in self.__controls

    def get(self, name):
        return self.__controls[name] if self.has(name) else None

    def applyObservableUpdate(self, obId, value):
        for name in self.__observableGroups.get(obId, ()):
            self.__groupBindings[name].update(obId, value)

    def getRegisteredData(self):
        from copy import deepcopy
        return [{'type': control.typeId, 'name': control.name, 'path': control.path,
                 'options': deepcopy(control.options)} for control in self.__controls.values()]

