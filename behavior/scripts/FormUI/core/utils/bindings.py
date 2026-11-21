# -*- coding: utf-8 -*-
"""Dependency indexes rebuilt on structural changes, not on each notification."""
from .group import iterControls, collectObservableIds
from .type import unwrapWrappedValue


class WrappedBindings(object):
    def __init__(self, data):
        self.byId = {}
        seen = set()
        def visit(entry):
            if isinstance(entry, (dict, list, tuple)):
                identity = id(entry)
                if identity in seen:
                    return
                seen.add(identity)
            if isinstance(entry, dict):
                if entry.get('type') == 'Observable' and entry.get('obId') is not None:
                    self.byId.setdefault(entry['obId'], []).append(entry)
                else:
                    for child in entry.values():
                        visit(child)
            elif isinstance(entry, (list, tuple)):
                for child in entry:
                    visit(child)
        visit(data)

    def update(self, obId, value):
        previous = {}
        for entry in self.byId.get(obId, ()):
            previous[id(entry)] = entry['value']
            entry['value'] = value
        return previous


class FormBindings(WrappedBindings):
    def __init__(self, form):
        WrappedBindings.__init__(self, form)
        self.controls = {}
        self.groupStyles = {}
        self.groupGeometryIds = set()
        self.classIds = set()
        self.customParams = {}
        self.itemChanges = {}
        for address, control in iterControls(form.get('controls', [])):
            own = {key: value for key, value in control.items()
                   if key not in ('children', '_groupInput')}
            for obId in collectObservableIds(own):
                self.controls.setdefault(obId, []).append((address, control))
            if 'items' in control:
                for obId in collectObservableIds([control['items'], control.get('style', {}).get('itemHeight')]):
                    self.itemChanges.setdefault(obId, set()).add(address)
            definition = control.get('_groupDefinition', control.get('_groupLayout'))
            if definition is not None:
                ids = collectObservableIds(definition)
                self.groupGeometryIds.update(ids)
                for obId in ids:
                    self.groupStyles.setdefault(obId, []).append((address, control))
                if isinstance(address, tuple):
                    self.classIds.update(collectObservableIds(definition.get('class')))
            if control.get('custom', {}).get('value', True):
                for key, binding in control.get('params', {}).items():
                    for obId in collectObservableIds(binding):
                        self.customParams.setdefault(obId, []).append((address, key, binding))

    def customUpdates(self, obId, previous):
        return [(address, key, unwrapWrappedValue(binding, previous), unwrapWrappedValue(binding))
                for address, key, binding in self.customParams.get(obId, ())]
