# -*- coding: utf-8 -*-
"""Public calling conventions, configuration ownership and reactive helpers."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import test_group_controls as groups
import test_observable_updates as observables

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'behavior/scripts/FormUI/core'


class FormApiTests(unittest.TestCase):
    def setUp(self):
        self.fx = groups.GroupControlTests()
        self.fx.setUp()
        self.system = self.fx.system
        self.form = self.system.formManager.create
        self.create = self.system.observableManager.create

    def tearDown(self):
        self.fx.tearDown()

    def payload(self, form):
        form.show('p1')
        return self.fx.payloads[-1]

    def load(self, suffix, path):
        name = self.fx.prefix + suffix
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        self.fx.modules.append(name)
        spec.loader.exec_module(module)
        return module

    def screen(self):
        screen = self.load('.general.screen', CORE / 'general/screen.py').Screen()
        self.system.screen = screen
        return screen

    def test_default_form_has_a_working_builtin_panel(self):
        data = self.payload(self.form('Default'))
        self.assertEqual(data['style']['class']['value'], 'oreui:light_panel_thin')

    def test_theme_applies_to_root_and_all_standard_controls(self):
        for theme in ('oreui', 'flutter', 'flutter-dark', 'fluent', 'fluent-dark'):
            form = self.form('Theme', theme=theme)
            form.button('go').toggle('enabled', True).label('text').divider()
            form.slider('value', 0).textfield('name', '').dropdown('choice', [], None).listview('rows', [])
            data = self.payload(form)
            namespace = theme.split('-')[0] + ':'
            self.assertTrue(data['style']['class']['value'].startswith(namespace))
            for entry in data['controls']:
                self.assertTrue(entry['style']['class']['value'].startswith(namespace))
                if theme.endswith('-dark'):
                    self.assertIn(':dark_', entry['style']['class']['value'])

    def test_explicit_class_overrides_theme_and_themes_do_not_leak(self):
        screen = self.screen()
        screen.setDefaultStyle('button', {'class': 'project:button', 'height': 44})
        themed = self.form('A', {'class': 'project:panel'}, 'fluent-dark')
        themed.button('default').button('custom', style={'class': 'project:special'})
        data = self.payload(themed)
        self.assertEqual(data['style']['class']['value'], 'project:panel')
        self.assertEqual(data['controls'][0]['style']['class']['value'], 'fluent:dark_primary_button')
        self.assertEqual(data['controls'][0]['style']['height']['value'], 44)
        self.assertEqual(data['controls'][1]['style']['class']['value'], 'project:special')
        plain = self.payload(self.form('B').button('default'))
        self.assertEqual(plain['controls'][0]['style']['class']['value'], 'project:button')
        self.assertEqual(screen.getDefaultStyle('button')['class'], 'project:button')

    def test_unknown_theme_fails_immediately(self):
        for theme in ('dark', 'fluter', {}, 1):
            with self.subTest(theme=theme), self.assertRaises(ValueError):
                self.form('bad', theme=theme)

    def test_theme_keeps_custom_and_group_classes_explicit(self):
        form = self.form('A', theme='flutter')
        form.custom(style={'class': 'project:custom'}).group(style={'class': 'project:group'})
        classes = [entry['style']['class']['value'] for entry in self.payload(form)['controls']]
        self.assertEqual(classes, ['project:custom', 'project:group'])

    def test_button_callable_and_group_callable_keep_player_argument(self):
        received = []
        form = self.form('Actions').button('go', received.append)
        form.group({'button': {'callbacks': received.append}}, {'class': 'project:group'})
        data = self.payload(form)
        for control in (data['controls'][0], data['controls'][1]['children']['button']):
            form._btnCallbacks[control['callbacks']['onClick']['value']]('p2')
        self.assertEqual(received, ['p2', 'p2'])

    def test_invalid_callbacks_fail_before_allocating_callback_ids(self):
        form = self.form('Actions')
        for callback in ({'onClik': lambda player: None}, {'onClick': 1}, []):
            with self.subTest(callback=callback), self.assertRaises((TypeError, ValueError)):
                form.button('bad', callback)
        self.assertEqual(list(form._btnCallbacks), [0])

    def test_params_are_snapshots_but_observables_keep_identity(self):
        value = self.create(1)
        params = {'config': {'names': ['one'], 'value': value}}
        form = self.form('Snapshots').button('go', params=params)
        params['config']['names'].append('two')
        value.setValue(2)
        config = self.payload(form)['controls'][0]['params']['config']
        self.assertEqual([item['value'] for item in config['names']], ['one'])
        self.assertEqual((config['value']['obId'], config['value']['value']), (value._id, 2))

    def test_defaults_do_not_share_nested_containers_or_mutate_fallback(self):
        screen = self.screen()
        value = self.create(True)
        source = {'grids': [1, 2], 'visible': value}
        screen.setDefaultStyle('scrolling_panel', source)
        source['grids'][0] = 9
        fallback = {'width': 200}
        result = screen.getDefaultStyle('scrolling_panel', fallback)
        self.assertEqual(fallback, {'width': 200})
        self.assertEqual(result['grids'], [1, 2])
        self.assertIs(result['visible'], value)
        result['grids'][0] = 3
        self.assertEqual(screen.getDefaultStyle('scrolling_panel')['grids'], [1, 2])

    def test_generator_targets_are_deduplicated_and_materialized_for_transport(self):
        sent = []
        self.system.NotifyToMultiClients = lambda targets, event, data: sent.append((targets, event))
        form = self.form('Targets')
        form.show(player for player in ('p2', 'p1', 'p2'))
        form.close(player for player in ('p2', 'p1', 'p2'))
        self.assertEqual(sent, [(['p2', 'p1'], 'showForm'), (['p2', 'p1'], 'closeForm')])

    def test_empty_targets_never_broadcast_or_install_close_listeners(self):
        screen = self.screen()
        sent = []
        self.system.NotifyToMultiClients = lambda *args: sent.append(args)
        form = self.form('Empty')
        form.show([])
        form.close([])
        screen.closeAllForms([])
        self.assertEqual(sent, [])
        self.assertEqual(self.fx.listeners, [])

    def test_invalid_server_targets_fail_before_network_operations(self):
        form = self.form('Bad target')
        for target in ('', False, 123, ['p1', None], {'p1': True}):
            with self.subTest(target=target), self.assertRaises((ValueError, TypeError)):
                form.show(target)
            with self.subTest(target=target), self.assertRaises((ValueError, TypeError)):
                form.close(target)
        self.assertEqual(self.fx.payloads, [])
        self.assertEqual(self.fx.listeners, [])

    def test_close_all_default_and_generator_use_same_target_semantics(self):
        screen = self.screen()
        sent = []
        self.system.NotifyToMultiClients = lambda targets, event, data: sent.append(targets)
        screen.closeAllForms()
        screen.closeAllForms(player for player in ('p2', 'p2'))
        self.assertEqual(sent, [['p1', 'p2'], ['p2']])

    def test_explicit_showing_queries_keep_legacy_all_semantics(self):
        form = self.form('State')
        form.show(['p1', 'p2'])
        fid = self.fx.payloads[-1]['formId']['value']
        self.fx.emit('formClose%s' % fid, {'playerId': 'p1', 'closeReason': 'user'})
        self.assertFalse(form.isShowing())
        self.assertTrue(form.isAnyShowing())
        self.assertEqual(form.getShowingPlayers(), ['p2'])
        self.fx.players.remove('p2')
        self.assertFalse(form.isAnyShowing())

    def test_show_callback_is_installed_before_synchronous_close(self):
        received = []
        def send(target, event, data):
            fid = data['formId']['value']
            self.fx.emit('formClose%s' % fid, {'playerId': target, 'closeReason': 'user'})
        self.system.NotifyToClient = send
        form = self.form('Close')
        form.show('p1', onClose=lambda args: received.append((args.playerId, form.isAnyShowing())))
        self.assertEqual(received, [('p1', False)])
        self.assertEqual(self.fx.listeners, [])

    def test_descriptors_and_registration_options_have_independent_paths(self):
        descriptors = sys.modules[self.fx.public.__module__.rsplit('.', 1)[0] + '.controls']
        first, second = descriptors.Button(), descriptors.Button()
        first.labelPaths.append('/other')
        self.assertEqual(second.labelPaths, ['/button_label'])
        self.fx.server_side = False
        self.fx.public.register('copy:button', 'button.path', first)
        first.labelPaths.append('/later')
        stored = self.system.controlManager.get('copy:button').options['labelPaths']
        self.assertEqual(stored, ['/button_label', '/other'])
        with self.assertRaises(TypeError):
            self.fx.public.register('copy:bad', 'button.path', object())

    def test_auto_registration_requeries_system_on_both_sides(self):
        prefix = '_formui_environment_actual'
        for suffix in ('', '.core', '.core.utils', '.core.config', '.register', '.core.init_system'):
            node = types.ModuleType(prefix + suffix)
            node.__path__ = []
            sys.modules[node.__name__] = node
            self.fx.modules.append(node.__name__)
        config = sys.modules[prefix + '.core.config']
        config.Namespace, config.SystemNameServer, config.SystemNameClient = 'test', 'server', 'client'
        client_stub = sys.modules[prefix + '.register']
        client_stub.client_system_path = 'client.path'
        server_stub = sys.modules[prefix + '.core.init_system']
        server_stub.server_system_path = 'server.path'
        spec = importlib.util.spec_from_file_location(prefix + '.core.utils.environment', CORE / 'utils/environment.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for side, getter in (('server', module.getServerSystem), ('client', module.getClientSystem)):
            api = sys.modules['mod.%s.extra%sApi' % (side, side.title())]
            with patch.object(api, 'GetSystem', side_effect=[None, self.system], create=True) as get:
                self.assertIs(getter(), self.system)
                self.assertEqual(get.call_count, 2)


class ObservableApiTests(unittest.TestCase):
    setUp = observables.ObservableUpdateTests.setUp
    tearDown = observables.ObservableUpdateTests.tearDown
    load_environment = observables.ObservableUpdateTests.load_environment
    create = observables.ObservableUpdateTests.create
    values_sent = observables.ObservableUpdateTests.values_sent

    def test_update_copies_nested_mutable_state_and_preserves_old_callback_value(self):
        source = {'items': [1]}
        value = self.create(source)
        seen = []
        value.subscribe(lambda new: seen.append((value.getValue(), new)))
        def append(current):
            current['items'].append(2)
            return current
        value.update(append)
        self.assertEqual(source, {'items': [1]})
        self.assertEqual(seen, [({'items': [1]}, {'items': [1, 2]})])

    def test_reentrant_updates_compute_from_latest_committed_value(self):
        value = self.create(0)
        def changed(new):
            if new == 1:
                value.update(lambda current: current + 1)
                value.update(lambda current: current + 1)
        value.subscribe(changed)
        value.setValue(1)
        self.assertEqual(value.getValue(), 3)
        self.assertEqual(self.values_sent(), [1, 2, 3])

    def test_updater_failure_keeps_original_state_and_later_updates_work(self):
        value = self.create([1])
        def fail(current):
            current.append(2)
            raise RuntimeError('cannot compute')
        with self.assertRaises(RuntimeError):
            value.update(fail)
        self.assertEqual(value.getValue(), [1])
        self.assertEqual(self.values_sent(), [])
        value.update(lambda current: current + [3])
        self.assertEqual(value.getValue(), [1, 3])

    def test_watch_immediate_cancel_and_same_callback_independent_handles(self):
        value = self.create(0)
        seen = []
        stop_first = value.watch(seen.append)
        stop_second = value.watch(seen.append, immediate=False)
        self.assertEqual(seen, [0])
        value.setValue(1)
        stop_first()
        stop_first()
        value.setValue(2)
        stop_second()
        value.setValue(3)
        self.assertEqual(seen, [0, 1, 1, 2])

    def test_watch_initial_callback_failure_does_not_leave_subscription(self):
        value = self.create(0)
        def fail(new):
            raise RuntimeError('initial callback failed')
        with self.assertRaises(RuntimeError):
            value.watch(fail)
        value.setValue(1)
        self.assertEqual(value.getValue(), 1)

    def test_map_initial_value_chained_updates_and_input_copy(self):
        value = self.create([1])
        length = value.map(lambda rows: len(rows))
        label = length.map(lambda count: 'Count: %s' % count)
        def transform(rows):
            rows.append(99)
            return rows
        mapped = value.map(transform)
        self.assertEqual(value.getValue(), [1])
        self.assertEqual(mapped.getValue(), [1, 99])
        value.update(lambda rows: rows + [2])
        self.assertEqual(length.getValue(), 2)
        self.assertEqual(label.getValue(), 'Count: 2')
        self.assertEqual(mapped.getValue(), [1, 2, 99])

    def test_helper_arguments_fail_immediately(self):
        value = self.create(0)
        for method in (value.subscribe, value.watch, value.map, value.update):
            with self.subTest(method=method.__name__), self.assertRaises(TypeError):
                method(None)

    def test_unknown_remote_observable_is_ignored(self):
        server = self.server_class.__new__(self.server_class)
        server.observableManager = self.system.observableManager
        server.applyObservableUpdate({'obId': 999, 'value': True})
        self.assertEqual(self.values_sent(), [])


if __name__ == '__main__':
    unittest.main()
