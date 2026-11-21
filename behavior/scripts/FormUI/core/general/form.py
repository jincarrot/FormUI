# -*- coding: utf-8 -*-
from ..utils.environment import *
from ..utils.type import FormShowResultArgs, copyContainers
from ..utils.ui import validateGrids, validateDropdownItems, getFontScale, validateListViewItems, validateListViewHeight, normalizeTargets, STRING_TYPES
from ..utils.grid import validateGrid, validateCell, planCells
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
        pending, self.__pendingPlayers = self.__pendingPlayers, set()
        return pending

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
        if callback is not None and not callable(callback):
            raise TypeError('onClose must be callable or None')
        self.__callback = callback
        

class Form:
    """
    自定义表单类（客户端服务端通用）
    """
    
    def __init__(self, id, title="", style=None, theme=None, grid=None, layout=None):
        if style is None:
            style = {}
        if not isinstance(style, dict):
            raise TypeError('form style must be a dict')
        screen = getSystem().screen
        name = screen.getDefaultTheme() if theme is None else theme
        self.__theme = screen.themes.get(name) if name is not None else {}
        self.__screenGrid = screen.getGrid()
        style = copyContainers(style)
        if grid is not None:
            style['grid'] = grid
        if layout is not None:
            style['layout'] = layout
        self.__id = id
        self.__title = title
        self.__controls = []
        defaultStyle = self._getDefaultStyle("scrolling_panel", {
            "class": "oreui:light_panel_thin",
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
        if defaultStyle.get('grid') is not None:
            if self.__screenGrid is None:
                raise ValueError('Form grid position requires Screen.setGrid()')
            defaultStyle['grid'] = validateCell(defaultStyle['grid'], self.__screenGrid)
            # A positioned window fills its cell unless a caller/default/theme sizes it.
            configured = screen.getDefaultStyle('scrolling_panel')
            configured.update(self.__theme.get('scrolling_panel', {}))
            configured.update(style)
            for key, value in (('width', '100%'), ('height', '100%')):
                if key not in configured:
                    defaultStyle[key] = value
        inherited = None if 'grids' in style else self.__screenGrid
        contentGrid = defaultStyle.get('layout', inherited)
        defaultStyle['layout'] = validateGrid(contentGrid) if contentGrid is not None and contentGrid is not False else None
        self.__style = copyContainers(defaultStyle)
        self.__template = None
        self._isShowing = {}
        self.identifier = ""
        self._btnCallbacks = {
            0: lambda x: None
        }

    def _getDefaultStyle(self, kind, fallback):
        if kind != 'scrolling_panel' and self.__style.get('layout') is not None:
            fallback = dict(fallback, width='100%', height='100%', offsetX=0, offsetY=0)
        style = copyContainers(getSystem().screen.getDefaultStyle(kind, fallback))
        if kind in self.__theme:
            style.update(copyContainers(self.__theme[kind]))
        return style

    def getShowingPlayers(self):
        """Return online players currently showing or waiting to create this form."""
        if isServer():
            import mod.server.extraServerApi as s
            players = s.GetPlayerList()
        else:
            import mod.client.extraClientApi as c
            players = [c.GetLocalPlayerId()]
        return [player for player in players if self._isShowing.get(player, False)]

    def isAnyShowing(self):
        """Whether at least one online player is showing this form."""
        return bool(self.getShowingPlayers())

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
    
    def button(self, label, callbacks={}, style={}, params={}, grid=None):
        # type: (str, dict, dict, dict) -> Form
        """
        添加一个按钮。
        """
        if callable(callbacks):
            callbacks = {'onClick': callbacks}
        elif callbacks is None:
            callbacks = {}
        self._validateButtonCallbacks(callbacks)
        temp = {}
        for key in callbacks:
            self._btnCallbacks[len(self._btnCallbacks)] = callbacks[key]
            temp[key] = len(self._btnCallbacks) - 1
        defaultCallbacks = {
            "onClick": 0,
            "onMoveIn": 0,
            "onMoveOut": 0
        }
        defaultStyle = self._getDefaultStyle("button", {
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
        }, params, grid)
        return self

    @staticmethod
    def _validateButtonCallbacks(callbacks):
        if not isinstance(callbacks, dict):
            raise TypeError('button callbacks must be a callable or a dict')
        for name, callback in callbacks.items():
            if name not in ('onClick', 'onMoveIn', 'onMoveOut'):
                raise ValueError('Unknown button callback: %s' % name)
            if not callable(callback):
                raise TypeError('button callback %s must be callable' % name)

    def _appendControl(self, control, params={}, grid=None):
        """Store independent instance params and an explicit creation-mode marker."""
        if not isinstance(params, dict):
            raise TypeError('control params must be a dict')
        control = copyContainers(control)
        if grid is not None:
            control['style']['grid'] = copyContainers(grid)
        layout = self.__style.get('layout')
        if control['style'].get('grid') is not None:
            if layout is None:
                raise ValueError('Control grid position requires form layout or Screen.setGrid()')
            control['style']['grid'] = validateCell(control['style']['grid'], layout)
        if control['style'].get('layout') is not None:
            control['style']['layout'] = validateGrid(control['style']['layout'])
        if '_groupLayout' in control:
            for key in ('grid', 'layout'):
                if key in control['style']:
                    control['_groupLayout'][key] = copyContainers(control['style'][key])
        if layout is not None:
            planCells([(i, entry['style'].get('grid'))
                       for i, entry in enumerate(self.__controls + [control])], layout)
        control['params'] = copyContainers(params)
        control.setdefault('custom', False)
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
    
    def toggle(self, label, state, style={}, params={}, grid=None):
        """
        添加一个开关。
        """
        defaultStyle = self._getDefaultStyle("toggle", {
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
        }, params, grid)
        return self

    def divider(self, style={}, params={}, grid=None):
        # type: (dict, dict) -> Form
        """
        添加一个分割线。
        """
        defaultStyle = self._getDefaultStyle("divider", {
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
        }, params, grid)
        return self

    def label(self, text, style={}, params={}, grid=None):
        # type: (str, dict, dict) -> Form
        """
        添加一个文本控件。
        """
        defaultStyle = self._getDefaultStyle("label", {
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
        }, params, grid)
        return self

    def slider(self, label, value, minValue=0.0, maxValue=1.0, step=1, style={}, params={}, grid=None):
        """添加滑动条；step=0 为连续模式，负步长取绝对值，反向边界自动排序。"""
        defaultStyle = self._getDefaultStyle("slider", {
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
        }, params, grid)
        return self

    def textfield(self, label, value, style={}, params={}, grid=None):
        defaultStyle = self._getDefaultStyle("textfield", {
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
        }, params, grid)
        return self

    def dropdown(self, label, items, value, style={}, params={}, grid=None):
        items = validateDropdownItems(items)
        defaultStyle = self._getDefaultStyle("dropdown", {
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
        }, params, grid)
        return self
    
    def listview(self, label, items, value=None, style={}, params={}, grid=None):
        """添加内部滚动的单选列表；items 和 value 可绑定 Observable。"""
        bound = items.__class__.__name__ == 'Observable'
        checked = validateListViewItems(items.getValue() if bound else items)
        defaults = self._getDefaultStyle('listview', {
            'class': 'oreui:listview', 'width': '100%-8px', 'height': 160,
            'offsetX': 4, 'offsetY': 0, 'visible': True,
            'itemHeight': 32, 'emptyText': '暂无内容',
        })
        defaults.update(style)
        height = defaults['itemHeight']
        validateListViewHeight(height.getValue() if height.__class__.__name__ == 'Observable' else height)
        self._appendControl({
            'label': label, 'items': items if bound else checked,
            'value': value, 'style': defaults,
        }, params, grid)
        return self

    def group(self, children={}, style={}, params={}, grid=None):
        """Add a registered Group; children supplies named child values and callbacks."""
        if not isinstance(children, dict):
            raise TypeError('group children must be a dict')
        def encode(entries):
            result = {}
            for name, properties in entries.items():
                if not isinstance(properties, dict):
                    raise TypeError('group child data must be a dict')
                data = dict(properties)
                if 'params' in data:
                    if not isinstance(data['params'], dict):
                        raise TypeError('group child params must be a dict')
                    data['params'] = dict(data['params'])
                if 'items' in data and data['items'].__class__.__name__ != 'Observable':
                    data['items'] = validateDropdownItems(data['items'])
                if 'callbacks' in data:
                    if callable(data['callbacks']):
                        data['callbacks'] = {'onClick': data['callbacks']}
                    self._validateButtonCallbacks(data['callbacks'])
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
        defaults = self._getDefaultStyle('group', {
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
        self._appendControl({'children': encode(children), 'style': defaults, 'group': True, '_groupLayout': groupLayout}, params, grid)
        return self

    def custom(self, params={}, style={}, grid=None):
        """Add a native template with client-side creation/update callbacks and parameter values."""
        if not isinstance(params, dict):
            raise TypeError('custom params must be a dict')
        defaultStyle = self._getDefaultStyle("custom", {
            "class": "oreui:light_panel_thin",
            "width": "100%-8px",
            "height": "default",
            "offsetX": 4,
            "offsetY": 0,
            "visible": True
        })
        defaultStyle.update(style)
        self._appendControl({
            "custom": True,
            "style": defaultStyle
        }, params, grid)
        return self

    def bindTemplate(self, name=None):
        """绑定已生成的 JSON UI。当前控件组成模板，后续追加的控件仍可动态创建。"""
        if name is None:
            self.__template = None
        else:
            from ..utils.template import validateTemplateName
            self.__template = {'name': validateTemplateName(name), 'count': len(self.__controls)}
        return self

    def toJsonUI(self, name):
        """生成可写入资源包的 JSON UI 字典。使用当前端注册的原生控件定义。"""
        from ..utils.template import templateStructure, exportTemplate, validateTemplateName
        from ..utils.type import wrapList
        validateTemplateName(name)
        count = len(self.__controls)
        if self.__template is not None and self.__template['name'] == name:
            count = self.__template['count']
        controls = wrapList(self.__controls[:count])
        rootClass = self.__style['class']
        if rootClass.__class__.__name__ == 'Observable':
            rootClass = rootClass.getValue()
        structure = templateStructure(getSystem().controlManager, rootClass, controls)
        return exportTemplate(name, structure, controls)

    def show(self, target=None, onClose=None, options=None):
        """显示表单。options 中的 combineUI=True 将本次表单挂载到玩家当前的界面。"""
        validateGrids(self.__style['grids'])
        serverSide = isServer()
        if not serverSide and isinstance(target, dict) and options is None:
            options, target = target, None
        if isinstance(onClose, dict) and options is None:
            options, onClose = onClose, None
        if options is None:
            options = {}
        if not isinstance(options, dict) or any(key != 'combineUI' for key in options):
            raise TypeError('show options must be a dict containing only combineUI')
        combineUI = options.get('combineUI', False)
        if not isinstance(combineUI, bool):
            raise TypeError('combineUI must be a bool')
        if onClose is not None and not callable(onClose):
            raise TypeError('onClose must be callable or None')
        if serverSide:
            if target is None:
                import mod.server.extraServerApi as s
                target = s.GetPlayerList()
            targets = normalizeTargets(target)
        else:
            import mod.client.extraClientApi as c
            targets = [c.GetLocalPlayerId()]
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
            "screenGrid": self.__screenGrid,
            "fromServer": serverSide
        }, observables)
        data['observables'] = observables
        if self.__template is not None:
            data['template'] = dict(self.__template)
        if combineUI:
            data['options'] = {'combineUI': True}
        result = FormShowResult(self.__id, targets)
        result.onClose(onClose)
        if not targets:
            return result
        previous = dict(self._isShowing)
        for playerId in targets:
            self._isShowing[playerId] = True
        # Send data.
        try:
            if serverSide:
                if isinstance(target, STRING_TYPES):
                    getSystem().NotifyToClient(target, "showForm", data)
                else:
                    getSystem().NotifyToMultiClients(targets, "showForm", data)
            else:
                getSystem().showForm(data)
        except:
            for playerId in result._cancel():
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
        if target is None:
            if isServer():
                import mod.server.extraServerApi as s
                target = s.GetPlayerList()
            else:
                import mod.client.extraClientApi as c
                target = c.GetLocalPlayerId()
        if isServer():
            targets = normalizeTargets(target)
            if not targets:
                return
            if isinstance(target, STRING_TYPES):
                getSystem().NotifyToClient(target, "closeForm", data)
            else:
                getSystem().NotifyToMultiClients(targets, "closeForm", data)
        else:
            getSystem().closeForm(data)
