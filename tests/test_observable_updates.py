# -*- coding: utf-8 -*-
"""Run with python -S -B -m unittest discover -s tests (no game runtime needed)."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


CORE = Path(__file__).resolve().parents[1] / "behavior/scripts/FormUI/core"


class ObservableUpdateTests(unittest.TestCase):
    def setUp(self):
        self.modules = []
        self.environments = 0
        self.system, self.observable_class, self.server_class = self.load_environment(True)

    def tearDown(self):
        for name in reversed(self.modules):
            sys.modules.pop(name, None)

    def load_environment(self, server):
        self.environments += 1
        prefix = "_formui_observable_test_{}".format(self.environments)

        def module(name, package=False):
            result = types.ModuleType(name)
            if package:
                result.__path__ = []
            sys.modules[name] = result
            self.modules.append(name)
            return result

        def load(suffix, relative_path):
            name = prefix + suffix
            spec = importlib.util.spec_from_file_location(name, CORE / relative_path)
            result = importlib.util.module_from_spec(spec)
            sys.modules[name] = result
            self.modules.append(name)
            spec.loader.exec_module(result)
            return result

        for suffix in ("", ".general", ".general.managers", ".utils", ".server"):
            module(prefix + suffix, True)
        system = types.SimpleNamespace(updates=[])

        def record(data):
            current = system.observableManager.get(data["id"]).getValue()
            system.updates.append((dict(data), current))

        system.BroadcastToAllClient = lambda event, data: record(data)
        system.applyObservableUpdate = record
        environment = module(prefix + ".utils.environment")
        environment.isServer = lambda: server
        environment.getServerSystem = lambda: system
        environment.getClientSystem = lambda: system
        observable = load(".general.observable", "general/observable.py").Observable
        manager = load(".general.managers.observable", "general/managers/observable.py")
        system.observableManager = manager.ObservableManager()
        config = module(prefix + ".config")
        config.Namespace = "test"
        config.SystemNameClient = "client"
        engine = types.ModuleType("mod.server.extraServerApi")
        engine.GetServerSystemCls = lambda: object
        with patch.dict(sys.modules, {
            "mod": types.ModuleType("mod"),
            "mod.server": types.ModuleType("mod.server"),
            "mod.server.extraServerApi": engine,
        }):
            server_class = load(".server.system", "server/system.py").Server
        return system, observable, server_class

    def create(self, value):
        return self.system.observableManager.create(value)

    def values_sent(self):
        return [data["value"] for data, current in self.system.updates]

    def test_both_sides_notify_once_and_callbacks_read_old_value(self):
        for server in (True, False):
            with self.subTest(server=server):
                system, observable, server_class = self.load_environment(server)
                value = system.observableManager.create(10)
                seen = []
                value.subscribe(lambda new: seen.append((value.getValue(), new)))
                value.setValue(20)
                self.assertEqual(seen, [(10, 20)])
                self.assertEqual(value.getValue(), 20)
                self.assertEqual(system.updates, [({"id": value._id, "value": 20}, 20)])
                self.assertEqual(value._id, 0 if server else -1)

    def test_equal_value_does_not_notify(self):
        value = self.create(10)
        value.subscribe(lambda new: self.fail("Equal values must not notify"))
        value.setValue(10)
        self.assertEqual(self.system.updates, [])

    def test_set_data_uses_same_update_flow(self):
        value = self.create("old")
        seen = []
        value.subscribe(lambda new: seen.append((value.getData(), new)))
        value.setData("new")
        self.assertEqual(seen, [("old", "new")])
        self.assertEqual(self.values_sent(), ["new"])

    def test_server_input_suppresses_repeated_values(self):
        value = self.create(False)
        seen = []
        value.subscribe(lambda new: seen.append((value.getValue(), new)))
        server = self.server_class.__new__(self.server_class)
        server.observableManager = self.system.observableManager
        data = {"obId": value._id, "value": True}
        server.applyObservableUpdate(data)
        server.applyObservableUpdate(data)
        self.assertEqual(seen, [(False, True)])
        self.assertEqual(self.values_sent(), [True])

    def test_legacy_update_entry_uses_setter(self):
        value = self.create(0)
        value._onUpdate(1)
        value._onUpdate(1)
        self.assertEqual(value.getValue(), 1)
        self.assertEqual(self.values_sent(), [1])

    def test_list_replacement_preserves_old_list_in_callback(self):
        value = self.create([1])
        seen = []
        value.subscribe(lambda new: seen.append((list(value.getValue()), list(new))))
        value.setValue([1, 2])
        value.setValue([1, 2])
        self.assertEqual(seen, [([1], [1, 2])])
        self.assertEqual(self.values_sent(), [[1, 2]])

    def test_reentrant_updates_are_processed_in_order(self):
        value = self.create(0)
        seen = []

        def callback(new):
            seen.append((value.getValue(), new))
            if new == 1:
                value.setValue(2)
                value.setValue(3)

        value.subscribe(callback)
        value.setValue(1)
        self.assertEqual(seen, [(0, 1), (1, 2), (2, 3)])
        self.assertEqual(self.values_sent(), [1, 2, 3])
        self.assertEqual(value.getValue(), 3)

    def test_callback_reapplying_new_value_does_not_recurse(self):
        value = self.create(0)
        value.subscribe(lambda new: value.setValue(new))
        value.setValue(1)
        self.assertEqual(self.values_sent(), [1])

    def test_subscription_changes_take_effect_on_next_update(self):
        value = self.create(0)
        seen = []

        def second(new):
            seen.append(("second", new))

        def first(new):
            seen.append(("first", new))
            value.unsubscribe(first)
            value.unsubscribe(second)
            value.subscribe(lambda next_value: seen.append(("third", next_value)))

        value.subscribe(first)
        value.subscribe(second)
        value.setValue(1)
        value.setValue(2)
        self.assertEqual(seen, [("first", 1), ("second", 1), ("third", 2)])

    def test_callback_exception_commits_and_does_not_replay_pending_values(self):
        value = self.create(0)

        def failing(new):
            value.setValue(2)
            raise RuntimeError("callback failed")

        value.subscribe(failing)
        with self.assertRaises(RuntimeError):
            value.setValue(1)
        self.assertEqual(value.getValue(), 1)
        self.assertEqual(self.values_sent(), [1])
        value.unsubscribe(failing)
        value.setValue(3)
        self.assertEqual(self.values_sent(), [1, 3])


if __name__ == "__main__":
    unittest.main()
