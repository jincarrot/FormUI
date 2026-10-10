# -*- coding: utf-8 -*-
"""Observable operator regressions; uses the isolated engine fixture."""
import importlib.util
import operator
import unittest
import test_observable_updates as fixture


class ObservableOperationTests(unittest.TestCase):
    setUp = fixture.ObservableUpdateTests.setUp
    tearDown = fixture.ObservableUpdateTests.tearDown
    load_environment = fixture.ObservableUpdateTests.load_environment
    create = fixture.ObservableUpdateTests.create
    values_sent = fixture.ObservableUpdateTests.values_sent

    def test_all_forward_operators_register_and_follow_both_operands(self):
        operations = (
            operator.lt, operator.le, operator.gt, operator.ge,
            operator.eq, operator.ne, operator.add, operator.sub,
            operator.mul, operator.truediv, operator.floordiv,
            operator.mod, operator.pow, operator.and_, operator.or_,
            operator.xor, operator.lshift, operator.rshift,
        )
        for operation in operations:
            with self.subTest(operation=operation.__name__):
                left, right = self.create(6), self.create(2)
                result = operation(left, right)
                self.assertIs(self.system.observableManager.get(result._id), result)
                self.assertEqual(result.getValue(), operation(6, 2))
                left.setValue(9)
                self.assertEqual(result.getValue(), operation(9, 2))
                right.setValue(3)
                self.assertEqual(result.getValue(), operation(9, 3))
                constant_result = operation(left, 2)
                left.setValue(5)
                self.assertEqual(constant_result.getValue(), operation(5, 2))
                self.assertEqual(result.getValue(), operation(5, 3))

    def test_reverse_operators_preserve_operand_order(self):
        operations = (
            operator.lt, operator.le, operator.gt, operator.ge,
            operator.eq, operator.ne, operator.add, operator.sub,
            operator.mul, operator.truediv, operator.floordiv,
            operator.mod, operator.pow, operator.and_, operator.or_,
            operator.xor, operator.lshift, operator.rshift,
        )
        for operation in operations:
            with self.subTest(operation=operation.__name__):
                value = self.create(2)
                result = operation(6, value)
                self.assertIs(self.system.observableManager.get(result._id), result)
                self.assertEqual(result.getValue(), operation(6, 2))
                value.setValue(3)
                self.assertEqual(result.getValue(), operation(6, 3))

    def test_derived_values_bind_and_sync_on_both_sides(self):
        spec = importlib.util.spec_from_file_location("_formui_wrap_test", fixture.CORE / "utils/type.py")
        wrapper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wrapper)
        for server in (True, False):
            with self.subTest(server=server):
                system, observable, server_class = self.load_environment(server)
                source = system.observableManager.create(2)
                result = source * 3
                record = []
                wrapped = wrapper.wrapVariable(result, record)
                self.assertEqual(wrapped, {"type": "Observable", "value": 6, "obId": result._id})
                self.assertEqual(record, [result._id])
                seen = []
                result.subscribe(lambda new: seen.append((result.getValue(), new)))
                source.setValue(4)
                self.assertEqual(seen, [(6, 12)])
                updates = [data for data, current in system.updates if data["id"] == result._id]
                self.assertEqual(updates, [{"id": result._id, "value": 12}])
                self.assertEqual(result._id, 1 if server else -2)

    def test_same_source_in_both_operands_has_no_intermediate_values(self):
        value = self.create(3)
        difference = value - value
        total = value + value
        seen = []
        difference.subscribe(lambda new: self.fail("x - x must stay zero"))
        total.subscribe(lambda new: seen.append(new))
        value.setValue(5)
        self.assertEqual(difference.getValue(), 0)
        self.assertEqual(total.getValue(), 10)
        self.assertEqual(seen, [10])

    def test_chained_expression_uses_callback_new_values(self):
        source = self.create(2)
        result = (source + 1) * 3
        comparison = result > 10
        self.assertEqual(result.getValue(), 9)
        self.assertFalse(comparison)
        source.setValue(4)
        self.assertEqual(result.getValue(), 15)
        self.assertTrue(comparison)
        source.setValue(1)
        self.assertEqual(result.getValue(), 6)
        self.assertFalse(comparison)

    def test_truth_conversion_reads_underlying_value(self):
        for raw in (False, True, 0, 1, "", "text", [], [1], None):
            with self.subTest(raw=raw):
                value = self.create(raw)
                self.assertEqual(bool(value), bool(raw))
                self.assertEqual(value.__nonzero__(), bool(raw))
        value = self.create(3)
        equal = value == 4
        different = value != 4
        self.assertFalse(equal)
        self.assertTrue(different)
        value.setValue(4)
        self.assertTrue(equal)
        self.assertFalse(different)

    def test_python2_division_entries_use_true_division(self):
        value = self.create(3)
        quotient = value.__div__(2)
        reverse_quotient = value.__rdiv__(10)
        self.assertEqual(quotient.getValue(), 1.5)
        self.assertEqual(reverse_quotient.getValue(), 10 / 3)
        value.setValue(4)
        self.assertEqual(quotient.getValue(), 2)
        self.assertEqual(reverse_quotient.getValue(), 2.5)

    def test_modular_power_follows_all_three_observables(self):
        base, exponent, modulus = self.create(2), self.create(3), self.create(5)
        result = pow(base, exponent, modulus)
        self.assertEqual(result.getValue(), pow(2, 3, 5))
        base.setValue(3)
        self.assertEqual(result.getValue(), pow(3, 3, 5))
        exponent.setValue(4)
        self.assertEqual(result.getValue(), pow(3, 4, 5))
        modulus.setValue(7)
        self.assertEqual(result.getValue(), pow(3, 4, 7))

    def test_failed_initial_operation_does_not_create_result_or_subscription(self):
        value = self.create(2)
        with self.assertRaises(ZeroDivisionError):
            value / 0
        value.setValue(3)
        self.assertEqual(self.values_sent(), [3])
        next_value = self.create(4)
        self.assertEqual(next_value._id, value._id + 1)

    def test_server_input_updates_derived_expression(self):
        source = self.create(2)
        result = source + 3
        server = self.server_class.__new__(self.server_class)
        server.observableManager = self.system.observableManager
        server.applyObservableUpdate({"obId": source._id, "value": 4})
        self.assertEqual(result.getValue(), 7)
        self.assertIs(self.system.observableManager.get(result._id), result)

    def test_invalid_intermediate_operation_recovers_on_next_update(self):
        numerator, denominator = self.create(6), self.create(2)
        result = numerator / denominator
        with self.assertRaises(ZeroDivisionError):
            denominator.setValue(0)
        self.assertEqual(denominator.getValue(), 0)
        denominator.setValue(3)
        self.assertEqual(result.getValue(), 2)


if __name__ == "__main__":
    unittest.main()
