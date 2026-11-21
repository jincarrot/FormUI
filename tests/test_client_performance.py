"""Regression checks for unnecessary native calls and cache lifetime."""
import sys
import unittest
from unittest.mock import patch

import test_group_controls as groups
import test_listview as lists
import test_client_observable_delivery as delivery
from test_grid_layout import GeometryControl, dimension


class ClientPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.fx = groups.GroupControlTests()
        self.fx.setUp()
        self.ui = self.fx.ui
        self.create = self.fx.system.observableManager.create

    def tearDown(self):
        self.fx.tearDown()

    def test_idle_sliders_do_not_rewrite_labels_but_native_input_is_polled_each_frame(self):
        value = self.create(50)
        fid, _ = self.fx.add(self.fx.make_form().slider('slider', value, 0, 100, 1, {'class': 'slider'}))
        native = self.ui.getControl(fid, 0)
        label = native.children['/value']
        screen_module = sys.modules[self.fx.prefix + '.client.ui.screen']
        with patch.object(label, 'SetText', wraps=label.SetText) as write, \
                patch.object(native, 'GetSliderValue', wraps=native.GetSliderValue) as read, \
                patch.object(screen_module, 'getSliderValue', wraps=screen_module.getSliderValue) as convert:
            for frame in range(60):
                self.ui.Update()
            self.assertEqual(write.call_count, 0)
            self.assertEqual(read.call_count, 60)
            self.assertEqual(convert.call_count, 0)
            native.slider = .7
            self.ui.Update()
            self.assertEqual(write.call_count, 1)
            self.assertEqual(convert.call_count, 1)
            self.assertEqual(float(label.text), 70)
            self.ui.Update()
            self.assertEqual(write.call_count, 1)

    def test_non_grid_static_controls_do_not_participate_in_frame_layout(self):
        form = self.fx.make_form()
        for index in range(100):
            form.label(str(index), {'class': 'label', 'height': 20})
        self.fx.add(form)
        with patch.object(self.ui, 'getControl', side_effect=AssertionError('idle tree traversal')), \
                patch.object(self.ui, '_relayoutForm') as layout:
            for frame in range(30):
                self.ui.Update()
        layout.assert_not_called()

    def test_legacy_relayout_does_not_reread_cached_template_geometry(self):
        fid, _ = self.fx.add(self.fx.make_form().button('button', style={'class': 'button'}))
        native = self.ui.getControl(fid, 0)
        with patch.object(native, 'GetFullSize', wraps=native.GetFullSize) as size, \
                patch.object(native, 'GetFullPosition', wraps=native.GetFullPosition) as position:
            self.ui._relayoutForm(fid)
        # One origin read per axis is required by the geometry setter; no default reads.
        self.assertEqual(size.call_count, 2)
        self.assertEqual(position.call_count, 2)

    def test_loading_indicator_only_changes_visibility_when_state_changes(self):
        node = GeometryControl()
        self.ui.nodes['/pre_screen'] = node
        with patch.object(node, 'SetVisible', wraps=node.SetVisible) as write:
            for frame in range(10):
                self.ui.Update()
            self.assertEqual(write.call_count, 1)
            form = self.fx.make_form()
            form.show('p1')
            self.ui.addForm(self.fx.payloads[-1])
            self.ui.Update()
            self.assertTrue(node.visible)
            self.fx.timers.drain()
            self.ui.Update()
            self.assertFalse(node.visible)
            self.assertEqual(write.call_count, 3)

    def test_label_notification_does_not_relayout_groups_or_scan_other_controls(self):
        text = self.create('old')
        self.fx.register('group', {'text': {'class': 'label', 'size': ['100%', 20]}})
        form = self.fx.group_form(children={'text': {'label': text}})
        for index in range(100):
            form.label(str(index), {'class': 'label'})
        fid, _ = self.fx.add(form)
        screen_module = sys.modules[self.fx.prefix + '.client.ui.screen']
        with patch.object(screen_module, 'iterControls', side_effect=AssertionError('full tree walk')), \
                patch.object(self.ui, '_layoutGroups') as groups_layout, \
                patch.object(self.ui, '_relayoutForm') as layout:
            text.setValue('new')
        layout.assert_not_called()
        groups_layout.assert_not_called()
        self.assertEqual(self.ui.getControl(fid, (0, 'text')).children['/label'].text, 'new')

    def test_notification_only_visits_forms_bound_to_that_observable(self):
        first, second = self.create('first'), self.create('second')
        ids = []
        for value in (first, second):
            fid, _ = self.fx.add(self.fx.make_form().label(value, {'class': 'label'}))
            ids.append(fid)
        with patch.object(self.ui, '_applyFormObservableUpdate', wraps=self.ui._applyFormObservableUpdate) as update:
            second.setValue('updated')
        self.assertEqual([call.args[0] for call in update.call_args_list], [ids[1]])
        self.assertEqual(self.ui.getControl(ids[0], 0).children['/label'].text, 'first')
        self.assertEqual(self.ui.getControl(ids[1], 0).children['/label'].text, 'updated')

    def test_grid_resize_reuses_plan_and_updates_actual_geometry(self):
        self.fx.system.screen.setGrid(2, 1)
        form = self.fx.system.formManager.create('grid', {'class': 'root'},
            grid={'row': 0, 'column': 1}, layout={'columns': 2, 'rows': 1})
        form.label('label', {'class': 'label'}, grid={'row': 0, 'column': 1})
        fid, _ = self.fx.add(form)
        module = sys.modules[self.fx.prefix + '.client.ui.grid']
        with patch.object(module, 'planCells', side_effect=AssertionError('recompiled static grid')):
            self.ui.Update()
            self.ui.nodes['/panel'].size['x'] = dimension(absolute=800)
            self.ui.Update()
        self.assertEqual(self.ui.getControl(fid, 0).GetPosition(), (200, 0))
        self.assertEqual(self.ui.getControl(fid, 0).GetSize()[0], 200)

    def test_moving_grid_window_does_not_relayout_content(self):
        self.fx.system.screen.setGrid(2, 1)
        offset = self.create(0)
        form = self.fx.system.formManager.create('grid', {'class': 'root', 'offsetX': offset},
                                                 grid={'row': 0, 'column': 1})
        form.label('text', {'class': 'label'})
        fid, _ = self.fx.add(form)
        with patch.object(self.ui, '_relayoutForm') as layout, patch.object(self.ui, '_layoutGroups') as groups_layout:
            offset.setValue(10)
        layout.assert_not_called()
        groups_layout.assert_not_called()
        self.assertEqual(self.ui.GetBaseUIControl('/panel/fm%s' % fid).GetPosition()[0], 210)

    def test_closing_releases_binding_input_and_grid_cache_references(self):
        value = self.create('x')
        form = self.fx.system.formManager.create('grid', {'class': 'root'}, layout={'columns': 2})
        form.textfield('field', value, {'class': 'textfield'})
        fid, _ = self.fx.add(form)
        self.fx.close_ui(fid)
        self.assertNotIn(fid, self.ui._formBindings)
        self.assertNotIn(value._id, self.ui._observableForms)
        self.assertNotIn(fid, self.ui._gridPlans)
        self.assertNotIn(fid, self.ui._gridWatches)
        self.assertEqual(self.ui._Screen__inputRecords, {})
        self.ui.Update()

    def test_repeat_tasks_run_linearly_and_new_tasks_wait_until_next_frame(self):
        seen = []
        def first():
            seen.append('first')
            self.ui.addRepeatFunc(lambda: seen.append('new'), 1)
        self.ui.addRepeatFunc(first, 1)
        self.ui.addRepeatFunc(lambda: seen.append('second'), 2)
        self.ui.Update()
        self.assertEqual(seen, ['first', 'second'])
        self.ui.Update()
        self.assertEqual(seen, ['first', 'second', 'second', 'new'])
        self.assertEqual(self.ui._Screen__repeatFuncs, [])

    def test_failing_repeat_task_expires_without_blocking_other_tasks(self):
        calls, seen = [], []
        def fail():
            calls.append(1)
            raise RuntimeError('failed native operation')
        self.ui.addRepeatFunc(fail, 2)
        self.ui.addRepeatFunc(lambda: seen.append(True), 2)
        for frame in range(5):
            self.ui.Update()
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(seen), 2)
        self.assertEqual(self.ui._Screen__repeatFuncs, [])

    def test_failing_input_does_not_skip_other_inputs(self):
        fid, _ = self.fx.add(self.fx.make_form().toggle('bad', False, {'class': 'toggle'})
                             .slider('good', 0, 0, 100, 1, {'class': 'slider'}))
        toggle, slider = self.ui.getControl(fid, 0), self.ui.getControl(fid, 1)
        slider.slider = .5
        with patch.object(toggle, 'GetToggleState', side_effect=RuntimeError('unavailable')):
            self.ui.Update()
        self.assertEqual(float(slider.children['/value'].text), 50)

    def test_synchronous_input_subscriber_can_close_form_without_skipping_another(self):
        self.fx.server_side = False
        value = self.create(False)
        first = self.fx.make_form().toggle('close', value, {'class': 'toggle'})
        one, _ = self.fx.add(first)
        two, _ = self.fx.add(self.fx.make_form().toggle('other', False, {'class': 'toggle'}))
        value.subscribe(lambda new: self.fx.close_ui(one))
        self.ui.getControl(one, 0).toggle = True
        self.ui.getControl(two, 0).toggle = True
        self.ui.Update()
        self.assertNotIn(one, self.ui.forms)
        self.assertTrue(self.ui.forms[two]['controls'][0]['state']['value'])

    def test_sync_range_update_during_input_is_not_overwritten_by_poll_cache(self):
        self.fx.server_side = False
        value, maximum = self.create(0), self.create(100)
        fid, _ = self.fx.add(self.fx.make_form().slider('value', value, 0, maximum, 1, {'class': 'slider'}))
        value.subscribe(lambda new: maximum.setValue(25))
        self.ui.getControl(fid, 0).slider = .5
        self.ui.Update()
        self.assertEqual(self.ui.sliders[0]['value'], 25)
        self.assertEqual(float(self.ui.getControl(fid, 0).children['/value'].text), 25)

    def test_wrapped_binding_aliases_keep_the_original_old_value(self):
        module = sys.modules[self.fx.prefix + '.utils.bindings']
        shared = {'type': 'Observable', 'obId': 1, 'value': 'old'}
        index = module.WrappedBindings({'first': shared, 'second': shared})
        previous = index.update(1, 'new')
        self.assertEqual(previous, {id(shared): 'old'})
        self.assertEqual(shared['value'], 'new')

    def test_group_reregistration_discards_old_definition_dependencies(self):
        first, second = self.create(10), self.create(20)
        self.fx.register('group', {'label': {'class': 'label', 'height': first}})
        old = self.ui.controlManager.get('group').options['controls']['label']['height']
        self.fx.register('group', {'label': {'class': 'label', 'height': second}})
        first.setValue(99)
        self.assertEqual(old['value'], 10)
        second.setValue(30)
        current = self.ui.controlManager.get('group').options['controls']['label']['height']
        self.assertEqual(current['value'], 30)


class ListViewPerformanceTests(unittest.TestCase):
    def test_changing_selection_touches_only_old_and_new_rows(self):
        fx = lists.ListViewTests()
        fx.setUp()
        try:
            selected = fx.create(0)
            fid, _ = fx.fx.add(fx.form([{'label': str(i), 'value': i} for i in range(1000)], selected))
            marker_type = type(fx.rows(fid)[0][0].children['/selected'])
            original = marker_type.SetVisible
            with patch.object(marker_type, 'SetVisible', autospec=True, side_effect=original) as write:
                selected.setValue(999)
                self.assertEqual(write.call_count, 2)
                self.assertEqual(fx.selected(fid), [999])
                selected.setValue(None)
                self.assertEqual(write.call_count, 3)
                self.assertEqual(fx.selected(fid), [])
                fx.click(fx.rows(fid)[100][0])
                self.assertEqual(write.call_count, 4)
                self.assertEqual(fx.selected(fid), [100])
        finally:
            fx.tearDown()

    def test_pending_unprepared_group_items_keep_receiving_updates(self):
        fx = delivery.ClientObservableDeliveryTests()
        fx.setUp()
        try:
            items = fx.system.observableManager.create([{'label': 'one', 'value': 1}])
            form = fx.make_form().group({'list': {'items': items}}, {'class': 'registered_later'})
            form.show('p1')
            payload = fx.payloads[-1]
            fx.top = None
            fx.client.showForm(payload)
            items.setValue([{'label': 'two', 'value': 2}])
            self.assertEqual(payload['controls'][0]['children']['list']['items']['value'],
                             [{'label': 'two', 'value': 2}])
        finally:
            fx.tearDown()


if __name__ == '__main__':
    unittest.main()
