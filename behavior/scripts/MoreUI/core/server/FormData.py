# -*- coding: utf-8 -*-
from copy import deepcopy
import mod.server.extraServerApi as serverApi
import types
from ..config_server import *

Observables = []
CustomForms = {} # type: dict[int, dict[str, list]]
BarForms = {}
SidebarForms = {}

def getSystem():
    system = serverApi.GetSystem(NamespaceServer, SystemNameServer)
    if system:
        return system
    raise Exception("MoreUI运行时错误！未知原因导致无法获取服务端系统！")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def resolve(value):
    """Return the underlying value of an Observable, or the value unchanged."""
    return value.getData() if hasattr(value, "getData") else value

def _type_name(value):
    """Readable type name, rendering Observables as ``Observable<inner>``."""
    if hasattr(value, "getData"):
        return "Observable<%s>" % type(value.getData()).__name__
    return type(value).__name__

def register_obs(store, formId, *values):
    """Record the id of every Observable in ``values`` against a form."""
    bucket = store[formId]['obs']
    for value in values:
        if isinstance(value, Observable):
            bucket.append(value._id)

def _normalize_options(options, where, defaults):
    """Validate ``options`` is a dict and return a copy with ``defaults`` filled in."""
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise Exception("%s! Expected options of type dict, but got %s" % (where, type(options).__name__))
    options = dict(options)
    for key in defaults:
        if key not in options:
            options[key] = defaults[key]
    return options

def _require_text(value, where):
    """``value`` must be a str or an Observable wrapping a str."""
    if not isinstance(resolve(value), str):
        raise Exception("%s! Expected type str | Observable<str>, but got %s" % (where, _type_name(value)))

def _require_int(value, where):
    """``value`` must be an int or an Observable wrapping an int."""
    if not isinstance(resolve(value), int):
        raise Exception("%s! Expected type int | Observable<int>, but got %s" % (where, _type_name(value)))

def _require_writable_observable(value, inner_types, type_label, noun, where):
    """``value`` must be a client-writable Observable wrapping one of ``inner_types``."""
    if not isinstance(value, Observable):
        raise Exception("%s! Expected type Observable<%s>, but got %s" % (where, type_label, type(value).__name__))
    if not value._options['clientWritable']:
        raise Exception("Excepted %s observable to be client writable." % noun)
    if type(value.getData()) not in inner_types:
        raise Exception(
            "%s! Expected type Observable<%s>, but got Observable<%s>" % (where, type_label, type(value.getData()).__name__)
        )


class Observable:
    """
    A class that represents data that can be Observed. Extensively used for UI.
    """
    ID = 0

    def __init__(self, data, options):
        if not isinstance(options, dict):
            raise TypeError("Create observable failed! Options should be a dict, but got %s" % type(options).__name__)
        if type(data) not in (int, float, str, bool):
            raise TypeError(
                "Create observable failed! Expected type int | float | str | bool, but got %s" % type(data).__name__
            )
        options = dict(options)
        options.setdefault('clientWritable', False)

        self.__data = data
        self.__callbacks = []
        self._options = options
        self._id = Observable.ID
        Observable.ID += 1

        if options['clientWritable']:
            getSystem().ListenForEvent(NamespaceClient, SystemNameClient, "updateObservable%s" % self._id, self, self._update)

    @property
    def typeId(self):
        return type(self.__data)

    def _update(self, data):
        self.setData(data['value'], True)

    def getData(self):
        return self.__data

    def setData(self, data, bit=False):
        # Inner type conversion.
        if data == self.__data:
            return
        if type(self.__data) == str:
            data = str(data)
        elif type(self.__data) == bool:
            data = bool(data)
        if type(data) == int and type(self.__data) == float:
            data = float(data)
        if type(data) == float and type(self.__data) == int:
            data = int(data)
        # Set data or throw error.
        if type(data) != type(self.__data):
            raise TypeError(
                "Observable expected data of type %s, but got %s" % (type(self.__data).__name__, type(data).__name__)
            )
        self.__data = data
        for callback in self.__callbacks:
            callback(self.__data)
        if not bit:
            return
        for formId in CustomForms:
            if self._id in CustomForms[formId]['obs']:
                updateForm(CustomForms[formId]['form'])

    def subscribe(self, callback):
        # type: (types.FunctionType) -> None
        if callback not in self.__callbacks:
            self.__callbacks.append(callback)

    def unsubscribe(self, callback):
        # type: (types.FunctionType) -> None
        if callback in self.__callbacks:
            self.__callbacks.remove(callback)

    @staticmethod
    def create(data, options={"clientWritable": False}):
        ob = Observable(data, options)
        Observables.append(ob)
        return ob


# Control type -> (observable fields to resolve, plain fields to copy verbatim).
# Drives the serialization in updateForm so every control stays in one table.
_CONTROL_RESOLVE_FIELDS = {
    "button": ["label"],
    "label": ["text"],
    "textField": ["label", "text"],
    "toggle": ["label", "toggled"],
    "slider": ["label", "value", "minValue", "maxValue"],
    "dropdown": ["label", "value"],
}
_CONTROL_PLAIN_FIELDS = {
    "textField": ["clientWritable", "textId"],
    "toggle": ["clientWritable", "toggledId"],
    "slider": ["clientWritable", "valueId"],
    "dropdown": ["items", "clientWritable", "valueId"],
}
# Form option keys that may hold Observables and must be resolved before sending.
_FORM_OPTION_KEYS = [
    "resizable", "movable", "closable", "pos", "size",
    "offset", "margin", "direction", "layer", "mayCloseAll",
]


def updateForm(form, mode="update", options={}):
    # type: (CustomForm, str, dict) -> None
    if mode == 'sendMore':
        getSystem().NotifyToClient(
            form,
            "sendMoreCustomForm",
            {
                "row": options['row'],
                "column": options['column']
            }
        )
        return

    if not options:
        options = deepcopy(form._options)
    for key in _FORM_OPTION_KEYS:
        if key not in options:
            continue
        if isinstance(options[key], (list, tuple)):
            for i in range(len(options[key])):
                options[key][i] = resolve(form._options[key][i])
        else:
            options[key] = resolve(options[key])

    data = []
    for control in form._data:
        ctype = control['type']
        temp = {"type": ctype}
        for field in _CONTROL_RESOLVE_FIELDS.get(ctype, []):
            temp[field] = resolve(control[field])
        for field in _CONTROL_PLAIN_FIELDS.get(ctype, []):
            temp[field] = control[field]
        if ctype == 'label':
            temp['text'] = str(temp['text'])
        temp['visible'] = resolve(control['visible'])
        data.append(temp)

    getSystem().NotifyToClient(
        form._playerId,
        "%sCustomForm" % mode,
        {
            "formId": form._formId,
            "title": resolve(form._title),
            "data": data,
            "options": options
        }
    )

class DynamicForm:
    """Base class of dynamic forms (CustomForm, MessageForm)."""
    pass


class CustomForm(DynamicForm):
    """
    A customizable form that lets you put buttons, labels, toggles, dropdowns, sliders, and more into a form!
    Built on top of Observable, the form will update when the Observables' value changes.
    """
    ID = 0

    def __init__(self, playerId, title, options=None):
        # type: (str, str | Observable, dict) -> None
        if not isinstance(playerId, str):
            raise Exception("Create custom form failed! arg 0 excepted type str")
        _require_text(title, "Create custom form failed")
        options = _normalize_options(options, "Custom form create failed", {
            "resizable": False,
            "movable": False,
            "style": "oreui",
            "closable": True,
        })
        # Set data.
        self._playerId = playerId
        self._title = title
        self._data = []
        self._options = options
        self._formId = CustomForm.ID
        CustomForm.ID += 1
        CustomForms[self._formId] = {"form": self, "obs": []}
        register_obs(CustomForms, self._formId, title, options['resizable'], options['movable'], options['closable'])
        getSystem().ListenForEvent(NamespaceClient, SystemNameClient, "updateForm%s" % self._formId, self, self._update)

    @property
    def formId(self):
        return self._formId

    def _update(self, data):
        selection = data['selection']
        index = 0
        selected = None
        for controlData in self._data:
            if not controlData['visible']:
                continue
            if index == selection:
                selected = controlData
                break
            index += 1
        if data['operation'] == 'buttonClick' and selected is not None and 'callback' in selected:
            selected['callback']()
            updateForm(self)

    def button(self, label, onClick, options=None):
        # type: (str | Observable, types.FunctionType, dict) -> CustomForm
        _require_text(label, "CustomForm create button failed")
        options = _normalize_options(options, "CustomForm create button failed", {"visible": True})
        self._data.append({
            "type": "button",
            "label": label,
            "callback": onClick,
            "visible": options['visible'],
        })
        register_obs(CustomForms, self._formId, label, options['visible'])
        updateForm(self)
        return self

    def close(self):
        getSystem().NotifyToClient(self._playerId, "closeCustomForm", {"formId": self._formId})
        return self

    def divider(self, options=None):
        # type: (dict) -> CustomForm
        options = _normalize_options(options, "CustomForm create divider failed", {"visible": True})
        self._data.append({"type": "divider", "visible": options['visible']})
        register_obs(CustomForms, self._formId, options['visible'])
        updateForm(self)
        return self

    def dropdown(self, label, value, items, options=None):
        # type: (str | Observable, Observable, list, dict) -> CustomForm
        _require_text(label, "CustomForm create dropdown failed")
        _require_writable_observable(value, (int, float), "int", "value", "CustomForm create dropdown failed")
        options = _normalize_options(options, "CustomForm create dropdown failed", {"visible": True})
        self._data.append({
            "type": "dropdown",
            "label": label,
            "value": value,
            "items": items,
            "clientWritable": value._options['clientWritable'],
            "visible": options['visible'],
            "valueId": value._id,
        })
        register_obs(CustomForms, self._formId, label, value, options['visible'])
        updateForm(self)
        return self

    def label(self, text, options=None):
        # type: (str | Observable, dict) -> CustomForm
        _require_text(text, "CustomForm create label failed")
        options = _normalize_options(options, "CustomForm create label failed", {"visible": True})
        self._data.append({"type": "label", "text": text, "visible": options['visible']})
        register_obs(CustomForms, self._formId, text, options['visible'])
        updateForm(self)
        return self

    def show(self):
        updateForm(self, "send")
        return self

    def slider(self, label, value, minValue, maxValue, options=None):
        # type: (str | Observable, Observable, int | Observable, int | Observable, dict) -> CustomForm
        _require_text(label, "CustomForm create slider failed")
        _require_writable_observable(value, (int, float), "int", "value", "CustomForm create slider failed")
        _require_int(minValue, "CustomForm create slider failed")
        _require_int(maxValue, "CustomForm create slider failed")
        options = _normalize_options(options, "CustomForm create slider failed", {"visible": True})
        self._data.append({
            "type": "slider",
            "label": label,
            "value": value,
            "minValue": minValue,
            "maxValue": maxValue,
            "clientWritable": value._options['clientWritable'],
            "visible": options['visible'],
            "valueId": value._id,
        })
        register_obs(CustomForms, self._formId, label, value, minValue, maxValue, options['visible'])
        updateForm(self)
        return self

    def spacer(self, options=None):
        return self.label("", options)

    def textField(self, label, text, options=None):
        # type: (str | Observable, Observable, dict) -> CustomForm
        _require_text(label, "CustomForm create textField failed")
        _require_writable_observable(text, (str,), "str", "text", "CustomForm create textField failed")
        options = _normalize_options(options, "CustomForm create textField failed", {"visible": True})
        self._data.append({
            "type": "textField",
            "label": label,
            "text": text,
            "clientWritable": text._options['clientWritable'],
            "textId": text._id,
            "visible": options['visible'],
        })
        register_obs(CustomForms, self._formId, label, text, options['visible'])
        updateForm(self)
        return self

    def toggle(self, label, toggled, options=None):
        # type: (str | Observable, Observable, dict) -> CustomForm
        _require_text(label, "CustomForm create toggle failed")
        _require_writable_observable(toggled, (bool,), "bool", "toggled", "CustomForm create toggle failed")
        options = _normalize_options(options, "CustomForm create toggle failed", {"visible": True})
        self._data.append({
            "type": "toggle",
            "label": label,
            "toggled": toggled,
            "clientWritable": toggled._options['clientWritable'],
            "visible": options['visible'],
            "toggledId": toggled._id,
        })
        register_obs(CustomForms, self._formId, label, toggled, options['visible'])
        updateForm(self)
        return self

    def custom(self, identifier, params):
        # type: (str, dict) -> CustomForm
        """增加一个自定义控件。"""
        pass

    @staticmethod
    def create(playerId, title, options={"resizable": False, "movable": False, "style": "oreui", "closable": True}):
        # type: (str, str | Observable, dict) -> CustomForm
        return CustomForm(playerId, title, options)


class MessageForm(DynamicForm):

    def __init__(self, playerId, title):
        pass


class BarForm(DynamicForm):

    def __init__(self, playerId, title, options=None):
        if not isinstance(playerId, str):
            raise Exception("Create bar form failed! arg 0 excepted type str")
        _require_text(title, "Create bar form failed")
        options = _normalize_options(options, "Bar form create failed", {
            "resizable": False,
            "movable": False,
            "style": "oreui",
            "closable": False,
            "direction": "vertical",
        })
        # Set data.
        self._playerId = playerId
        self._title = title
        self._data = []
        self._options = options
        self._formId = CustomForm.ID
        CustomForm.ID += 1
        BarForms[self._formId] = {"form": self, "obs": []}
        register_obs(BarForms, self._formId, title, options['resizable'], options['movable'], options['closable'])
        getSystem().ListenForEvent(NamespaceClient, SystemNameClient, "updateBarForm%s" % self._formId, self, self._update)

    @property
    def formId(self):
        return self._formId

    def _update(self, data):
        selection = data['selection']
        self._data[selection]['callback']()

    @staticmethod
    def create(playerId, title, options=None):
        return BarForm(playerId, title, options)

    def button(self, label, onClick, options=None):
        _require_text(label, "BarForm create button failed")
        options = _normalize_options(options, "BarForm create button failed", {"visible": True})
        self._data.append({
            "type": "button",
            "label": label,
            "callback": onClick,
            "visible": options['visible'],
        })
        register_obs(BarForms, self._formId, label, options['visible'])
        updateForm(self)
        return self

    def close(self):
        getSystem().NotifyToClient(self._playerId, "closeCustomForm", {"formId": self._formId})
        return self

    def show(self):
        updateForm(self, "send")
        return self


class SidebarForm(DynamicForm):
    """
    A form with a vertical strip of square icon tabs down the left side. Each tab is bound
    to its own CustomForm, which is shown in the main area on the right when the tab is
    clicked. The content forms are ordinary CustomForms, rendered through the same combine
    pipeline as MoreUI, so every existing control type works inside a tab.
    """
    ID = 0

    def __init__(self, playerId, options=None):
        # type: (str, dict) -> None
        if not isinstance(playerId, str):
            raise Exception("Create sidebar form failed! arg 0 excepted type str")
        options = _normalize_options(options, "Sidebar form create failed", {
            "movable": False,
            "resizable": False,
            "closable": True,
            "style": "oreui",
        })
        self._playerId = playerId
        self._options = options
        self._tabs = []  # list of {"iconPath": str, "form": CustomForm, "callback": fn}
        self._formId = SidebarForm.ID
        SidebarForm.ID += 1
        SidebarForms[self._formId] = {"form": self, "obs": []}
        getSystem().ListenForEvent(NamespaceClient, SystemNameClient, "updateSidebarForm%s" % self._formId, self, self._update)

    @property
    def formId(self):
        return self._formId

    @staticmethod
    def create(playerId, options=None):
        # type: (str, dict) -> SidebarForm
        return SidebarForm(playerId, options)

    def tab(self, iconPath, form, options=None):
        # type: (str, CustomForm, dict) -> SidebarForm
        if not isinstance(iconPath, str):
            raise Exception("SidebarForm create tab failed! arg 0 expected type str, but got %s" % type(iconPath).__name__)
        if not isinstance(form, CustomForm):
            raise Exception("SidebarForm create tab failed! arg 1 expected type CustomForm, but got %s" % type(form).__name__)
        _normalize_options(options, "SidebarForm create tab failed", {})
        this = self

        def onClick():
            for tab in this._tabs:
                tab['form'].close()
            form.show()

        self._tabs.append({"iconPath": iconPath, "form": form, "callback": onClick})
        return self

    def _update(self, data):
        selection = data['selection']
        if 0 <= selection < len(self._tabs):
            self._tabs[selection]['callback']()

    def show(self):
        options = dict(self._options)
        for key in _FORM_OPTION_KEYS:
            if key in options:
                options[key] = resolve(options[key])
        getSystem().NotifyToClient(self._playerId, "sendSidebarForm", {
            "formId": self._formId,
            "tabs": [tab['iconPath'] for tab in self._tabs],
            "formIds": [tab['form']._formId for tab in self._tabs],
            "options": options,
        })
        # Render every tab's content form into the sidebar screen. The client combine is
        # deferred (timer), so it can't reliably react to a hide/show sent for a not-yet
        # created form; the client decides initial visibility (first tab only) per combine.
        for tab in self._tabs:
            updateForm(tab['form'], "combine")
        return self

    def close(self):
        getSystem().NotifyToClient(self._playerId, "closeSidebarForm", {"formId": self._formId})
        return self


class FormLayout:

    def __init__(self, layout={}):
        self.__position = layout.get("position", [0, 0])
        self.__offset = layout.get("offset", [0, 0])
        self.__size = layout.get("size", [1, 1])
        self.__margin = layout.get("margin", [0, 0, 0, 0])
        self.__layer = layout.get("layer", 0)

    @property
    def position(self):
        return self.__position

    @position.setter
    def position(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                if isinstance(value[0], (int, Observable)) and isinstance(value[1], (int, Observable)):
                    self.__position = [value[0], value[1]]
                else:
                    raise Exception("Set position failed! Elements must be int.")
            else:
                raise Exception("Set position failed! Position must has at least 2 elements.")
        else:
            raise Exception("Set position failed! Position must be a tuple or a list.")

    @property
    def offset(self):
        return self.__offset

    @offset.setter
    def offset(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                if isinstance(value[0], (int, float, Observable)) and isinstance(value[1], (int, float, Observable)):
                    self.__offset = [value[0], value[1]]
                else:
                    raise Exception("Set offset failed! Elements must be float.")
            else:
                raise Exception("Set offset failed! Offset must has at least 2 elements.")
        else:
            raise Exception("Set offset failed! Offset must be a tuple or a list.")

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                if isinstance(value[0], (int, Observable)) and isinstance(value[1], (int, Observable)):
                    self.__size = [value[0], value[1]]
                else:
                    raise Exception("Set size failed! Elements must be int.")
            else:
                raise Exception("Set size failed! Size must has at least 2 elements.")
        else:
            raise Exception("Set size failed! Size must be a tuple or a list.")

    @property
    def margin(self):
        return self.__margin

    @margin.setter
    def margin(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 3:
                if isinstance(value[0], (int, float, Observable)) and isinstance(value[1], (int, float, Observable)):
                    self.__margin = [value[0], value[1]]
                else:
                    raise Exception("Set margin failed! Elements must be float.")
            else:
                raise Exception("Set margin failed! Margin must has at least 2 elements.")
        else:
            raise Exception("Set margin failed! Margin must be a tuple or a list.")

    @property
    def layer(self):
        return self.__layer

    @layer.setter
    def layer(self, value):
        if isinstance(value, (int, Observable)):
            self.__layer = value
        else:
            raise Exception("Set layer failed! Layer must be an int.")


class _MoreUIFormData:
    """Holds a form together with its layout inside a MoreUI."""

    def __init__(self, form, layout):
        # type: (DynamicForm, FormLayout) -> None
        self.__form = form
        self.__layout = layout
        self.__mayCloseAll = Observable.create(False)

    @property
    def form(self):
        return self.__form

    @property
    def layout(self):
        return self.__layout

    @property
    def mayCloseAll(self):
        return self.__mayCloseAll

    @mayCloseAll.setter
    def mayCloseAll(self, value):
        self.__mayCloseAll.setData(value)


class MoreUICustomData(_MoreUIFormData):
    pass


class MoreUIBarData(_MoreUIFormData):
    pass


class MoreUILayout:
    """
    Layout.
    """

    def __init__(self, layout={}):
        self.__row = layout.get("row", [1])
        self.__column = layout.get("column", [1])

    @property
    def row(self):
        return self.__row

    @row.setter
    def row(self, value):
        if isinstance(value, (list, tuple)):
            for el in value:
                if not isinstance(el, (float, int, Observable)):
                    raise TypeError("Property row excepted list[int | float], but got list[%s]" % type(el).__name__)
        else:
            raise TypeError("Property row excepted list[int | float], but got %s" % type(value).__name__)
        self.__row = value

    @property
    def column(self):
        return self.__column

    @column.setter
    def column(self, value):
        if isinstance(value, (list, tuple)):
            for el in value:
                if not isinstance(el, (float, int, Observable)):
                    raise TypeError("Property column excepted list[int | float], but got list[%s]" % type(el).__name__)
        else:
            raise TypeError("Property column excepted list[int | float], but got %s" % type(value).__name__)
        self.__column = value


class MoreUI:
    """
    A custom UI consisting of multiple forms.
    """
    _ID = 0

    def __init__(self, playerId, layout={}):
        # type: (str, dict) -> None
        if not isinstance(playerId, str):
            raise Exception("Create MoreUI failed! arg 0 excepted type str.")
        if not isinstance(layout, dict):
            raise Exception("Create MoreUI failed! arg 1 excepted type dict, but got type %s" % layout)
        self.__id = MoreUI._ID
        self.__forms = [] # type: list[MoreUICustomData]
        self.__layout = MoreUILayout(layout)
        self.__playerId = playerId
        MoreUI._ID += 1

    @staticmethod
    def create(playerId, layout={}):
        # type: (str, dict) -> MoreUI
        """
        Create a MoreUI.
        """
        return MoreUI(playerId, layout)

    def __attach(self, form, dataCls, store, layout):
        """Wrap a form in layout data, push its layout into the form options and register it."""
        data = dataCls(form, FormLayout(layout))
        self.__forms.append(data)
        d = form._options
        d['pos'] = data.layout.position
        d['size'] = data.layout.size
        d['offset'] = data.layout.offset
        d['margin'] = data.layout.margin
        d['mayCloseAll'] = data.mayCloseAll
        d['layer'] = data.layout.layer
        for group in (d['pos'], d['size'], d['offset'], d['margin'], [d['layer'], d['mayCloseAll']]):
            register_obs(store, form.formId, *group)
        updateForm(form, "combine")
        return data

    def addCustomForm(self, title, options=None, layout=None):
        if layout is not None and not isinstance(layout, dict):
            raise Exception("Add custom form failed! Arg 2 excepted dict, but got %s" % layout)
        fm = CustomForm.create(self.__playerId, title, options)
        return self.__attach(fm, MoreUICustomData, CustomForms, layout or {})

    def addBarForm(self, title, options=None, layout=None):
        if layout is not None and not isinstance(layout, dict):
            raise Exception("Add bar form failed! Arg 2 excepted dict, but got %s" % layout)
        fm = BarForm.create(self.__playerId, title, options)
        return self.__attach(fm, MoreUIBarData, BarForms, layout or {})

    @property
    def layout(self):
        """
        Layout of this UI.
        """
        return self.__layout

    @layout.setter
    def layout(self, style):
        if isinstance(style, dict):
            style = MoreUILayout(style)
        else:
            raise Exception("Set layout failed! style excepted type dict, but got %s" % type(style).__name__)
        self.__layout = style

    def addForm(self, form, layout=None):
        # type: (DynamicForm, dict) -> MoreUICustomData
        if not isinstance(form, DynamicForm):
            raise Exception("Add form failed! Arg 0 excepted type <DynamicForm>, but got %s" % type(form).__name__)
        if layout is not None and not isinstance(layout, dict):
            raise Exception("Add form failed! Arg 1 excepted type dict, but got %s" % type(layout).__name__)
        if isinstance(form, BarForm):
            store = BarForms
        else:
            store = CustomForms
        return self.__attach(form, MoreUICustomData, store, layout or {})

    def removeForm(self, form):
        self.__forms.remove(form)
        return self

    def show(self):
        # type: () -> None
        layout = {"row": self.layout.row, "column": self.layout.column}
        updateForm(self.__playerId, "sendMore", layout)
        for formData in self.__forms:
            updateForm(formData.form, "combine")

    def close(self):
        getSystem().NotifyToClient(self.__playerId, "closeMoreUI", {"formId": self.__id})
        return self
