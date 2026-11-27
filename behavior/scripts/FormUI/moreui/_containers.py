# -*- coding: utf-8 -*-
from ..core.utils.ui import STRING_TYPES
from ._forms import BarForm, CustomForm, sendForms, validatePlayer
from ._layout import FormLayout, MoreUILayout
from ._observable import Observable, current, optionsDict


class MoreUICustomData(object):
    """【已废弃】MoreUI 中的子表单及其布局。"""

    def __init__(self, owner, form, layout, flags=None):
        self._owner = owner
        self._form = form
        self._layout = FormLayout(layout)
        self._flags = flags or {}
        self._mayCloseAll = Observable.create(False)

    @property
    def form(self):
        return self._form

    @property
    def layout(self):
        return self._layout

    @property
    def mayCloseAll(self):
        return self._mayCloseAll

    @mayCloseAll.setter
    def mayCloseAll(self, value):
        self._mayCloseAll.setData(current(value))


class MoreUIBarData(MoreUICustomData):
    """【已废弃】MoreUI 中的按钮栏及其布局。"""


class MoreUI(object):
    """【已废弃】在同一个界面中显示多张旧版表单。"""

    _nextGroup = 0

    def __init__(self, playerId, layout=None):
        validatePlayer(playerId)
        self._playerId = playerId
        self._layout = MoreUILayout(layout)
        self._forms = []
        MoreUI._nextGroup += 1
        self._group = 'moreui:group:%s' % MoreUI._nextGroup

    @staticmethod
    def create(playerId, layout=None):
        return MoreUI(playerId, layout)

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, layout):
        self._layout._replace(layout)

    def _active(self):
        return any(entry.form._isShowing() and not entry.form._closing for entry in self._forms)

    def _attach(self, form, layout=None, flags=None, visible=None):
        if not isinstance(form, (CustomForm, BarForm)):
            raise TypeError('MoreUI.addForm requires a CustomForm or BarForm')
        if form._playerId != self._playerId:
            raise ValueError('The form and the MoreUI must belong to the same player')
        if form._entry is not None:
            raise ValueError('The form already belongs to a MoreUI')
        placementType = MoreUIBarData if isinstance(form, BarForm) else MoreUICustomData
        entry = placementType(self, form, layout, flags)
        active = self._active()
        wasVisible = form._visible.getValue()
        form.close()
        if visible is not None:
            form._visible.setValue(visible)
        form._entry = entry
        self._forms.append(entry)
        try:
            if active:
                form.show()
        except:
            self._forms.remove(entry)
            form._entry = None
            entry.layout._unbindSources()
            if visible is not None:
                form._visible.setValue(wasVisible)
            raise
        return entry

    def addCustomForm(self, title, options=None, layout=None):
        return self.addForm(CustomForm.create(self._playerId, title, options), layout)

    def addBarForm(self, title, options=None, layout=None):
        return self.addForm(BarForm.create(self._playerId, title, options), layout)

    def addForm(self, form, layout=None):
        return self._attach(form, layout)

    def removeForm(self, form):
        entry = form._entry if isinstance(form, (CustomForm, BarForm)) else form
        if entry not in self._forms:
            raise ValueError('The form is not attached to this MoreUI')
        entry.form.close()
        self._forms.remove(entry)
        entry.form._entry = None
        entry.layout._unbindSources()
        return self

    def show(self):
        sendForms(self._playerId, self._group, [entry.form for entry in self._forms])

    def close(self):
        for entry in list(self._forms):
            entry.form.close()
        return self


class _Pages(object):
    def __init__(self, ui, layout, flags=None):
        self._ui = ui
        self._layout = layout
        self._flags = flags
        self.first = None
        self._selected = None

    def add(self, form):
        if not isinstance(form, CustomForm):
            raise TypeError('Menu pages require a MoreUI CustomForm')
        selected = self._selected is None
        self._ui._attach(form, self._layout, self._flags, visible=selected)
        if selected:
            self.first = self._selected = form

    def select(self, form, show=True):
        if form is not self._selected:
            self._selected._visible.setValue(False)
            self._selected = form
            form._visible.setValue(True)
        if show:
            form.show()


class SidebarForm(object):
    """【已废弃】通过左侧图标在多个 CustomForm 之间切换。"""

    def __init__(self, playerId, options=None):
        options = optionsDict(options)
        options.setdefault('closable', True)
        options['direction'] = 'vertical'
        self._ui = MoreUI.create(playerId, {'column': [1, 4]})
        rail = self._ui.addBarForm('', options)
        rail.mayCloseAll = True
        self._rail = rail.form
        self._pages = _Pages(self._ui, {'position': [1, 0]}, {
            'closable': False, 'movable': False, 'resizable': False,
        })

    @property
    def formId(self):
        return self._rail.formId

    @staticmethod
    def create(playerId, options=None):
        return SidebarForm(playerId, options)

    def tab(self, iconPath, form, options=None):
        if not isinstance(iconPath, STRING_TYPES):
            raise TypeError('iconPath must be a string')
        options = optionsDict(options)
        self._pages.add(form)
        self._rail._icon(iconPath, form._visible, lambda: self._pages.select(form), options)
        return self

    def show(self):
        if self._pages.first is not None and not self._ui._active():
            self._pages.select(self._pages.first, show=False)
        self._ui.show()
        return self

    def close(self):
        self._ui.close()
        return self


class ConfigMenu(object):
    """【已废弃】带标题和侧栏的多页设置菜单。"""

    def __init__(self, playerId, title):
        self._ui = MoreUI.create(playerId, {'column': [1, 4], 'row': [1, 10]})
        header = self._ui.addBarForm(title, {'closable': True}, {'size': [2, 1], 'layer': 1})
        header.mayCloseAll = True
        self._sidebar = self._ui.addBarForm('', layout={'position': [0, 1]}).form
        self._pages = _Pages(self._ui, {'position': [1, 1]})
        self._pages.add(CustomForm.create(playerId, '', {'closable': False}))

    @staticmethod
    def create(playerId, title):
        return ConfigMenu(playerId, title)

    def addPage(self, form, tabName=None):
        self._pages.add(form)
        self._sidebar.button(tabName or form._title, lambda: self._pages.select(form))

    def show(self):
        if not self._ui._active():
            self._pages.select(self._pages.first, show=False)
        self._ui.show()

    def close(self):
        self._ui.close()
