# -*- coding: utf-8 -*-
from ..utils.environment import *
from ..utils.type import FormShowResultArgs
from ..utils.ui import validateGrids, validateDropdownItems, getFontScale
from ..config import Namespace, SystemNameClient

class FormShowResult:
    """
    表单显示结果
    """
    def __init__(self, formId, targets):
        self.__formId = formId
        self.__callback = None
        self.__pendingPlayers = set(targets)
        self.__system = getSystem()
        self.__listeners = []
        if self.__pendingPlayers:
            try:
                self.__listen(Namespace, SystemNameClient, "formClose%s" % formId, self._onClose)
                if isServer():
                    import mod.server.extraServerApi as s
                    self.__listen(s.GetEngineNamespace(), s.GetEngineSystemName(),
                                  "PlayerLeftMessageServerEvent", self._onPlayerLeft)
            except:
                self._cancel()
                raise

    def __listen(self, namespace, systemName, event, callback):
        listener = (namespace, systemName, event, self, callback)
        self.__system.ListenForEvent(*listener)
        self.__listeners.append(listener)

    def _cancel(self):
        for listener in self.__listeners:
            self.__system.UnListenForEvent(*listener)
        self.__listeners = []
        self.__pendingPlayers.clear()

    def __finishPlayer(self, playerId):
        if playerId not in self.__pendingPlayers:
            return False
        self.__pendingPlayers.remove(playerId)
        form = self.__system.formManager.get(self.__formId)
        if form:
            form._isShowing[playerId] = False
        if not self.__pendingPlayers:
            self._cancel()
        return True

    def _onClose(self, data):
        if self.__finishPlayer(data['playerId']) and self.__callback:
            self.__callback(FormShowResultArgs(data))

    def _onPlayerLeft(self, data):
        self.__finishPlayer(data['id'])

    def onClose(self, callback):
        """
        当表单关闭时触发。

        每个本次显示的目标玩家关闭时触发一次，参数为FormShowResultArgs。
        玩家离线时只清理状态和监听，不触发关闭回调。
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
            "class": "",
            "offsetX": 0,
            "offsetY": 0,
            "width": "72%y",
            "height": "90%",
            "grids": [1],
            "hideOtherForms": False,
            "layer": 0,
            "visible": True
        })
        defaultStyle.update(style)
        defaultStyle['grids'] = validateGrids(defaultStyle['grids'])
        self.__style = defaultStyle
        self._isShowing = {}
        self.identifier = ""
        self._btnCallbacks = {
            0: lambda x: None
        }

    def isShowing(self, playerId=None):
        """查询指定玩家；服务端省略参数时检查历史显示过的所有玩家。"""
        if isServer():
            import mod.server.extraServerApi as s
            onlinePlayers = set(s.GetPlayerList())
            if playerId is not None:
                return playerId in onlinePlayers and self._isShowing.get(playerId, False)
            return bool(self._isShowing) and all(
                pId in onlinePlayers and showing for pId, showing in self._isShowing.items()
            )
        else:
            import mod.client.extraClientApi as c
            if playerId is None:
                playerId = c.GetLocalPlayerId()
            return self._isShowing.get(playerId, False)
    
    def button(self, label, callbacks={}, style={}):
        # type: (str, dict, dict) -> Form
        """
        添加一个按钮。
        """
        temp = {}
        for key in callbacks:
            self._btnCallbacks[len(self._btnCallbacks)] = callbacks[key]
            temp[key] = len(self._btnCallbacks) - 1
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
        defaultCallbacks.update(temp)
        defaultStyle.update(style)
        self._appendControl({
            "label": label,
            "callbacks": defaultCallbacks,
            "style": defaultStyle
        })
        return self

    def _appendControl(self, control):
        index = len(self.__controls)
        self.__controls.append(control)
        targets = [player for player, showing in self._isShowing.items() if showing]
        if not targets:
            return
        from ..utils.type import wrapDict
        data = {'formId': self.__id, 'index': index, 'control': wrapDict(control, [])}
        if isServer():
            import mod.server.extraServerApi as s
            online = set(s.GetPlayerList())
            targets = [player for player in targets if player in online]
            if targets:
                getSystem().NotifyToMultiClients(targets, 'appendFormControl', data)
        else:
            getSystem().appendFormControl(data)
    
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
        self._appendControl({
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
        self._appendControl({
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
        fontSize = defaultStyle['fontSize']
        getFontScale(fontSize.getValue() if fontSize.__class__.__name__ == 'Observable' else fontSize)
        self._appendControl({
            "label": text,
            "style": defaultStyle
        })
        return self

    def slider(self, label, value, minValue=0.0, maxValue=1.0, step=1, style={}):
        """添加滑动条；step=0 为连续模式，负步长取绝对值，反向边界自动排序。"""
        defaultStyle = getSystem().screen.getDefaultStyle("slider", {
            "class": "oreui:slider",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self._appendControl({
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
        self._appendControl({
            "label": label,
            "value": value,
            "style": defaultStyle
        })
        return self

    def dropdown(self, label, items, value, style={}):
        items = validateDropdownItems(items)
        defaultStyle = getSystem().screen.getDefaultStyle("dropdown", {
            "class": "oreui:dropdown",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self._appendControl({
            "label": label,
            "items": items,
            "value": value,
            "style": defaultStyle
        })
        return self
    
    def group(self, children={}, style={}):
        """Add a registered Group; children supplies named child values and callbacks."""
        if not isinstance(children, dict):
            raise TypeError('group children must be a dict')
        def encode(entries):
            result = {}
            for name, properties in entries.items():
                if not isinstance(properties, dict):
                    raise TypeError('group child data must be a dict')
                data = dict(properties)
                if 'items' in data:
                    data['items'] = validateDropdownItems(data['items'])
                if 'callbacks' in data:
                    callbacks = {}
                    for event, callback in data['callbacks'].items():
                        callbackId = len(self._btnCallbacks)
                        self._btnCallbacks[callbackId] = callback
                        callbacks[event] = callbackId
                    data['callbacks'] = callbacks
                if 'children' in data:
                    data['children'] = encode(data['children'])
                result[name] = data
            return result
        defaults = getSystem().screen.getDefaultStyle('group', {
            'class': '', 'width': '100%-8px', 'height': 'default',
            'offsetX': 4, 'offsetY': 0, 'visible': True,
        })
        defaults.update(style)
        groupLayout = dict(defaults)
        for pair, axes in (('offset', ('offsetX', 'offsetY')), ('size', ('width', 'height'))):
            if pair in style:
                pairValue = style[pair]
                values = pairValue.getValue() if pairValue.__class__.__name__ == 'Observable' else pairValue
                if not isinstance(values, list) or len(values) != 2:
                    raise ValueError('group style %s must be a list with two elements' % pair)
                for i, axis in enumerate(axes):
                    if axis not in style:
                        defaults[axis] = values[i]
                        groupLayout.pop(axis, None)
                defaults.pop(pair, None)
        self._appendControl({'children': encode(children), 'style': defaults, 'group': True, '_groupLayout': groupLayout})
        return self

    def custom(self, params={}, style={}):
        """Add a native template with client-side creation/update callbacks and parameter values."""
        if not isinstance(params, dict):
            raise TypeError('custom params must be a dict')
        defaultStyle = getSystem().screen.getDefaultStyle("custom", {
            "class": "oreui:light_panel_thin",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self._appendControl({
            "params": dict(params),
            "style": defaultStyle
        })
        return self

    def show(self, target=None):
        """
        显示表单，显示配置由创建时的style提供。
        """
        validateGrids(self.__style['grids'])
        if isServer():
            if target is None:
                import mod.server.extraServerApi as s
                target = s.GetPlayerList()
            targets = [target] if isinstance(target, str) else list(target)
        else:
            import mod.client.extraClientApi as c
            targets = [c.GetLocalPlayerId()]
        targets = list(dict.fromkeys(targets))
        if any(self._isShowing.get(playerId, False) for playerId in targets):
            raise RuntimeError('该表单已经被显示出来了，关闭后才能再次调用 show()。')
        # Wrap data.
        from ..utils.type import wrapDict
        observables = []
        data = wrapDict({
            "formId": self.__id,
            "title": self.__title,
            "controls": self.__controls,
            "style": self.__style,
            "fromServer": isServer()
        }, observables)
        data['observables'] = observables
        result = FormShowResult(self.__id, targets)
        previous = dict(self._isShowing)
        for playerId in targets:
            self._isShowing[playerId] = True
        # Send data.
        try:
            if isServer():
                if isinstance(target, str):
                    getSystem().NotifyToClient(target, "showForm", data)
                else:
                    getSystem().NotifyToMultiClients(targets, "showForm", data)
            else:
                getSystem().showForm(data)
        except:
            result._cancel()
            for playerId in targets:
                if playerId in previous:
                    self._isShowing[playerId] = previous[playerId]
                else:
                    self._isShowing.pop(playerId, None)
            raise
        return result

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
