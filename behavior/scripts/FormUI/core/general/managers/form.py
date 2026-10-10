# -*- coding: utf-8 -*-
from ...utils.environment import isServer

from ..form import Form

class FormManager:
    """
    Manager of forms.
    """

    def __init__(self):
        self.__forms = {}
        self.__currentId = 0 if isServer() else -1

    def create(self, title="", style={}):
        v = Form(self.__currentId, title, style)
        self.__forms[self.__currentId] = v
        self.__currentId += 1 if isServer() else -1
        return v
    
    def get(self, formId):
        return self.__forms[formId] if formId in self.__forms else None
    