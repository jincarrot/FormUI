# -*- coding: utf-8 -*-
from ..lib import Form, Observable as FormObservable
from ..core.utils.environment import getSystem, isServer
from ..core.utils.ui import STRING_TYPES
from ._layout import windowRect
from ._observable import Observable, binding, current, optionsDict


def validatePlayer(playerId):
    if not isServer():
        raise RuntimeError('MoreUI forms must be created on the server')
    if not isinstance(playerId, STRING_TYPES) or not playerId:
        raise ValueError('playerId must be a nonempty string')


def sendForms(playerId, group, forms):
    prepared, reopen = [], []
    try:
        for form in forms:
            if form._isShowing():
                if form._closing:
                    reopen.append((form, form._reopen))
                continue
            form._closing = form._reopen = False
            entry = form._entry
            config = form._windowConfig(entry)

            def closed(args, owner=form, placement=entry):
                owner._onClose(args, placement)

            payload, result, previous = form._form._prepareShow([playerId], closed, config)
            prepared.append((form._form, payload, result, previous))
        for form, previous in reopen:
            form._reopen = True
        if prepared:
            getSystem().NotifyToClient(playerId, 'showFormGroup', {
                'group': group, 'forms': [record[1] for record in prepared],
            })
    except:
        for form, payload, result, previous in prepared:
            form._cancelShow(result, previous)
        for form, previous in reopen:
            if form._closing:
                form._reopen = previous
        raise


def _writable(value, accepted):
    if not isinstance(value, Observable) or not current(value._options['clientWritable']):
        raise TypeError('MoreUI input controls require a clientWritable Observable')
    data = value.getData()
    if not accepted(data):
        raise TypeError('Invalid value type for MoreUI input control: %s' % type(data).__name__)
    return value._binding


def _controlStyle(options):
    return {'visible': binding(optionsDict(options).get('visible', True)), 'grid': None}


def _boundParams(value):
    if isinstance(value, dict):
        return {key: _boundParams(entry) for key, entry in value.items()}
    if isinstance(value, (list, tuple)):
        return [_boundParams(entry) for entry in value]
    return binding(value)


class DynamicForm(object):
    """【已废弃】绑定单个玩家的旧版表单。"""

    def __init__(self, playerId, title, options=None, root=None, closable=True):
        validatePlayer(playerId)
        self._playerId = playerId
        self._title = title
        self._options = optionsDict(options)
        for key, default in (('movable', False), ('resizable', False), ('closable', closable)):
            self._options.setdefault(key, default)
        theme = self._options.get('style', 'oreui')
        if theme != 'oreui' and theme not in getSystem().screen.themes.names():
            theme = 'oreui'
        self._visible = FormObservable.create(True)
        self._form = Form.create(binding(title), {
            'width': '40%', 'height': '80%', 'grids': [1], 'visible': self._visible,
            'layer': 0, 'offsetX': 0, 'offsetY': 0, 'grid': None, 'hideOtherForms': False,
        }, theme=theme, layout=False, root=root)
        self._entry = None
        self._closing = False
        self._reopen = False

    @property
    def formId(self):
        return self._form.formId

    def _windowConfig(self, entry):
        config = {key: binding(self._options[key]) for key in ('movable', 'resizable', 'closable')}
        if entry is not None:
            config.update(entry._flags)
            grid = entry._owner.layout
            windowRect(grid._snapshot(), entry.layout._snapshot())
            config.update(grid=grid._observable(), layout=entry.layout._observable())
        return config

    def _onClose(self, args, entry):
        reopen = self._reopen
        self._closing = self._reopen = False
        if entry is not None and args.closeReason == 'user' and entry.mayCloseAll.getData():
            entry._owner.close()
        elif reopen and args.closeReason == 'api':
            self.show()

    def show(self):
        group = self._entry._owner._group if self._entry is not None else 'moreui:form:%s' % self.formId
        sendForms(self._playerId, group, [self])
        return self

    def _isShowing(self):
        return self._form._isShowing.get(self._playerId, False)

    def close(self):
        self._reopen = False
        if not self._closing and self._isShowing():
            self._closing = True
            try:
                self._form.close(self._playerId)
            except:
                self._closing = False
                raise
        return self

    def _addButton(self, label, onClick, style, params=None):
        if not callable(onClick):
            raise TypeError('onClick must be callable')

        def clicked(playerId):
            if playerId == self._playerId:
                onClick()

        self._form.button(binding(label), clicked, style, params or {})
        return self

    def button(self, label, onClick, options=None):
        return self._addButton(label, onClick, _controlStyle(options))


class CustomForm(DynamicForm):
    """【已废弃】支持旧版链式输入和显示接口的通用表单。"""

    @staticmethod
    def create(playerId, title, options=None):
        return CustomForm(playerId, title, options)

    def label(self, text, options=None):
        self._form.label(binding(text), _controlStyle(options))
        return self

    def divider(self, options=None):
        self._form.divider(_controlStyle(options))
        return self

    def spacer(self, options=None):
        return self.label('', options)

    def textField(self, label, text, options=None):
        self._form.textfield(binding(label), _writable(text, lambda value: isinstance(value, STRING_TYPES)),
                             _controlStyle(options))
        return self

    def toggle(self, label, toggled, options=None):
        self._form.toggle(binding(label), _writable(toggled, lambda value: isinstance(value, bool)),
                          _controlStyle(options))
        return self

    def slider(self, label, value, minValue, maxValue, options=None):
        self._form.slider(binding(label), _writable(value, lambda value: type(value) in (int, float)),
                          binding(minValue), binding(maxValue), style=_controlStyle(options))
        return self

    def dropdown(self, label, value, items, options=None):
        self._form.dropdown(binding(label), items, _writable(value, lambda value: type(value) in (int, float)),
                            _controlStyle(options))
        return self

    def custom(self, identifier, params):
        self._form.custom(_boundParams(params), style={'class': identifier, 'grid': None})
        return self


class BarForm(DynamicForm):
    """【已废弃】由按钮组成的横栏或侧栏。"""

    def __init__(self, playerId, title, options=None):
        DynamicForm.__init__(self, playerId, title, options, root='moreui:bar', closable=False)
        self._direction = self._options.get('direction', 'vertical')
        if self._direction not in ('horizontal', 'vertical'):
            raise ValueError('BarForm direction must be horizontal or vertical')

    @staticmethod
    def create(playerId, title, options=None):
        return BarForm(playerId, title, options)

    def _windowConfig(self, entry):
        config = DynamicForm._windowConfig(self, entry)
        config['direction'] = self._direction
        return config

    def _icon(self, path, selected, callback, options):
        style = _controlStyle(options)
        style.update({'class': 'moreui:icon_tab', 'height': 36})
        return self._addButton('', callback, style, {'iconPath': path, 'selected': selected})
