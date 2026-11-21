# -*- coding: utf-8 -*-
from ...utils.bindings import FormBindings


class BindingMixin(object):
    def _resetBindings(self):
        self._formBindings = {}
        self._observableForms = {}

    def _forgetFormBindings(self, formId):
        old = self._formBindings.pop(formId, None)
        if old is not None:
            for obId in old.byId:
                forms = self._observableForms[obId]
                forms.discard(formId)
                if not forms:
                    del self._observableForms[obId]
        self.observables = list(self._observableForms)

    def _refreshFormBindings(self, formId):
        self._forgetFormBindings(formId)
        index = FormBindings(self.forms[formId])
        self._formBindings[formId] = index
        for obId in index.byId:
            self._observableForms.setdefault(obId, set()).add(formId)
        self.forms[formId]['observables'] = list(index.byId)
        self.observables = list(self._observableForms)
        return index

    def _getFormBindings(self, formId):
        index = self._formBindings.get(formId)
        return index if index is not None else self._refreshFormBindings(formId)
