# -*- coding: utf-8 -*-
from ..utils.environment import *

class Form:
    """
    自定义表单类（客户端服务端通用）
    """
    
    def __init__(self, id, title="", style={}):
        # type: (int, str, dict) -> None
        self.__id = id
        self.__title = title
        self.__controls = []
        defaultStyle = {
            "class": "oreui:light_panel_thin",
            "offsetX": 0,
            "offsetY": 0,
            "width": "40%",
            "height": "70%",
            "columns": [1]
        }
        defaultStyle.update(style)
        self.__style = defaultStyle
        self._btnCallbacks = {
            0: lambda: None
        }

    def button(self, label, callbacks={}, style={}):
        # type: (str, dict, dict) -> Form
        """
        添加一个按钮。
        """
        for key in callbacks:
            self._btnCallbacks[len(self._btnCallbacks)] = callbacks[key]
            callbacks[key] = len(self._btnCallbacks) - 1
        defaultCallbacks = {
            "onClick": 0,
            "onMoveIn": 0,
            "onMoveOut": 0
        }
        defaultStyle = {
            "class": "oreui:normal_btn_thin",
            "width": "100%-4px",
            "height": 30,
            "offsetX": 0,
            "offsetY": 0
        }
        defaultCallbacks.update(callbacks)
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "callbacks": defaultCallbacks,
            "style": defaultStyle
        })
        return self
    
    def toggle(self, label, state, style={}):
        """
        添加一个开关。
        """
        return self

    def show(self, target, options={}):
        """
        显示表单。
        """
        defaultOptions = {
            "hideOtherForms": False
        }
        defaultOptions.update(options)
        # Wrap data.
        from ..utils.type import wrapDict
        observables = []
        data = wrapDict({
            "formId": self.__id,
            "title": self.__title,
            "controls": self.__controls,
            "style": self.__style,
            "options": defaultOptions,
            "fromServer": isServer()
        }, observables)
        data['observables'] = observables
        # Send data.
        if isServer():
            if isinstance(target, str):
                getSystem().NotifyToClient(target, "showForm", data)
            else:
                getSystem().NotifyToMultiClients(target, "showForm", data)
        else:
            getSystem().showForm(data)
