# -*- coding: utf-8 -*-
from ..utils.environment import *
from ..config import Namespace, SystemNameClient

class FormShowResult:
    """
    表单显示结果
    """
    def __init__(self, formId):
        self.__formId = formId
        self.__callback = None
        getSystem().ListenForEvent(Namespace, SystemNameClient, "formClose%s" % formId, self, self._onClose)

    def _onClose(self, data):
        getSystem().UnListenForEvent(Namespace, SystemNameClient, "formClose%s" % self.__formId, self, self._onClose)
        getSystem().formManager.get(self.__formId)._isShowing = False
        if self.__callback:
            self.__callback(data)

    def onClose(self, callback):
        """
        当表单关闭时触发。

        callback: 回调函数，参数为表单对象
        """
        self.__callback = callback
        

class Form:
    """
    自定义表单类（客户端服务端通用）
    """
    
    def __init__(self, id, title="", style={}):
        # type: (int, str, dict) -> None
        self.__id = id
        self.__title = title
        self.__controls = []
        defaultStyle = getSystem().screen.getDefaultStyle("scrolling_panel", {
            "class": "oreui:light_panel_thin",
            "offsetX": 0,
            "offsetY": 0,
            "width": "72%y",
            "height": "90%",
            "columns": [1],
            "closeAll": False
        })
        defaultStyle.update(style)
        self.__style = defaultStyle
        self._isShowing = False
        self.identifier = ""
        self._btnCallbacks = {
            0: lambda: None
        }

    @property
    def isShowing(self):
        return self._isShowing
    
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
        defaultStyle = getSystem().screen.getDefaultStyle("button", {
            "class": "oreui:normal_btn_thin",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
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
        defaultStyle = getSystem().screen.getDefaultStyle("toggle", {
            "class": "oreui:toggle_thin",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "state": state,
            "style": defaultStyle
        })
        return self

    def divider(self, style={}):
        # type: (str, dict) -> Form
        """
        添加一个分割线。
        """
        defaultStyle = getSystem().screen.getDefaultStyle("divider", {
            "class": "oreui:divider_in",
            "width": "100%-8px",
            "height": 2,
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "style": defaultStyle
        })
        return self

    def label(self, text, style={}):
        # type: (str, dict, dict) -> Form
        """
        添加一个按钮。
        """
        defaultStyle = getSystem().screen.getDefaultStyle("label", {
            "class": "oreui:label",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True,
            "fontSize": "default"
        })
        defaultStyle.update(style)
        self.__controls.append({
            "label": text,
            "style": defaultStyle
        })
        return self

    def slider(self, label, value, minValue=0.0, maxValue=1.0, step=1, style={}):
        """添加一个滑动条。"""
        defaultStyle = getSystem().screen.getDefaultStyle("slider", {
            "class": "oreui:slider",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "value": value,
            "minValue": minValue,
            "maxValue": maxValue,
            "step": step,
            "style": defaultStyle
        })
        return self

    def textfield(self, label, value, style={}):
        defaultStyle = getSystem().screen.getDefaultStyle("textfield", {
            "class": "oreui:textfield",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "value": value,
            "style": defaultStyle
        })
        return self

    def dropdown(self, label, items, value, style={}):
        defaultStyle = getSystem().screen.getDefaultStyle("dropdown", {
            "class": "oreui:dropdown",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "items": items,
            "value": value,
            "style": defaultStyle
        })
        return self
    
    def custom(self, params={}, style={}):
        defaultStyle = getSystem().screen.getDefaultStyle("custom", {
            "class": "oreui:divider",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self.__controls.append({
            "params": params,
            "style": style
        })
        return self

    def show(self, target=None, options={}):
        """
        显示表单。
        """
        if not target and not isServer():
            import mod.client.extraClientApi as c
            target = c.GetLocalPlayerId()
        defaultOptions = {
            "hideOtherForms": False,
            "layer": 0,
            "visible": True,
            "closeAll": False
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
        self._isShowing = True
        return FormShowResult(self.__id)

    def close(self, target=None):
        data = {
            "formId": self.__id
        }
        if not target:
            if isServer():
                import mod.server.extraServerApi as s
                target = s.GetPlayerList()
            else:
                import mod.client.extraClientApi as c
                target = c.GetLocalPlayerId()
        if isServer():
            if isinstance(target, str):
                getSystem().NotifyToClient(target, "closeForm", data)
            else:
                getSystem().NotifyToMultiClients(target, "closeForm", data)
        else:
            getSystem().closeForm(data)