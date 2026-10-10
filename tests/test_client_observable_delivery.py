# -*- coding: utf-8 -*-
"""Keep updates while screens are covered or form creation is deferred."""
import gc
import importlib.util
import sys
import types
import unittest
import weakref
import test_form_style as fixture
import test_observable_updates as paths
from custom_ui_fixture import install_custom_ui


class FakeClientSystem:
    def __init__(self, namespace, name):
        pass

    def ListenForEvent(self, *args):
        pass


class ClientObservableDeliveryTests(unittest.TestCase):
    load_environment = fixture.FormStyleTests.load_environment
    get_players = fixture.FormStyleTests.get_players
    emit = fixture.FormStyleTests.emit
    tearDown = fixture.FormStyleTests.tearDown
    make_form = fixture.FormStyleTests.make_form
    add = fixture.FormStyleTests.add
    root = fixture.FormStyleTests.root

    def setUp(self):
        fixture.FormStyleTests.setUp(self)
        prefix = self.observable_class.__module__.split('.general')[0]
        config = sys.modules[prefix + '.config']
        config.SystemNameServer = 'server'
        self.engine = sys.modules['mod.client.extraClientApi']
        self.engine.GetClientSystemCls = lambda: FakeClientSystem
        self.engine.GetEngineNamespace = lambda: 'engine'
        self.engine.GetEngineSystemName = lambda: 'engineClient'
        self.top = self.ui
        self.engine.GetTopScreen = lambda: self.top
        self.pushes = []
        self.engine.PushScreen = lambda *args: self.pushes.append(args)

        def load(suffix, relative):
            name = prefix + suffix
            spec = importlib.util.spec_from_file_location(name, paths.CORE / relative)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.modules.append(name)
            spec.loader.exec_module(module)
            return module

        load('.general.control', 'general/control.py')
        load('.general.managers.control', 'general/managers/control.py')
        load('.general.screen', 'general/screen.py')
        self.client_class = load('.client.system', 'client/system.py').Client
        self.client = self.client_class('test', 'client')
        self.client.controlManager = self.system.controlManager
        environment = sys.modules[prefix + '.utils.environment']
        environment.getClientSystem = lambda: self.client
        self.client._registerFormScreen(self.ui)
        self.system.applyObservableUpdate = self.client.applyObservableUpdate
        self.system.BroadcastToAllClient = lambda event, data: self.client.applyObservableUpdate(data)

    def test_covered_screen_still_receives_updates(self):
        layer = self.system.observableManager.create(1)
        form_id, data = self.add(self.make_form(layer=layer))
        self.top = object()
        layer.setValue(8)
        self.assertEqual(self.root(form_id).layer, 8)
        self.assertEqual(data['style']['layer']['value'], 8)
        self.top = None
        layer.setValue(9)
        self.assertEqual(self.root(form_id).layer, 9)

    def test_multiple_live_screens_receive_updates_once(self):
        second = self.screen_class('test', 'second', {})
        calls = []
        self.ui.applyObservableUpdate = lambda *args: calls.append(('first', args))
        second.applyObservableUpdate = lambda *args: calls.append(('second', args))
        self.top = second
        self.client.applyObservableUpdate({'id': 5, 'value': 20})
        self.assertCountEqual(calls, [('first', (5, 20)), ('second', (5, 20))])

    def test_registry_does_not_keep_unused_screens_alive(self):
        second = self.screen_class('test', 'second', {})
        reference = weakref.ref(second)
        del second
        gc.collect()
        self.assertIsNone(reference())
        self.client.applyObservableUpdate({'id': 50, 'value': 1})

    def test_update_before_controls_exist_is_used_during_creation(self):
        width = self.system.observableManager.create(100)
        visible = self.system.observableManager.create(True)
        form = self.make_form(width=width).button('a', style={'width': width, 'visible': visible})
        form.show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        width.setValue(200)
        visible.setValue(False)
        self.assertEqual(self.sizes, [])
        self.assertEqual(data['style']['width']['value'], 200)
        self.assertEqual(data['controls'][0]['style']['width']['value'], 200)
        self.assertFalse(data['controls'][0]['style']['visible']['value'])
        created = []
        self.ui.setFormContent = lambda form_id, path: created.append(data['controls'][0]['style']['width']['value'])
        self.timers.drain()
        self.assertEqual(created, [200])
        self.assertTrue(any(index == -1 and axis == 'x' and value['absoluteValue'] == 200
                            for index, axis, value in self.sizes))

    def test_ui_failure_does_not_drop_updates_to_other_bound_fields(self):
        width = self.system.observableManager.create(100)
        form_id, data = self.add(self.make_form(width=width).button(width, style={'width': width}))
        def fail(*args):
            raise AttributeError('control unavailable')
        self.ui.setSize = fail
        width.setValue(200)
        self.assertEqual(data['style']['width']['value'], 200)
        self.assertEqual(data['controls'][0]['label']['value'], 200)
        self.assertEqual(data['controls'][0]['style']['width']['value'], 200)

    def test_waiting_to_push_screen_keeps_latest_snapshot(self):
        value = self.system.observableManager.create('old')
        form = self.make_form().button(value)
        form.show('p1')
        data = self.payloads[-1]
        self.top = None
        self.client.showForm(data)
        value.setValue('intermediate')
        value.setValue('latest')
        self.assertEqual(data['controls'][0]['label']['value'], 'latest')
        self.ui.Create()
        self.top = self.ui
        self.timers.drain()
        self.assertIn(data['formId']['value'], self.ui.forms)
        self.assertEqual(data['controls'][0]['label']['value'], 'latest')
        self.assertEqual(len(self.pushes), 1)

    def test_waiting_forms_are_updated_independently(self):
        first = self.system.observableManager.create('first')
        second = self.system.observableManager.create('second')
        self.top = None
        waiting = []
        for observable in (first, second):
            self.make_form().button(observable).show('p1')
            data = self.payloads[-1]
            waiting.append(data)
            self.client.showForm(data)
        second.setValue('changed')
        self.assertEqual(waiting[0]['controls'][0]['label']['value'], 'first')
        self.assertEqual(waiting[1]['controls'][0]['label']['value'], 'changed')

    def test_pending_delivery_failure_does_not_retain_snapshot(self):
        observable = self.system.observableManager.create(1)
        self.make_form().button(observable).show('p1')
        data = self.payloads[-1]
        self.top = None
        def fail(*args):
            raise RuntimeError('push failed')
        self.engine.PushScreen = fail
        with self.assertRaises(RuntimeError):
            self.client.showForm(data)
        observable.setValue(2)
        self.assertEqual(data['controls'][0]['label']['value'], 1)

    def test_cache_first_preserves_custom_callback_old_and_new_values(self):
        value = self.system.observableManager.create(10)
        received = []
        install_custom_ui(self, on_update=lambda args: received.append((args.oldValue, args.newValue, args.key)))
        _, data = self.add(self.make_form().custom({'count': value}, style={'class': 'custom'}))
        value.setValue(20)
        value.setValue(30)
        self.assertEqual(received, [(10, 20, 'count'), (20, 30, 'count')])
        self.assertEqual(data['controls'][0]['params']['count']['value'], 30)

    def capture_custom_creation(self, received):
        install_custom_ui(self, on_create=lambda args: received.append('created'),
                          on_update=lambda args: received.append((args.oldValue, args.newValue, args.key)))

    def test_custom_notifications_wait_for_control_creation_in_order(self):
        value = self.system.observableManager.create(10)
        received = []
        self.capture_custom_creation(received)
        self.make_form().custom({'count': value}, style={'class': 'custom'}).show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        value.setValue(20)
        value.setValue(30)
        self.assertEqual(received, [])
        self.assertEqual(data['controls'][0]['params']['count']['value'], 30)
        self.timers.drain()
        self.assertEqual(received, ['created', (10, 20, 'count'), (20, 30, 'count')])

    def test_custom_notifications_survive_waiting_to_push_screen(self):
        value = self.system.observableManager.create(10)
        received = []
        self.capture_custom_creation(received)
        self.make_form().custom({'count': value}, style={'class': 'custom'}).show('p1')
        data = self.payloads[-1]
        self.top = None
        self.client.showForm(data)
        value.setValue(20)
        value.setValue(30)
        self.assertEqual(received, [])
        self.ui.Create()
        self.top = self.ui
        self.timers.drain()
        self.assertEqual(received, ['created', (10, 20, 'count'), (20, 30, 'count')])
        self.assertEqual(data['controls'][0]['params']['count']['value'], 30)


if __name__ == '__main__':
    unittest.main()
