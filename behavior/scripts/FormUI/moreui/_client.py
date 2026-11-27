# -*- coding: utf-8 -*-
from ..core.utils.group import collectObservableIds
from ..core.utils.type import unwrapWrappedValue
from ._layout import windowRect


_DEFAULT_RECT = ((0.30, 0), (0.10, 0), (0.40, 0), (0.80, 0))
_DRAG_HANDLES = (('movable', 'move_handle', 4), ('resizable', 'resize_handle', -3))


def _dimension(relative=0, absolute=0):
    return {'relativeValue': relative, 'absoluteValue': absolute, 'followType': 'parent'}


def _setSelected(control, selected):
    mark = control.GetChildByPath('/selected')
    if mark:
        mark.SetVisible(bool(selected))


def _createIcon(args):
    icon = args.control.GetChildByPath('/icon')
    if icon and args.params['iconPath']:
        icon.asImage().SetSprite(args.params['iconPath'])
        icon.SetVisible(True)
    _setSelected(args.control, args.params['selected'])


def registerControls(manager):
    if manager.has('moreui:bar'):
        return
    manager.create('panel', 'moreui:bar', 'fui_moreui.bar', {
        'contentPath': '/body', 'titlePath': '/header/title', 'closeBtnPath': '/header/close',
    })
    manager.create('button', 'moreui:icon_tab', 'fui_moreui.icon_tab', {
        'buttonPath': '/plate/button', 'labelPaths': (), 'onCreate': _createIcon,
    })


class Window(object):
    def __init__(self, screen, formId, root, close):
        self._screen = screen
        self._id = formId
        self._root = root
        self._close = close
        self._form = screen.forms[formId]
        self._config = self._form['moreui']
        self._bindings = collectObservableIds(self._config)
        self._bar = self._form['style']['class']['value'] == 'moreui:bar'
        self.grouped = 'grid' in self._config
        self.horizontal = False
        self._rect = None
        self._layer = None
        self._closable = None
        self._handles = {}
        self._enabled = set()
        self._lastDelta = {}
        self._polling = False

    def apply(self, obId=None):
        if obId is not None:
            if self._bar:
                self._updateTabs(obId)
            if obId not in self._bindings:
                return False
        config = unwrapWrappedValue(self._config)
        rect = _DEFAULT_RECT
        if self.grouped:
            rect = windowRect(config['grid'], config['layout'])
            layer = int(config['layout']['layer']) * 50
            if layer != self._layer:
                self._root.SetLayer(layer)
                self._layer = layer
        changed = self._setRect(rect)
        horizontal = config.get('direction') == 'horizontal'
        changed = changed or self.horizontal != horizontal
        self.horizontal = horizontal
        closable = bool(config['closable'])
        if self._close and closable != self._closable:
            self._close.SetVisible(closable)
            self._closable = closable
        for flag, name, offset in _DRAG_HANDLES:
            self._setHandle(flag, name, bool(config[flag]))
        if self._enabled and not self._polling:
            self._polling = True
            self._screen.addRepeatFunc(self._poll, 1)
        return changed

    def _setRect(self, rect):
        if rect == self._rect:
            return False
        resized = self._rect is None or self._rect[2:] != rect[2:]
        if self._rect is None:
            self._root.SetAnchorFrom('top_left')
            self._root.SetAnchorTo('top_left')
        for index, axis in enumerate(('x', 'y')):
            self._root.SetFullPosition(axis, _dimension(*rect[index]))
            if resized:
                self._root.SetFullSize(axis, _dimension(*rect[index + 2]))
        self._rect = rect
        return resized

    def _setHandle(self, flag, name, enabled):
        handle = self._handles.get(flag)
        if enabled and handle is None:
            native = self._screen.CreateChildControl('fui_moreui.' + name, name, self._root)
            handle = native.asInputPanel() if native else None
            if handle is None:
                return
            self._handles[flag] = handle
            self._lastDelta[flag] = (0, 0)
        if handle is not None and enabled != (flag in self._enabled):
            handle.SetVisible(enabled)
            if enabled:
                self._enabled.add(flag)
            else:
                self._enabled.discard(flag)

    def _poll(self):
        if self._screen.forms.get(self._id) is not self._form or not self._enabled:
            self._polling = False
            return
        self._screen.addRepeatFunc(self._poll, 1)
        if not self._form['style']['visible']['value']:
            return
        for flag, name, offset in _DRAG_HANDLES:
            if flag in self._enabled:
                self._drag(flag, offset)

    def _drag(self, flag, offset):
        handle = self._handles[flag]
        delta = handle.GetOffsetDelta()
        previous = self._lastDelta[flag]
        if delta is None or delta == previous:
            return
        self._lastDelta[flag] = delta
        resizing = flag == 'resizable'
        size = self._root.GetSize() if resizing else None
        changed = False
        for index, axis in enumerate(('x', 'y')):
            difference = delta[index] - previous[index]
            if not difference:
                continue
            # The handle follows its parent. Cancel the handle's own drag offset.
            handle.SetFullPosition(axis, _dimension(0, offset - delta[index]))
            if resizing:
                difference = max(60, size[index] + difference) - size[index]
                geometry = dict(self._root.GetFullSize(axis))
                setter = self._root.SetFullSize
            else:
                geometry = dict(self._root.GetFullPosition(axis))
                setter = self._root.SetFullPosition
            if difference:
                geometry['absoluteValue'] = geometry.get('absoluteValue', 0) + difference
                setter(axis, geometry)
                changed = True
        if resizing and changed:
            self._screen._relayoutForm(self._id)
            self._screen._layoutGroups(self._id)

    def _updateTabs(self, obId):
        bindings = self._screen._getFormBindings(self._id)
        for index, data in bindings.controls.get(obId, ()):
            if data['style']['class']['value'] != 'moreui:icon_tab':
                continue
            selected = data['params']['selected']
            if selected.get('obId') == obId:
                native = self._screen.getControl(self._id, index)
                if native:
                    _setSelected(native, selected['value'])

    def layoutBar(self):
        x = 4
        for index, data in enumerate(self._form['controls']):
            control = self._screen.getControl(self._id, index)
            if not control:
                continue
            visible = bool(data['style']['visible']['value'])
            control.SetVisible(visible)
            if visible:
                control.SetFullPosition('x', _dimension(0, x))
                control.SetFullPosition('y', _dimension(0, 4))
                control.SetFullSize('x', _dimension(0, 40))
                control.SetFullSize('y', _dimension(0, 20))
                x += 45
