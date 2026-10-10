"""Dimension expressions and slider boundaries without the game runtime."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'ui_parameter_utils', Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/core/utils/ui.py')
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


class UIParameterTests(unittest.TestCase):
    def test_dimensions_support_signed_decimals_and_numeric_strings(self):
        cases = [('50.5%-2.25px', -2.25, .505, 'parent'),
                 ('-.5px', -.5, 0, 'parent'), ('12.5', 12.5, 0, 'parent'),
                 ('100%+-15px', -15, 1, 'parent'),
                 (' 72.5%y + 2px - .5px ', 1.5, .725, 'y'),
                 ('20%x+30%x', 0, .5, 'x'), ('1e2px-2.5e1px', 75, 0, 'parent')]
        for expression, absolute, relative, follow in cases:
            with self.subTest(expression=expression):
                self.assertEqual(ui.getSizeDict(expression), {
                    'absoluteValue': absolute, 'relativeValue': relative, 'followType': follow})

    def test_special_dimensions_and_numeric_values(self):
        self.assertIsNone(ui.getSizeDict(' default '))
        self.assertEqual(ui.getSizeDict(' fill '), ui.getSizeDict('100%'))
        self.assertEqual(ui.getSizeDict(-2.5), ui.getSizeDict('-2.5px'))

    def test_invalid_dimensions_fail_instead_of_silently_truncating(self):
        for expression in ('', ' ', '10p', '10x', '10pxjunk', '10px20px', '50%+',
                           '1..2px', '100%+20%x', '10%x+20%y', '1e999px',
                           None, True, float('nan'), float('inf')):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                ui.getSizeDict(expression)

    def test_continuous_slider_clamps_values_and_percentages(self):
        for value, expected in ((-2, 0), (.37, .37), (20, 1)):
            self.assertEqual(ui.getStepedValue(value, 0, 1, 0), expected)
            self.assertEqual(ui.getSliderPercentage(value, 0, 1, 0), expected)
        self.assertEqual(ui.getSliderValue(-1, 0, 10, 0), 0)
        self.assertEqual(ui.getSliderValue(2, 0, 10, 0), 10)

    def test_equal_and_reversed_slider_bounds_and_negative_step(self):
        self.assertEqual(ui.getStepedValue(100, 4, 4, 0), 4)
        self.assertEqual(ui.getSliderPercentage(100, 4, 4, 2), 0)
        self.assertEqual(ui.getSliderValue(.7, 4, 4, 0), 4)
        self.assertEqual(ui.getStepedValue(7, 10, 0, -2), 8)
        self.assertEqual(ui.getSliderPercentage(8, 10, 0, -2), .8)
        self.assertEqual(ui.getSliderValue(.8, 10, 0, -2), 8)

    def test_discrete_slider_stays_on_the_last_valid_step(self):
        self.assertEqual(ui.getStepedValue(20, 0, 10, 3), 9)
        self.assertEqual(ui.getStepedValue(20, 0, 10, 20), 0)
        self.assertAlmostEqual(ui.getStepedValue(.3, 0, .3, .1), .3)
        self.assertAlmostEqual(ui.getSliderValue(1, 0, .3, .1), .3)
        for position in range(101):
            value = ui.getSliderValue(position / 100.0, -1, 1, .1)
            self.assertAlmostEqual(ui.getSliderValue(ui.getSliderPercentage(value, -1, 1, .1), -1, 1, .1), value)

    def test_slider_rejects_nonfinite_and_nonnumeric_parameters(self):
        for invalid in (float('nan'), float('inf'), True, '1', None):
            for index in range(4):
                args = [.5, 0, 1, .1]
                args[index] = invalid
                with self.subTest(invalid=invalid, index=index), self.assertRaises(ValueError):
                    ui.getStepedValue(*args)


if __name__ == '__main__':
    unittest.main()
