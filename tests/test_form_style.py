# -*- coding: utf-8 -*-
"""Unified FormStyle transport and UI behavior without the game runtime."""
import importlib.util
import sys
import types
import unittest
import test_form_state as fixture
import test_observable_updates as paths


class FakeControl:
    def __init__(self):
        self.visible = True
        self.layer = None

    def GetFullSize(self, axis):
        return {'relativeValue': 1.0, 'absoluteValue': 0, 'followType': 'parent'}

    GetFullPosition = GetFullSize

    def GetChildByPath(self, path):
        return None

    def GetSize(self):
        return (100, 20)

    def GetPosition(self):
        return (0, 0)

    def SetVisible(self, value):
        self.visible = value

    def SetLayer(self, value):
        self.layer = value


class FakeScreenNode:
    def __init__(self, namespace, name, params):
        self.nodes = {'/panel': FakeControl()}

    def GetBaseUIControl(self, path):
        return self.nodes.get(path)

    def CreateChildControl(self, path, name, parent):
        control = FakeControl()
        self.nodes['/panel/' + name] = control
        return control

    def RemoveChildControl(self, control):
        for path, candidate in tuple(self.nodes.items()):
            if candidate is control:
                del self.nodes[path]


class FakeTimers:
    def __init__(self):
        self.queue = []
        self.next_id = 0

    def AddTimer(self, interval, callback, *args):
        self.next_id += 1
        self.queue.append((callback, args))
        return self.next_id

    AddRepeatedTimer = AddTimer

    def CancelTimer(self, timer_id):
        pass

    def drain(self):
        while self.queue:
            callback, args = self.queue.pop(0)
            callback(*args)


class FormStyleTests(unittest.TestCase):
    load_environment = fixture.FormStateTests.load_environment
    get_players = fixture.FormStateTests.get_players
    emit = fixture.FormStateTests.emit
    tearDown = fixture.FormStateTests.tearDown

    def setUp(self):
        fixture.FormStateTests.setUp(self)
        prefix = self.observable_class.__module__.split('.general')[0]
        self.payloads = []
        self.system.NotifyToClient = lambda target, event, data: self.payloads.append(data)
        self.system.NotifyToMultiClients = lambda targets, event, data: self.payloads.append(data)
        self.system.showForm = lambda data: self.payloads.append(data)
        self.system.NotifyToServer = lambda event, data: self.emit(event, data)
        self.system.BroadcastEvent = lambda event, data: self.emit(event, data)
        root_class = types.SimpleNamespace(path='root.path', options={
            'scrollingPanelPath': '/content', 'closeBtnPath': '/close', 'titlePath': '/title',
        })
        self.system.controlManager = types.SimpleNamespace(get=lambda name: root_class)
        self.system._registerFormScreen = lambda screen: None
        self.timers = FakeTimers()
        engine = sys.modules['mod.client.extraClientApi']
        engine.GetScreenNodeCls = lambda: FakeScreenNode
        engine.GetEngineCompFactory = lambda: types.SimpleNamespace(CreateGame=lambda level: self.timers)
        engine.GetLevelId = lambda: 'level'
        engine.PopScreen = lambda: None
        for suffix in ('.general.enums', '.client', '.client.ui'):
            module = types.ModuleType(prefix + suffix)
            module.__path__ = []
            sys.modules[module.__name__] = module
            self.modules.append(module.__name__)

        def load(suffix, relative):
            name = prefix + suffix
            spec = importlib.util.spec_from_file_location(name, paths.CORE / relative)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.modules.append(name)
            spec.loader.exec_module(module)
            return module

        load('.general.enums.controlType', 'general/enums/controlType.py')
        load('.utils.ui', 'utils/ui.py')
        self.screen_class = load('.client.ui.screen', 'client/ui/screen.py').Screen
        self.ui = self.screen_class('test', 'screen', {})
        self.sizes = []
        self.offsets = []
        self.ui.setSize = lambda form, index, axis, data, control=None: self.sizes.append((index, axis, data))
        self.ui.setOffset = lambda form, index, axis, data, control=None: self.offsets.append((index, axis, data))
        self.ui.setFormTitle = lambda *args: None
        self.ui.setFormContent = lambda *args: None
        self.system.applyObservableUpdate = lambda data: self.ui.applyObservableUpdate(data['id'], data['value'])
        self.system.BroadcastToAllClient = lambda event, data: self.system.applyObservableUpdate(data)

    def make_form(self, **style):
        config = {'class': 'root'}
        config.update(style)
        return self.system.formManager.create('style test', config)

    def add(self, form):
        form.show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        self.timers.drain()
        return data['formId']['value'], data

    def root(self, form_id):
        return self.ui.GetBaseUIControl('/panel/fm%s' % form_id)

    def close_ui(self, form_id):
        self.ui.onClose({'AddTouchEventParams': {'formId': form_id}})

    def test_defaults_and_transport_have_one_style_dictionary(self):
        form = self.make_form()
        form.show('p1')
        data = self.payloads[-1]
        self.assertNotIn('options', data)
        style = data['style']
        self.assertEqual(style['layer']['value'], 0)
        self.assertTrue(style['visible']['value'])
        self.assertFalse(style['hideOtherForms']['value'])
        self.assertEqual([entry['value'] for entry in style['grids']], [1])
        self.assertNotIn('columns', style)
        self.assertNotIn('closeAll', style)

    def test_show_no_longer_accepts_options(self):
        with self.assertRaises(TypeError):
            self.make_form().show('p1', options={'layer': 3})
        self.assertEqual(self.listeners, [])

    def test_creation_style_is_applied_to_initial_ui(self):
        form_id, data = self.add(self.make_form(layer=7, visible=False, grids=[1, 3]))
        self.assertEqual(self.root(form_id).layer, 7)
        self.assertFalse(self.root(form_id).visible)
        self.assertEqual([entry['value'] for entry in data['style']['grids']], [1, 3])

    def test_default_styles_and_explicit_style_share_the_same_fields(self):
        def defaults(kind, fallback):
            fallback.update({'layer': 4, 'visible': False, 'hideOtherForms': True, 'grids': [2, 1]})
            return fallback
        self.system.screen.getDefaultStyle = defaults
        form = self.make_form(layer=8, visible=True)
        form.show('p1')
        style = self.payloads[-1]['style']
        self.assertEqual(style['layer']['value'], 8)
        self.assertTrue(style['visible']['value'])
        self.assertTrue(style['hideOtherForms']['value'])
        self.assertEqual([entry['value'] for entry in style['grids']], [2, 1])

    def test_initial_hide_and_close_restore_using_style_visibility(self):
        first, _ = self.add(self.make_form())
        hidden, _ = self.add(self.make_form(visible=False))
        overlay, _ = self.add(self.make_form(hideOtherForms=True))
        self.assertFalse(self.root(first).visible)
        self.assertFalse(self.root(hidden).visible)
        self.assertTrue(self.root(overlay).visible)
        self.close_ui(overlay)
        self.assertTrue(self.root(first).visible)
        self.assertFalse(self.root(hidden).visible)

    def test_closing_latest_overlay_preserves_previous_overlay_hiding(self):
        first, _ = self.add(self.make_form())
        second, _ = self.add(self.make_form(hideOtherForms=True))
        third, _ = self.add(self.make_form(hideOtherForms=True))
        self.close_ui(third)
        self.assertTrue(self.root(second).visible)
        self.assertFalse(self.root(first).visible)
        self.close_ui(second)
        self.assertTrue(self.root(first).visible)

    def test_invisible_overlay_does_not_hide_other_forms(self):
        first, _ = self.add(self.make_form())
        overlay, _ = self.add(self.make_form(visible=False, hideOtherForms=True))
        self.assertTrue(self.root(first).visible)
        self.assertFalse(self.root(overlay).visible)

    def test_layer_observable_updates_ui_and_cached_style(self):
        layer = self.system.observableManager.create(2)
        form_id, data = self.add(self.make_form(layer=layer))
        self.assertIn(layer._id, data['observables'])
        layer.setValue(9)
        self.assertEqual(self.root(form_id).layer, 9)
        self.assertEqual(data['style']['layer']['value'], 9)

    def test_visibility_observable_updates_ui_in_both_directions(self):
        visible = self.system.observableManager.create(False)
        form_id, data = self.add(self.make_form(visible=visible))
        self.assertFalse(self.root(form_id).visible)
        visible.setValue(True)
        self.assertTrue(self.root(form_id).visible)
        visible.setValue(False)
        self.assertFalse(self.root(form_id).visible)
        self.assertFalse(data['style']['visible']['value'])

    def test_hide_observable_hides_and_restores_other_forms(self):
        first, _ = self.add(self.make_form())
        hide = self.system.observableManager.create(False)
        overlay, data = self.add(self.make_form(hideOtherForms=hide))
        hide.setValue(True)
        self.assertFalse(self.root(first).visible)
        self.assertTrue(self.root(overlay).visible)
        hide.setValue(False)
        self.assertTrue(self.root(first).visible)
        self.assertFalse(data['style']['hideOtherForms']['value'])

    def test_overlay_visibility_observable_restores_and_rehides_others(self):
        first, _ = self.add(self.make_form())
        visible = self.system.observableManager.create(True)
        overlay, _ = self.add(self.make_form(visible=visible, hideOtherForms=True))
        visible.setValue(False)
        self.assertTrue(self.root(first).visible)
        self.assertFalse(self.root(overlay).visible)
        visible.setValue(True)
        self.assertFalse(self.root(first).visible)
        self.assertTrue(self.root(overlay).visible)

    def test_shared_visibility_observable_updates_all_forms(self):
        visible = self.system.observableManager.create(True)
        first, _ = self.add(self.make_form(visible=visible))
        second, _ = self.add(self.make_form(visible=visible))
        visible.setValue(False)
        self.assertFalse(self.root(first).visible)
        self.assertFalse(self.root(second).visible)
        visible.setValue(True)
        self.assertTrue(self.root(first).visible)
        self.assertTrue(self.root(second).visible)

    def test_grids_control_relative_column_width_and_offset(self):
        form_id, data = self.add(self.make_form(grids=[1, 3]))
        wrapper = sys.modules[self.observable_class.__module__.split('.general')[0] + '.utils.type']
        control_data = wrapper.wrapDict({'style': {'width': '100%', 'height': '20px', 'offsetX': 0, 'offsetY': 0, 'visible': True}}, [])
        for index in (0, 1):
            self.ui.setControlLayout(form_id, control_data, FakeControl(), data['style'], index, 0)
        widths = [value['relativeValue'] for index, axis, value in self.sizes if index >= 0 and axis == 'x']
        offsets = [value['relativeValue'] for index, axis, value in self.offsets if index >= 0 and axis == 'x']
        self.assertEqual(widths, [0.25, 0.75])
        self.assertEqual(offsets, [0, 0.25])

    def test_client_creation_style_survives_show(self):
        self.server_side = False
        form = self.make_form(layer=3, visible=False, hideOtherForms=True)
        form.show()
        style = self.payloads[-1]['style']
        self.assertEqual(style['layer']['value'], 3)
        self.assertFalse(style['visible']['value'])
        self.assertTrue(style['hideOtherForms']['value'])
        self.assertNotIn('options', self.payloads[-1])


if __name__ == '__main__':
    unittest.main()
