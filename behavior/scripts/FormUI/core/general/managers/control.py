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
    