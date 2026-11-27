# -*- coding: utf-8 -*-

import math
import re

try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)


def normalizeTargets(target):
    """Materialize nonempty player IDs once; an explicit empty collection stays empty."""
    if isinstance(target, STRING_TYPES):
        players = [target]
    else:
        if isinstance(target, dict):
            raise TypeError('target must be a player ID or an iterable of player IDs')
        try:
            players = list(target)
        except TypeError:
            raise TypeError('target must be a player ID or an iterable of player IDs')
    unique, seen = [], set()
    for player in players:
        if not isinstance(player, STRING_TYPES) or not player:
            raise ValueError('player IDs must be nonempty strings')
        if player not in seen:
            seen.add(player)
            unique.append(player)
    return unique

# 网易运行时使用 Python 2；long 同样是有效整数，无需依赖 numbers。
try:
    _NUMBER_TYPES = (int, long, float)
except NameError:
    _NUMBER_TYPES = (int, float)


def validateGrids(grids):
    """Return a copy of non-empty, finite, positive column weights."""
    if not isinstance(grids, (list, tuple)) or not grids:
        raise ValueError("grids must be a non-empty list of positive numbers")
    weights = list(grids)
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, _NUMBER_TYPES):
            raise ValueError("grids weights must be finite positive numbers")
        try:
            value = float(weight)
        except (ValueError, OverflowError):
            raise ValueError("grids weights must be finite positive numbers")
        if value <= 0 or math.isnan(value) or math.isinf(value):
            raise ValueError("grids weights must be finite positive numbers")
    total = sum(float(weight) for weight in weights)
    if math.isinf(total):
        raise ValueError("grids weight sum must be finite")
    return weights


def isFormScreen(screen):
    return hasattr(screen, "isFormScreen")

def getTopScreenNode():
    import mod.client.extraClientApi as c
    getter = getattr(c, 'GetTopUINode', None)
    if getter is not None:
        return getter()
    node = c.GetTopScreen()
    # Older SDKs expose only pushed mod nodes. A native screen can cover that node.
    getName = getattr(node, 'GetScreenName', None)
    getTopName = getattr(c, 'GetTopUI', None)
    if getName is not None and getTopName is not None:
        name = getName()
        if not name or getTopName() not in (name, name.rsplit('.', 1)[-1]):
            return None
    return node

def notifyFormClosed(system, formId, reason):
    import mod.client.extraClientApi as c
    event = 'formClose%s' % formId
    payload = {'closeReason': reason, 'playerId': c.GetLocalPlayerId()}
    system.NotifyToServer(event, payload)
    system.BroadcastEvent(event, payload)


def getFormRoot(manager, name):
    root = manager.get(name)
    if root is None or root.typeId not in ('panel', 'scrolling_panel'):
        raise ValueError('Form root %r must be a registered Panel or ScrollingPanel' % name)
    return root


def getFormContentPath(root):
    key = 'scrollingPanelPath' if root.typeId == 'scrolling_panel' else 'contentPath'
    return root.options.get(key) or ''


def getFormContent(viewport, scrolling):
    return getScrollingContent(viewport) if viewport and scrolling else viewport


def getScrollingContent(control):
    target = control.GetChildByPath("/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content")
    if not target:
        target = control.GetChildByPath("/scroll_touch/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content")
    return target

def _finiteNumber(value, name):
    if isinstance(value, bool) or not isinstance(value, _NUMBER_TYPES):
        raise ValueError("%s must be a finite number" % name)
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise ValueError("%s must be a finite number" % name)
    if math.isnan(number) or math.isinf(number):
        raise ValueError("%s must be a finite number" % name)
    return number


_DIMENSION_TERM = re.compile(r"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(%[xy]?|px)?")


def getSizeDict(info):
    """Parse pixels and percentages, including signed decimal expressions."""
    if isinstance(info, _NUMBER_TYPES):
        _finiteNumber(info, 'dimension')
        return {"absoluteValue": info, "relativeValue": 0.0, "followType": "parent"}
    if not isinstance(info, str):
        raise ValueError("Invalid dimension: %r" % (info,))
    expression = re.sub(r"\s+", "", info)
    if expression == 'default':
        return None
    if expression == 'fill':
        expression = '100%'
    absolute = relative = 0.0
    follow = None
    position = 0
    while position < len(expression):
        sign = 1
        if position:
            if expression[position] not in '+-':
                raise ValueError("Invalid dimension: %r" % info)
            sign = -1 if expression[position] == '-' else 1
            position += 1
        term = _DIMENSION_TERM.match(expression, position)
        if not term:
            raise ValueError("Invalid dimension: %r" % info)
        number = _finiteNumber(float(term.group(1)), 'dimension') * sign
        unit = term.group(2) or 'px'
        if unit.startswith('%'):
            axis = unit[1:] or 'parent'
            if follow is not None and follow != axis:
                raise ValueError("Dimension percentages must use the same reference axis")
            follow = axis
            relative += number / 100.0
        else:
            absolute += number
        position = term.end()
    if not expression:
        raise ValueError("Dimension cannot be empty")
    _finiteNumber(absolute, 'dimension')
    _finiteNumber(relative, 'dimension')
    return {"absoluteValue": absolute, "relativeValue": relative, "followType": follow or 'parent'}


def validateDropdownItems(items):
    """Dropdown options are static labels and values, never Observable bindings."""
    if not isinstance(items, list):
        raise TypeError('dropdown items must be a list of static options')
    result = []
    for item in items:
        if not isinstance(item, dict) or 'label' not in item or 'value' not in item:
            raise TypeError('dropdown options require label and value')
        if not isinstance(item['label'], str):
            raise TypeError('dropdown option label must be a string; Observable is not supported')
        if isinstance(item['value'], bool) or not isinstance(item['value'], (int, str)):
            raise TypeError('dropdown option value must be an int or string; Observable is not supported')
        result.append({'label': item['label'], 'value': item['value']})
    return result


def getFontScale(value):
    if isinstance(value, str) and value == 'default':
        return 1.0
    scale = _finiteNumber(value, 'fontSize')
    if scale < 0:
        raise ValueError('fontSize must be nonnegative')
    return scale


def validateListViewItems(items):
    """ListView rows have stable, unique string/integer keys and plain labels."""
    try:
        strings, integers = (basestring,), (int, long)
    except NameError:
        strings, integers = (str,), (int,)
    if not isinstance(items, list):
        raise TypeError('listview items must be a list')
    result, keys = [], set()
    for item in items:
        if not isinstance(item, dict) or set(item) != set(('label', 'value')):
            raise ValueError('listview items require exactly label and value')
        key = item['value']
        if not isinstance(item['label'], strings):
            raise TypeError('listview label must be a string')
        if isinstance(key, bool) or not isinstance(key, strings + integers):
            raise TypeError('listview value must be an integer or string')
        if key in keys:
            raise ValueError('listview item values must be unique')
        keys.add(key)
        result.append(dict(item))
    return result


def validateListViewHeight(value):
    value = _finiteNumber(value, 'listview itemHeight')
    if value <= 0:
        raise ValueError('listview itemHeight must be positive')
    return value


def getStepedValue(v, minV, maxV, step):
    """Clamp and quantize; zero step is continuous, reversed bounds are sorted."""
    v = _finiteNumber(v, 'slider value')
    low, high = sorted((_finiteNumber(minV, 'slider minimum'),
                        _finiteNumber(maxV, 'slider maximum')))
    step = abs(_finiteNumber(step, 'slider step'))
    v = max(low, min(v, high))
    if step == 0 or low == high:
        return v
    count = (high - low) / step
    _finiteNumber(count, 'slider step count')
    # Avoid dropping the last step for ranges such as 0..0.3 with step 0.1.
    tolerance = min(1e-7, 1e-12 * max(1.0, abs(count)))
    last = math.floor(count + tolerance)
    ticks = min(last, max(0, round((v - low) / step)))
    return max(low, min(high, low + ticks * step))

def getSliderPercentage(v, minV, maxV, step):
    v = getStepedValue(v, minV, maxV, step)
    low, high = sorted((float(minV), float(maxV)))
    return (v - low) / (high - low) if high != low else 0.0

def getSliderValue(percentage, minV, maxV, step):
    percentage = max(0.0, min(1.0, _finiteNumber(percentage, 'slider percentage')))
    low, high = sorted((_finiteNumber(minV, 'slider minimum'),
                        _finiteNumber(maxV, 'slider maximum')))
    return getStepedValue(low + percentage * (high - low), low, high, step)
