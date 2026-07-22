# -*- coding: utf-8 -*-

def wrapVariable(value, record=[]):
    # type: (any, list) -> dict
    typeId = value.__class__.__name__
    data = {
        "type": typeId,
        "value": value.getValue() if typeId == "Observable" else value,
        "obId": value._id if typeId == "Observable" else -1
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