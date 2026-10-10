# -*- coding: utf-8 -*-
"""Multi-form input caches and polling cleanup without the game runtime."""
import sys
import types
import unittest
import test_grid_layout as fixture


class NativeInput:
    def __init__(self, path):
        self.path = path
        self.value = 0
        self.text = ''
        self.toggle = False

    def asSlider(self):
        return self

    asLabel = asTextEditBox = asSwitchToggle = asSlider

    def SetSliderValue(self, value):
        self.value = value

    def GetSliderValue(self):
        return self.value

    def SetEditText(self, text):
        self.text = text

    def GetEditText(self):
        return self.text

    def SetText(self, text):
        self.text = text

    def SetToggleState(self, value, path):
        self.toggle = value

    def GetToggleState(self, path):
        return self.toggle

    def GetPath(self):
        return self.path


class ControlUpdateTests(unittest.TestCase):
    load_environment = fixture.GridLayoutTests.load_environment
    get_players = fixture.GridLayoutTests.get_players
    emit = fixture.GridLayoutTests.emit
    tearDown = fixture.GridLayoutTests.tearDown
    make_form = fixture.GridLayoutTests.make_form
    create_layout = fixture.GridLayoutTests.create_layout

    def setUp(self):
        fixture.GridLayoutTests.setUp(self)
        self.ui.setToggleProperties = lambda *args: None
        self.ui.setSliderProperties = lambda *args: None
        self.ui.setTextfieldProperties = lambda *args: None
        self.control_class.options.update({'togglePath': '/toggle', 'sliderPath': '/slider',
                                          'textfieldPath': '/field', 'valuePaths': ['/value'],
                                          'labelPaths': ['/label']})
        self.notifications = []
        self.system.NotifyToServer = lambda event, data: self.notifications.append((event, data))
        prefix = self.observable_class.__module__.split('.general')[0]
        self.util = sys.modules[prefix + '.utils.ui']

    def bind_input(self, form, kind):
        self.control_class.typeId = kind
        data = self.create_layout(form)
        form_id = data['formId']['value']
        self.ui._Screen__formOrder.append(form_id)
        path = '/panel/fm%s/content/c0/slider' % form_id
        native = NativeInput(path)
        root = self.controls[0]
        root.children.update({'/slider': native, '/field': native,
                              '/value': native, '/label': native})
        root.asSwitchToggle = lambda: native
        self.ui.nodes[path[:path.rfind('/')] + '/value'] = native
        record = {'control': native, 'formId': form_id, 'index': 0}
        control = data['controls'][0]
        if kind == 'toggle':
            native.toggle = control['state']['value']
            record.update(value=native.toggle, path='/toggle')
            self.ui.toggles.append(record)
        elif kind == 'textfield':
            native.text = control['value']['value']
            record['value'] = native.text
            self.ui.textfields.append(record)
        else:
            for field in ('value', 'minValue', 'maxValue', 'step'):
                record[field] = control[field]['value']
            record['valuePaths'] = ['/value']
            native.value = self.util.getSliderPercentage(record['value'], record['minValue'],
                                                        record['maxValue'], record['step'])
            self.ui.sliders.append(record)
        return form_id, record, native

    def test_toggle_cache_matches_form_and_index(self):
        first = self.system.observableManager.create(False)
        second = self.system.observableManager.create(False)
        _, first_cache, first_native = self.bind_input(self.make_form().toggle('a', first), 'toggle')
        _, second_cache, second_native = self.bind_input(self.make_form().toggle('b', second), 'toggle')
        second.setValue(True)
        self.assertFalse(first_cache['value'])
        self.assertFalse(first_native.toggle)
        self.assertTrue(second_cache['value'])
        self.assertTrue(second_native.toggle)
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_textfield_cache_matches_form_and_index(self):
        first = self.system.observableManager.create('first')
        second = self.system.observableManager.create('second')
        _, first_cache, first_native = self.bind_input(self.make_form().textfield('a', first), 'textfield')
        _, second_cache, second_native = self.bind_input(self.make_form().textfield('b', second), 'textfield')
        second.setValue('changed')
        self.assertEqual((first_cache['value'], first_native.text), ('first', 'first'))
        self.assertEqual((second_cache['value'], second_native.text), ('changed', 'changed'))
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_slider_value_and_range_caches_match_form_and_index(self):
        first = self.system.observableManager.create(10)
        second = self.system.observableManager.create(20)
        minimum = self.system.observableManager.create(0)
        maximum = self.system.observableManager.create(100)
        step = self.system.observableManager.create(1)
        _, first_cache, _ = self.bind_input(self.make_form().slider('a', first, 0, 100, 1), 'slider')
        _, second_cache, native = self.bind_input(self.make_form().slider('b', second, minimum, maximum, step), 'slider')
        minimum.setValue(2)
        maximum.setValue(90)
        step.setValue(2)
        second.setValue(42)
        fields = ('value', 'minValue', 'maxValue', 'step')
        self.assertEqual([first_cache[field] for field in fields], [10, 0, 100, 1])
        self.assertEqual([second_cache[field] for field in fields], [42, 2, 90, 2])
        self.assertAlmostEqual(native.value, 40.0 / 88)
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_shared_binding_updates_each_forms_cache(self):
        state = self.system.observableManager.create(False)
        _, first_cache, _ = self.bind_input(self.make_form().toggle('a', state), 'toggle')
        _, second_cache, _ = self.bind_input(self.make_form().toggle('b', state), 'toggle')
        state.setValue(True)
        self.assertTrue(first_cache['value'])
        self.assertTrue(second_cache['value'])
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_slider_range_updates_refresh_clamped_value_label_and_cache_together(self):
        value = self.system.observableManager.create(80)
        maximum = self.system.observableManager.create(100)
        step = self.system.observableManager.create(1)
        _, record, native = self.bind_input(self.make_form().slider('a', value, 0, maximum, step), 'slider')
        maximum.setValue(30)
        self.assertEqual(record['value'], 30)
        self.assertEqual(float(native.text), 30)
        self.assertEqual(native.value, 1)
        self.ui.Update()
        self.assertEqual(self.notifications, [])
        self.assertEqual(value.getValue(), 80)
        step.setValue(0)
        value.setValue(12.5)
        self.assertEqual(record['value'], 12.5)
        self.assertEqual(float(native.text), 12.5)
        self.assertAlmostEqual(native.value, 12.5 / 30)
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_shared_slider_binding_is_applied_before_projection(self):
        shared = self.system.observableManager.create(20)
        _, record, native = self.bind_input(self.make_form().slider('a', shared, 0, shared, 0), 'slider')
        shared.setValue(40)
        self.assertEqual((record['value'], record['maxValue'], native.value), (40, 40, 1))
        self.ui.Update()
        self.assertEqual(self.notifications, [])

    def test_close_removes_all_polling_records_and_keeps_other_forms(self):
        closed = self.system.observableManager.create(False)
        live = self.system.observableManager.create(False)
        first_id, _, _ = self.bind_input(self.make_form().toggle('closed', closed), 'toggle')
        second_id, live_cache, live_native = self.bind_input(self.make_form().toggle('live', live), 'toggle')
        for records in (self.ui.sliders, self.ui.textfields):
            records.append({'formId': first_id, 'index': 0})
        original_toggles = self.ui.toggles
        self.ui.onClose({'AddTouchEventParams': {'formId': first_id}})
        self.assertIs(self.ui.toggles, original_toggles)
        self.assertEqual(self.ui.sliders, [])
        self.assertEqual(self.ui.textfields, [])
        self.assertEqual(self.ui.toggles, [live_cache])
        self.assertNotIn(closed._id, self.ui.observables)
        self.assertIn(live._id, self.ui.observables)
        live_native.toggle = True
        self.ui.Update()
        self.assertEqual(self.notifications[-1], ('applyObservableUpdate', {'obId': live._id, 'value': True}))
        self.ui.onClose({'AddTouchEventParams': {'formId': second_id}})
        self.assertEqual(self.ui.toggles, [])
        self.assertEqual(self.ui.observables, [])

    def test_closing_one_form_keeps_shared_observable_registered(self):
        state = self.system.observableManager.create(False)
        first_id, _, _ = self.bind_input(self.make_form().toggle('a', state), 'toggle')
        _, cache, native = self.bind_input(self.make_form().toggle('b', state), 'toggle')
        self.ui.onClose({'AddTouchEventParams': {'formId': first_id}})
        state.setValue(True)
        self.assertTrue(cache['value'])
        self.assertTrue(native.toggle)


if __name__ == '__main__':
    unittest.main()
