# -*- coding: utf-8 -*-
from copy import deepcopy

class CreateArguments(object):

    def __init__(self, screenNode, control, params=None):
        self.__screenNode = screenNode
        self.__control = control
        self.__params = deepcopy(params) if params is not None else {}

    @property
    def screenNode(self):
        return self.__screenNode

    @property
    def control(self):
        return self.__control

    @property
    def params(self):
        """An independent snapshot of custom parameters, with Observable values unwrapped."""
        return self.__params

class FormShowResultArgs:
    def __init__(self, data):
        self.__closeReason = data['closeReason']
        self.__playerId = data['playerId']

    @property
    def closeReason(self):
        return self.__closeReason

    @property
    def playerId(self):
        return self.__playerId

class ObservableUpdateArguments(object):

    def __init__(self, old, new, key, screenNode=None, control=None, params=None):
        self.__old = deepcopy(old)
        self.__new = deepcopy(new)
        self.__key = key
        self.__screenNode = screenNode
        self.__control = control
        self.__params = deepcopy(params) if params is not None else {}

    @property
    def oldValue(self):
        return self.__old

    @property
    def newValue(self):
        return self.__new

    @property
    def key(self):
        return self.__key

    @property
    def screenNode(self):
        return self.__screenNode

    @property
    def control(self):
        return self.__control

    @property
    def params(self):
        """The current parameter snapshot; oldValue/newValue describe this notification."""
        return self.__params

def unwrapWrappedValue(data, previous=None):
    """Read a serialized value tree without exposing its binding metadata."""
    if isinstance(data, dict):
        if isinstance(data.get('type'), str) and 'obId' in data and 'value' in data:
            value = previous[id(data)] if previous is not None and id(data) in previous else data['value']
            return deepcopy(value)
        return {key: unwrapWrappedValue(value, previous) for key, value in data.items()}
    if isinstance(data, list):
        return [unwrapWrappedValue(value, previous) for value in data]
    if isinstance(data, tuple):
        return tuple(unwrapWrappedValue(value, previous) for value in data)
    return deepcopy(data)

def updateWrappedObservable(data, obId, value):
    """Update serialized bindings before touching UI; retain callback old values."""
    previous = {}
    def update(entry):
        if isinstance(entry, dict):
            if entry.get('type') == 'Observable' and entry.get('obId') == obId:
                previous[id(entry)] = entry['value']
                entry['value'] = value
            else:
                for child in entry.values():
                    update(child)
        elif isinstance(entry, (list, tuple)):
            for child in entry:
                update(child)
    update(data)
    return previous

def getCustomObservableUpdates(form, previous, value):
    """Capture parameter notifications while a form is waiting for its controls."""
    updates = []
    def changed(entry):
        if id(entry) in previous:
            return True
        if isinstance(entry, dict):
            return any(changed(child) for child in entry.values())
        if isinstance(entry, (list, tuple)):
            return any(changed(child) for child in entry)
        return False
    from .group import iterControls
    for index, control in iterControls(form.get('controls', [])):
        for key, binding in control.get('params', {}).items():
            if changed(binding):
                updates.append((index, key, unwrapWrappedValue(binding, previous), unwrapWrappedValue(binding)))
    return updates

def wrapVariable(value, record=[]):
    # type: (any, list) -> dict
    typeId = value.__class__.__name__
    data = {
        "type": typeId,
        "value": value.getValue() if typeId == "Observable" else value,
        "obId": value._id if typeId == "Observable" else None
    }
    if typeId == "Observable":
        record.append(value._id)
    return data

def wrapDict(value, record=[]):
    # type: (dict, list) -> dict
    data = {}
    for key in value.keys():
        if isinstance(value[key], dict):
            data[key] = wrapDict(value[key], record)
        elif isinstance(value[key], list):
            data[key] = wrapList(value[key], record)
        else:
            data[key] = wrapVariable(value[key], record)
    return data

def wrapList(value, record=[]):
    # type: (list, list) -> list
    data = []
    for el in value:
        if isinstance(el, dict):
            data.append(wrapDict(el, record))
        elif isinstance(el, list):
            data.append(wrapList(el, record))
        else:
            data.append(wrapVariable(el, record))
    return data
