# -*- coding: utf-8 -*-
"""A native-control scene for exercising production custom creation and updates."""
import types
from test_grid_layout import GeometryControl, dimension


class Label:
    def __init__(self):
        self.text = ''
        self.font_scale = 1.0

    def asLabel(self):
        return self

    def SetText(self, text):
        self.text = text

    def SetTextFontSize(self, scale):
        self.font_scale = scale


def install_custom_ui(test, on_create=None, on_update=None):
    root = types.SimpleNamespace(typeId='scrolling_panel', path='root.path', options={
        'scrollingPanelPath': '/content', 'closeBtnPath': '/close', 'titlePath': '/title',
    })
    custom = types.SimpleNamespace(typeId='custom', path='custom.path', options={
        'onCreate': on_create, 'onObservableUpdate': on_update,
    })
    test.registry = {'root': root, 'custom': custom, 'oreui:light_panel_thin': root}
    def register(kind, name, path, options):
        control = types.SimpleNamespace(typeId=kind, path=path, options=options)
        test.registry[name] = control
        return control
    test.system.controlManager = types.SimpleNamespace(get=test.registry.get, create=register)
    test.ui.controlManager = test.system.controlManager
    if hasattr(test, 'client'):
        test.client.controlManager = test.system.controlManager
    test.ui.setSize = types.MethodType(test.screen_class.setSize, test.ui)
    test.ui.setOffset = types.MethodType(test.screen_class.setOffset, test.ui)
    test.ui.setFormContent = types.MethodType(test.screen_class.setFormContent, test.ui)
    test.ui.nodes['/panel'] = GeometryControl(height=300)
    test.native_customs = []

    def create(path, name, parent):
        node = GeometryControl(parent)
        node.SetLayer = lambda layer: setattr(node, 'layer', layer)
        if name.startswith('fm'):
            node.size['y'] = dimension(absolute=200)
            scroll = GeometryControl(node)
            scroll.size['y'] = dimension(1)
            content = GeometryControl(scroll)
            scroll.children['/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content'] = content
            node.children['/content'] = scroll
            test.ui.nodes['/panel/' + name] = node
            test.ui.nodes['/panel/' + name + '/content'] = scroll
        else:
            node.children['/label'] = Label()
            parent.children['/' + name] = node
            test.native_customs.append(node)
        return node
    test.ui.CreateChildControl = create
