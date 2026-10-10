# -*- coding: utf-8 -*-
"""Production custom creation, instance routing, parameter snapshots and lifecycle."""
import io
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import test_form_style as fixture
from custom_ui_fixture import install_custom_ui


class CustomControlTests(unittest.TestCase):
    load_environment = fixture.FormStyleTests.load_environment
    get_players = fixture.FormStyleTests.get_players
    emit = fixture.FormStyleTests.emit
    tearDown = fixture.FormStyleTests.tearDown
    make_form = fixture.FormStyleTests.make_form
    add = fixture.FormStyleTests.add
    close_ui = fixture.FormStyleTests.close_ui

    def setUp(self):
        fixture.FormStyleTests.setUp(self)
        self.created = []
        self.updated = []
        install_custom_ui(self, self.created.append, self.updated.append)
        self.prefix = self.observable_class.__module__.split('.general')[0]
        self.util = sys.modules[self.prefix + '.utils.type']

    def make_custom(self, params, **style):
        options = {'class': 'custom'}
        options.update(style)
        return self.make_form(width=400, height=200).custom(params, options)

    def test_creation_gets_raw_parameters_native_control_and_completed_layout(self):
        value = self.system.observableManager.create(0)
        values = self.system.observableManager.create([1, 2])
        form = self.make_form(width=400, height=200, grids=[1, 1])
        params = {'text': 'hello', 'count': value, 'values': values,
                  'nested': {'a': False, 'b': [None, value]}}
        form.custom(params, {'class': 'custom'}).custom({'text': 'second'}, {'class': 'custom'})
        self.add(form)
        first, second = self.created
        self.assertIs(first.screenNode, self.ui)
        self.assertIs(first.control, self.native_customs[0])
        self.assertEqual(first.params, {'text': 'hello', 'count': 0, 'values': [1, 2],
                                        'nested': {'a': False, 'b': [None, 0]}})
        self.assertEqual(first.control.GetSize(), (192, 32))
        self.assertEqual(first.control.GetPosition(), (4, 0))
        self.assertEqual(second.control.GetPosition(), (204, 0))
        self.assertEqual(self.updated, [])

    def test_updates_target_same_class_instances_without_global_control_reference(self):
        first = self.system.observableManager.create('one')
        second = self.system.observableManager.create('two')
        def create(args):
            args.control.GetChildByPath('/label').asLabel().SetText(args.params['text'])
        def update(args):
            args.control.GetChildByPath('/label').asLabel().SetText(args.newValue)
            self.updated.append(args)
        self.registry['custom'].options.update(onCreate=create, onObservableUpdate=update)
        form = self.make_custom({'text': first}).custom({'text': second}, {'class': 'custom'})
        self.add(form)
        second.setValue('changed')
        self.assertEqual(self.native_customs[0].children['/label'].text, 'one')
        self.assertEqual(self.native_customs[1].children['/label'].text, 'changed')
        event = self.updated[0]
        self.assertIs(event.control, self.native_customs[1])
        self.assertIs(event.screenNode, self.ui)
        self.assertEqual((event.key, event.oldValue, event.newValue), ('text', 'two', 'changed'))
        self.assertEqual(event.params, {'text': 'changed'})

    def test_shared_observable_updates_every_instance_once(self):
        value = self.system.observableManager.create(1)
        self.add(self.make_custom({'count': value}))
        self.add(self.make_custom({'count': value}))
        value.setValue(2)
        self.assertEqual(len(self.updated), 2)
        self.assertCountEqual([args.control for args in self.updated], self.native_customs)
        self.assertTrue(all((args.oldValue, args.newValue) == (1, 2) for args in self.updated))

    def test_nested_observables_notify_top_level_parameter_with_complete_old_and_new_values(self):
        value = self.system.observableManager.create(1)
        self.add(self.make_custom({'config': {'count': value, 'items': [value, 'constant']},
                                   'array': [0, value]}))
        value.setValue(2)
        events = {event.key: event for event in self.updated}
        self.assertEqual(len(self.updated), 2)
        self.assertEqual(events['config'].oldValue, {'count': 1, 'items': [1, 'constant']})
        self.assertEqual(events['config'].newValue, {'count': 2, 'items': [2, 'constant']})
        self.assertEqual(events['array'].oldValue, [0, 1])
        self.assertEqual(events['array'].newValue, [0, 2])
        self.assertEqual(events['config'].params['array'], [0, 2])

    def test_list_valued_observable_and_snapshot_mutations_do_not_modify_binding_values(self):
        value = self.system.observableManager.create([1])
        _, data = self.add(self.make_custom({'items': value}))
        self.created[0].params['items'].append(99)
        self.assertEqual(value.getValue(), [1])
        value.setValue([2])
        event = self.updated[0]
        event.oldValue.append(10)
        event.newValue.append(20)
        event.params['items'].append(30)
        self.assertEqual(value.getValue(), [2])
        self.assertEqual(data['controls'][0]['params']['items']['value'], [2])

    def test_custom_works_with_update_callback_only(self):
        self.registry['custom'].options['onCreate'] = None
        value = self.system.observableManager.create(0)
        self.add(self.make_custom({'count': value}))
        value.setValue(1)
        self.assertEqual(self.created, [])
        self.assertIs(self.updated[0].control, self.native_customs[0])

    def test_custom_works_without_update_callback(self):
        self.registry['custom'].options['onObservableUpdate'] = None
        value = self.system.observableManager.create(False)
        _, data = self.add(self.make_custom({'state': value}))
        value.setValue(True)
        self.assertEqual(len(self.created), 1)
        self.assertTrue(data['controls'][0]['params']['state']['value'])
        self.assertEqual(self.updated, [])

    def test_default_native_panel_template_can_be_used_for_custom(self):
        _, data = self.add(self.make_form(width=400, height=200).custom({'plain': 1}))
        self.assertEqual(data['controls'][0]['style']['class']['value'], 'oreui:light_panel_thin')
        self.assertEqual(self.native_customs[0].GetSize(), (392, 32))

    def test_updates_before_creation_keep_context_and_order_during_reentrant_updates(self):
        value = self.system.observableManager.create(10)
        events = []
        targets = []
        def create(args):
            events.append(('created', args.params['count']))
        def update(args):
            events.append((args.oldValue, args.newValue))
            targets.append(args.control)
            if args.newValue == 20:
                value.setValue(40)
        self.registry['custom'].options.update(onCreate=create, onObservableUpdate=update)
        self.make_custom({'count': value}).show('p1')
        self.ui.addForm(self.payloads[-1])
        value.setValue(20)
        value.setValue(30)
        self.assertEqual(events, [])
        self.timers.drain()
        self.assertEqual(events, [('created', 30), (10, 20), (20, 30), (30, 40)])
        self.assertEqual(targets, [self.native_customs[0]] * 3)

    def test_on_create_updates_wait_until_callback_finishes_and_apply_style_changes(self):
        value = self.system.observableManager.create(1)
        height = self.system.observableManager.create(32)
        events = []
        def create(args):
            events.append('create start')
            value.setValue(2)
            height.setValue(64)
            events.append('create end')
        def update(args):
            events.append((args.oldValue, args.newValue, args.control.GetSize()[1]))
        self.registry['custom'].options.update(onCreate=create, onObservableUpdate=update)
        self.add(self.make_custom({'count': value}, height=height))
        self.assertEqual(events, ['create start', 'create end', (1, 2, 64)])
        self.assertEqual(self.native_customs[0].GetSize()[1], 64)

    def test_close_stops_callbacks_for_that_instance_and_preserves_other_forms(self):
        value = self.system.observableManager.create(1)
        first, _ = self.add(self.make_custom({'count': value}))
        self.add(self.make_custom({'count': value}))
        self.close_ui(first)
        value.setValue(2)
        self.assertEqual(len(self.updated), 1)
        self.assertIs(self.updated[0].control, self.native_customs[1])

    def test_closing_from_create_stops_remaining_creation_callbacks(self):
        def create(args):
            self.created.append(args)
            form_id = next(iter(self.ui.forms))
            self.close_ui(form_id)
        self.registry['custom'].options['onCreate'] = create
        self.add(self.make_custom({}).custom({}, {'class': 'custom'}))
        self.assertEqual(len(self.created), 1)
        self.assertEqual(self.ui.forms, {})

    def test_callback_failure_does_not_block_other_instances(self):
        value = self.system.observableManager.create(1)
        def update(args):
            if args.control is self.native_customs[0]:
                raise ValueError('bad renderer')
            self.updated.append(args)
        self.registry['custom'].options['onObservableUpdate'] = update
        _, data = self.add(self.make_custom({'count': value}).custom({'count': value}, {'class': 'custom'}))
        output = io.StringIO()
        with patch('sys.stdout', output):
            value.setValue(2)
        self.assertIn('bad renderer', output.getvalue())
        self.assertEqual(len(self.updated), 1)
        self.assertIs(self.updated[0].control, self.native_customs[1])
        self.assertEqual([control['params']['count']['value'] for control in data['controls']], [2, 2])

    def test_params_are_copied_and_invalid_params_fail_early(self):
        params = {'text': 'hello'}
        form = self.make_custom(params)
        params['new_key'] = 2
        _, data = self.add(form)
        self.assertEqual(self.created[0].params, {'text': 'hello'})
        for params in (None, [], 'invalid'):
            with self.subTest(params=params), self.assertRaises(TypeError):
                self.make_custom(params)

    def test_legacy_callback_argument_constructors_remain_supported(self):
        create = self.util.CreateArguments(self.ui, object())
        update = self.util.ObservableUpdateArguments(1, 2, 'count')
        self.assertEqual(create.params, {})
        self.assertEqual((update.oldValue, update.newValue, update.key), (1, 2, 'count'))
        self.assertIsNone(update.control)

    def load_public_registration(self):
        prefix = self.prefix + '_public'
        for suffix in ('', '.interfaces', '.interfaces.base'):
            package = types.ModuleType(prefix + suffix)
            package.__path__ = []
            sys.modules[package.__name__] = package
            self.modules.append(package.__name__)
        for name, module in list(sys.modules.items()):
            if name == self.prefix or name.startswith(self.prefix + '.'):
                alias = prefix + '.core' + name[len(self.prefix):]
                sys.modules[alias] = module
                self.modules.append(alias)
        loaded = []
        for suffix, relative in (('.controls', 'controls.py'), ('.control', 'control.py')):
            name = prefix + '.interfaces.base' + suffix
            path = Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/interfaces/base' / relative
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.modules.append(name)
            spec.loader.exec_module(module)
            loaded.append(module)
        return loaded[1].Control, loaded[0].Custom

    def test_public_client_custom_registration_drives_creation_and_updates(self):
        registrar, custom = self.load_public_registration()
        self.server_side = False
        registrar.register('sample:label', 'fui_ore_base.label',
                           custom(onCreate=self.created.append, onObservableUpdate=self.updated.append))
        self.server_side = True
        value = self.system.observableManager.create('initial')
        self.add(self.make_custom({'text': value}, **{'class': 'sample:label'}))
        value.setValue('changed')
        self.assertEqual(self.created[0].params, {'text': 'initial'})
        self.assertEqual(self.updated[0].newValue, 'changed')
        self.assertIs(self.created[0].control, self.updated[0].control)

    def test_server_registration_without_callbacks_remains_supported(self):
        registrar, custom = self.load_public_registration()
        broadcasts = []
        self.system.BroadcastToAllClient = lambda event, data: broadcasts.append((event, data))
        registrar.register('sample:plain', 'fui_ore_base.label', custom())
        self.assertEqual(broadcasts[0][0], 'registerControl')
        self.assertEqual(broadcasts[0][1]['type'], 'custom')
        self.add(self.make_custom({'text': 'plain'}, **{'class': 'sample:plain'}))
        self.assertEqual(self.created, [])
        self.assertEqual(self.updated, [])

    def test_server_owned_params_update_without_querying_remote_observable_objects(self):
        value = self.system.observableManager.create(10)
        self.add(self.make_custom({'count': value}))
        queries = []
        def fail(*args):
            queries.append(args)
            raise AssertionError('custom must use transferred values')
        self.system.observableManager.get = fail
        value.setValue(20)
        self.assertEqual(queries, [])
        self.assertEqual((self.updated[0].oldValue, self.updated[0].newValue), (10, 20))
        self.assertEqual(self.updated[0].params, {'count': 20})


if __name__ == '__main__':
    unittest.main()
