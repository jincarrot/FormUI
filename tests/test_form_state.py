# -*- coding: utf-8 -*-
"""Form state and close-listener regressions without the game runtime."""
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch
import test_observable_updates as fixture


class FormStateTests(unittest.TestCase):
    load_environment = fixture.ObservableUpdateTests.load_environment

    def setUp(self):
        fixture.ObservableUpdateTests.setUp(self)
        self.players = ['p1', 'p2']
        self.server_side = True
        self.listeners = []
        self.sent = []
        self.player_list_calls = 0
        self.system.ListenForEvent = lambda *args: self.listeners.append(args)
        self.system.UnListenForEvent = lambda *args: self.listeners.remove(args)
        self.system.NotifyToClient = lambda target, event, data: self.sent.append(([target], event))
        self.system.NotifyToMultiClients = lambda targets, event, data: self.sent.append((list(targets), event))
        self.system.showForm = lambda data: self.sent.append((['p1'], 'showForm'))
        self.system.screen = types.SimpleNamespace(getDefaultStyle=lambda kind, defaults: defaults)
        prefix = self.observable_class.__module__.split('.general')[0]
        environment = sys.modules[prefix + '.utils.environment']
        environment.isServer = lambda: self.server_side
        environment.getSystem = lambda: self.system
        server = types.ModuleType('mod.server.extraServerApi')
        server.GetPlayerList = self.get_players
        server.GetEngineNamespace = lambda: 'engine'
        server.GetEngineSystemName = lambda: 'engineServer'
        client = types.ModuleType('mod.client.extraClientApi')
        client.GetLocalPlayerId = lambda: 'p1'
        self.engine_patch = patch.dict(sys.modules, {
            'mod': types.ModuleType('mod'),
            'mod.server': types.ModuleType('mod.server'),
            'mod.client': types.ModuleType('mod.client'),
            'mod.server.extraServerApi': server,
            'mod.client.extraClientApi': client,
        })
        self.engine_patch.start()

        def load(suffix, relative):
            name = prefix + suffix
            spec = importlib.util.spec_from_file_location(name, fixture.CORE / relative)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.modules.append(name)
            spec.loader.exec_module(module)
            return module

        load('.utils.type', 'utils/type.py')
        load('.utils.ui', 'utils/ui.py')
        load('.utils.group', 'utils/group.py')
        load('.general.form', 'general/form.py')
        manager = load('.general.managers.form', 'general/managers/form.py')
        self.system.formManager = manager.FormManager()
        self.form = self.system.formManager.create('test')

    def tearDown(self):
        self.engine_patch.stop()
        fixture.ObservableUpdateTests.tearDown(self)

    def get_players(self):
        self.player_list_calls += 1
        return list(self.players)

    def emit(self, event, data):
        for listener in tuple(self.listeners):
            if listener in self.listeners and listener[2] == event:
                listener[-1](data)

    def close(self, player):
        self.emit('formClose0', {'playerId': player, 'closeReason': 'user'})

    def leave(self, player):
        self.players.remove(player)
        self.emit('PlayerLeftMessageServerEvent', {'id': player})

    def test_new_form_and_unknown_player_are_not_showing(self):
        self.assertFalse(self.form.isShowing())
        self.assertFalse(self.form.isShowing('p1'))
        self.assertFalse(self.form.isShowing(''))

    def test_all_means_historical_players_not_every_online_player(self):
        self.form.show('p1')
        self.assertTrue(self.form.isShowing())
        self.assertTrue(self.form.isShowing('p1'))
        self.assertFalse(self.form.isShowing('p2'))
        self.close('p1')
        self.assertFalse(self.form.isShowing())
        self.assertEqual(self.form._isShowing, {'p1': False})

    def test_closed_historical_player_keeps_all_query_false(self):
        self.form.show(['p1', 'p2'])
        self.close('p1')
        self.assertFalse(self.form.isShowing())
        self.assertFalse(self.form.isShowing('p1'))
        self.assertTrue(self.form.isShowing('p2'))

    def test_offline_players_are_not_showing_and_online_list_is_read_once(self):
        self.form.show(['p1', 'p2'])
        self.players[:] = []
        previous_calls = self.player_list_calls
        self.assertFalse(self.form.isShowing())
        self.assertEqual(self.player_list_calls, previous_calls + 1)
        self.assertFalse(self.form.isShowing('p1'))

    def test_disconnect_clears_state_and_listeners_before_reconnection(self):
        seen = []
        self.form.show('p1').onClose(lambda args: seen.append(args.playerId))
        self.leave('p1')
        self.assertEqual(self.form._isShowing, {'p1': False})
        self.assertEqual(self.listeners, [])
        self.assertEqual(seen, [])
        self.players.append('p1')
        self.assertFalse(self.form.isShowing('p1'))
        self.form.show('p1')
        self.assertTrue(self.form.isShowing('p1'))

    def test_separate_shows_only_receive_their_own_players(self):
        seen = []
        self.form.show('p1').onClose(lambda args: seen.append(('first', args.playerId)))
        self.form.show('p2').onClose(lambda args: seen.append(('second', args.playerId)))
        self.close('p1')
        self.assertEqual(seen, [('first', 'p1')])
        self.assertEqual(len(self.listeners), 2)
        self.close('p2')
        self.assertEqual(seen, [('first', 'p1'), ('second', 'p2')])
        self.assertEqual(self.listeners, [])

    def test_group_closes_once_per_player_then_unsubscribes(self):
        seen = []
        self.form.show(['p1', 'p2', 'p1']).onClose(lambda args: seen.append((args.playerId, args.closeReason)))
        self.close('p3')
        self.close('p1')
        self.close('p1')
        self.assertEqual(seen, [('p1', 'user')])
        self.assertNotIn('p3', self.form._isShowing)
        self.assertEqual(len(self.listeners), 2)
        self.close('p2')
        self.assertEqual(seen, [('p1', 'user'), ('p2', 'user')])
        self.assertEqual(self.listeners, [])

    def test_repeated_show_cycles_do_not_replay_old_callbacks(self):
        seen = []
        for index in range(3):
            self.form.show('p1').onClose(lambda args, current=index: seen.append(current))
            self.close('p1')
            self.assertEqual(self.listeners, [])
        self.assertEqual(seen, [0, 1, 2])

    def test_one_player_leaving_keeps_remaining_group_listener(self):
        seen = []
        self.form.show(['p1', 'p2']).onClose(lambda args: seen.append(args.playerId))
        self.leave('p2')
        self.assertEqual(len(self.listeners), 2)
        self.assertFalse(self.form.isShowing())
        self.assertTrue(self.form.isShowing('p1'))
        self.close('p1')
        self.assertEqual(seen, ['p1'])
        self.assertEqual(self.listeners, [])

    def test_client_tracks_actual_local_player_and_unsubscribes(self):
        self.server_side = False
        seen = []
        self.form.show('p2').onClose(lambda args: seen.append(args.playerId))
        self.assertTrue(self.form.isShowing())
        self.assertFalse(self.form.isShowing('p2'))
        self.assertEqual(len(self.listeners), 1)
        self.close('p1')
        self.assertFalse(self.form.isShowing())
        self.assertEqual(seen, ['p1'])
        self.assertEqual(self.listeners, [])

    def test_callback_observes_closed_state(self):
        seen = []
        self.form.show('p1').onClose(lambda args: seen.append(self.form.isShowing(args.playerId)))
        self.close('p1')
        self.assertEqual(seen, [False])

    def test_callback_exception_still_releases_listeners(self):
        def failing(args):
            raise RuntimeError('callback failed')
        self.form.show('p1').onClose(failing)
        with self.assertRaises(RuntimeError):
            self.close('p1')
        self.assertFalse(self.form.isShowing('p1'))
        self.assertEqual(self.listeners, [])

    def test_callback_can_show_again_without_old_listener_interfering(self):
        seen = []
        def reopen(args):
            seen.append('first')
            self.form.show('p1').onClose(lambda next_args: seen.append('second'))
        self.form.show('p1').onClose(reopen)
        self.close('p1')
        self.assertTrue(self.form.isShowing('p1'))
        self.assertEqual(len(self.listeners), 2)
        self.close('p1')
        self.assertEqual(seen, ['first', 'second'])
        self.assertEqual(self.listeners, [])

    def test_failed_send_restores_state_and_preserves_existing_listeners(self):
        self.form.show('p2')
        self.form._isShowing['p1'] = False
        previous_listeners = list(self.listeners)
        def failing(*args):
            raise RuntimeError('send failed')
        self.system.NotifyToClient = failing
        with self.assertRaises(RuntimeError):
            self.form.show('p1')
        self.assertEqual(self.form._isShowing, {'p1': False, 'p2': True})
        self.assertEqual(self.listeners, previous_listeners)
        with self.assertRaises(RuntimeError):
            self.form.show('p3')
        self.assertNotIn('p3', self.form._isShowing)
        self.assertEqual(self.listeners, previous_listeners)

    def test_empty_targets_create_no_listener_or_state(self):
        self.form.show([])
        self.assertEqual(self.listeners, [])
        self.assertFalse(self.form.isShowing())

    def test_duplicate_show_raises_before_sending_or_registering_listeners(self):
        self.form.show('p1')
        previous = list(self.listeners)
        sent = list(self.sent)
        with self.assertRaisesRegex(RuntimeError, '该表单已经被显示出来了'):
            self.form.show('p1')
        with self.assertRaises(RuntimeError):
            self.form.show(['p1', 'p2'])
        self.assertEqual(self.listeners, previous)
        self.assertEqual(self.sent, sent)
        self.assertFalse(self.form.isShowing('p2'))
        self.close('p1')
        self.form.show('p1')
        self.assertTrue(self.form.isShowing('p1'))

    def test_client_duplicate_show_uses_the_actual_local_player(self):
        self.server_side = False
        self.form.show()
        with self.assertRaises(RuntimeError):
            self.form.show('p2')
        self.assertEqual(len(self.listeners), 1)

    def test_server_default_targets_are_online_players(self):
        self.form.show()
        self.assertEqual(self.sent, [(['p1', 'p2'], 'showForm')])
        self.assertTrue(self.form.isShowing())
        self.close('p1')
        self.close('p2')
        self.assertEqual(self.listeners, [])

    def test_synchronous_close_during_send_is_not_missed(self):
        self.system.NotifyToClient = lambda *args: self.close('p1')
        self.form.show('p1')
        self.assertFalse(self.form.isShowing('p1'))
        self.assertEqual(self.listeners, [])

    def test_failed_listener_registration_releases_previous_registration(self):
        def listen(*args):
            if args[2] == 'PlayerLeftMessageServerEvent':
                raise RuntimeError('listen failed')
            self.listeners.append(args)
        self.system.ListenForEvent = listen
        with self.assertRaises(RuntimeError):
            self.form.show('p1')
        self.assertEqual(self.listeners, [])
        self.assertEqual(self.form._isShowing, {})


if __name__ == '__main__':
    unittest.main()
