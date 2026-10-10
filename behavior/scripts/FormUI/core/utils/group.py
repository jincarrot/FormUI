# -*- coding: utf-8 -*-
"""Validation and binding-preserving styles for registered control groups."""
from .type import unwrapWrappedValue, wrapVariable
from .ui import getSizeDict


GROUP_KEYS = frozenset(('class', 'offset', 'size', 'offsetX', 'offsetY',
                        'width', 'height', 'visible'))


def validateGroupControls(controls):
    if not isinstance(controls, dict):
        raise TypeError('Group controls must be a dict')
    result = {}
    for name, definition in controls.items():
        if not isinstance(name, str) or not name or '/' in name or name in ('.', '..'):
            raise ValueError('Group child names must be nonempty names without slashes')
        if not isinstance(definition, dict):
            raise TypeError('Group child %s must be a dict' % name)
        if 'class' not in definition:
            raise ValueError('Group child %s requires class' % name)
        unknown = set(definition) - GROUP_KEYS
        if unknown:
            raise ValueError('Unsupported Group child properties: %s' % sorted(unknown))
        copied = dict(definition)
        for key, value in definition.items():
            current = value.getValue() if value.__class__.__name__ == 'Observable' else value
            if key == 'class':
                if not isinstance(current, str) or not current:
                    raise ValueError('Group child class must be a nonempty string')
            elif key in ('offset', 'size'):
                if not isinstance(current, list) or len(current) != 2:
                    raise ValueError('Group %s must be a list with two elements' % key)
                for item in current:
                    getSizeDict(item.getValue() if item.__class__.__name__ == 'Observable' else item)
                if isinstance(value, list):
                    copied[key] = list(value)
            elif key == 'visible':
                if not isinstance(current, bool):
                    raise TypeError('Group visible must be a bool or an Observable bool')
            else:
                getSizeDict(current)
        result[name] = copied
    return result


def groupStyle(definition):
    """Keep scalar bindings; pair Observable values are resolved at each layout."""
    style = {'class': definition['class'], 'visible': wrapVariable(True)}
    for pair, axes, fallback in (('offset', ('offsetX', 'offsetY'), 0),
                                 ('size', ('width', 'height'), 'default')):
        value = definition.get(pair)
        if isinstance(value, dict):
            values = unwrapWrappedValue(value)
            if not isinstance(values, list) or len(values) != 2:
                raise ValueError('Group %s must be a list with two elements' % pair)
            values = [wrapVariable(item) for item in values]
        else:
            values = value if value is not None else [wrapVariable(fallback), wrapVariable(fallback)]
            if not isinstance(values, list) or len(values) != 2:
                raise ValueError('Group %s must be a list with two elements' % pair)
        for i, key in enumerate(axes):
            style[key] = definition.get(key, values[i])
    style['visible'] = definition.get('visible', style['visible'])
    return style


def iterControls(controls):
    def children(address, control):
        yield address, control
        prefix = address if isinstance(address, tuple) else (address,)
        for name, child in control.get('children', {}).items():
            for entry in children(prefix + (name,), child):
                yield entry
    for index, control in enumerate(controls):
        for entry in children(index, control):
            yield entry


def collectObservableIds(data):
    ids = set()
    def visit(value):
        if isinstance(value, dict):
            if value.get('type') == 'Observable' and value.get('obId') is not None:
                ids.add(value['obId'])
            else:
                for item in value.values():
                    visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
    visit(data)
    return ids
