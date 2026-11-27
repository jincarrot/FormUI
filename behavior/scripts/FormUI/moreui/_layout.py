# -*- coding: utf-8 -*-
from ._observable import FormObservable, NativeObservable, Observable, current, optionsDict
from ..core.utils.grid import cellRect, validateCell, validateGrid
from ..core.utils.ui import _finiteNumber


def _layoutProperty(name):
    def get(layout):
        return layout._values[name]

    def setValue(layout, value):
        layout._values[name] = layout._normalize(name, value)
        if layout._binding is not None:
            layout._bindSources()
            layout._publish()

    return property(get, setValue)


class _Layout(object):
    _defaults = {}
    _lengths = {}

    def __init__(self, layout=None):
        self._binding = None
        self._sources = []
        self._replace(layout)

    def _normalize(self, name, value):
        if name == 'layer':
            return value
        if not isinstance(value, (list, tuple)) or not value:
            raise TypeError('%s must be a nonempty list or tuple' % name)
        if name == 'margin' and len(value) == 2:
            value = list(value) * 2
        if name in self._lengths and len(value) != self._lengths[name]:
            raise ValueError('%s must have %s entries' % (name, self._lengths[name]))
        return list(value)

    def _replace(self, layout):
        config = optionsDict(layout)
        self._values = {name: self._normalize(name, config.get(name, default))
                        for name, default in self._defaults.items()}
        if self._binding is not None:
            self._bindSources()
            self._publish()

    def _snapshot(self, source=None, newValue=None):
        def resolve(value):
            return newValue if value is source else current(value)
        return {key: [resolve(item) for item in value] if isinstance(value, list) else resolve(value)
                for key, value in self._values.items()}

    def _publish(self, source=None, newValue=None):
        self._binding.setValue(self._snapshot(source, newValue))

    def _unbindSources(self):
        for source, callback in self._sources:
            source.unsubscribe(callback)
        self._sources = []

    def _bindSources(self):
        self._unbindSources()
        seen = set()
        def subscribe(source):
            if isinstance(source, (NativeObservable, Observable)) and id(source) not in seen:
                seen.add(id(source))
                def changed(value):
                    self._publish(source, value)
                self._sources.append((source, changed))
                source.subscribe(changed)
        for value in self._values.values():
            if isinstance(value, list):
                for item in value:
                    subscribe(item)
            else:
                subscribe(value)

    def _observable(self):
        if self._binding is None:
            self._binding = FormObservable.create(self._snapshot())
        else:
            self._publish()
        self._bindSources()
        return self._binding


class FormLayout(_Layout):
    """【已废弃】子表单的位置、跨度、边距、偏移和层级。"""

    _defaults = dict(position=(0, 0), size=(1, 1), offset=(0, 0), margin=(0, 0, 0, 0), layer=0)
    _lengths = dict(position=2, size=2, offset=2, margin=4)
    position = _layoutProperty('position')
    size = _layoutProperty('size')
    offset = _layoutProperty('offset')
    margin = _layoutProperty('margin')
    layer = _layoutProperty('layer')


class MoreUILayout(_Layout):
    """【已废弃】MoreUI 容器的行列权重。"""

    _defaults = dict(row=(1,), column=(1,))
    row = _layoutProperty('row')
    column = _layoutProperty('column')


def windowRect(grid, layout):
    grid = validateGrid({'columns': grid['column'], 'rows': grid['row']})
    column, row = layout['position']
    columnSpan, rowSpan = layout['size']
    cell = validateCell(dict(column=column, row=row, columnSpan=columnSpan, rowSpan=rowSpan), grid)
    x, y, width, height = cellRect(grid, cell, (1.0, 1.0))
    dx, dy = (_finiteNumber(value, 'offset') for value in layout['offset'])
    top, right, bottom, left = (_finiteNumber(value, 'margin') for value in layout['margin'])
    return ((x, dx + left), (y, dy + top), (width, -left - right), (height, -top - bottom))
