# -*- coding: utf-8 -*-
"""Exercise production grid creation and Observable updates with UI geometry."""
import copy
import sys
import types
import unittest
import test_form_style as fixture


def dimension(relative=0, absolute=0):
    return {'relativeValue': relative, 'absoluteValue': absolute, 'followType': 'parent'}


class GeometryControl:
    def __init__(self, parent=None, width=400, height=32):
        self.parent = parent
        self.size = {'x': dimension(1) if parent else dimension(absolute=width),
                     'y': dimension(absolute=height)}
        self.position = {'x': dimension(), 'y': dimension()}
        self.children = {}
        self.visible = True

    def GetFullSize(self, axis):
        return dict(self.size[axis])

    def GetFullPosition(self, axis):
        return dict(self.position[axis])

    def SetFullSize(self, axis, value):
        self.size[axis] = dict(value)

    def SetFullPosition(self, axis, value):
        self.position[axis] = dict(value)

    def resolve(self, value, axis):
        follow = value['followType']
        index = 0 if (axis if follow == 'parent' else follow) == 'x' else 1
        parent_size = self.parent.GetSize()[index] if self.parent else 0
        return parent_size * value['relativeValue'] + value['absoluteValue']

    def GetSize(self):
        return tuple(self.resolve(self.size[axis], axis) for axis in ('x', 'y'))

    def GetPosition(self):
        return tuple(self.resolve(self.position[axis], axis) for axis in ('x', 'y'))

    def GetChildByPath(self, path):
        return self.children.get(path)

    def SetVisible(self, value):
        self.visible = value

    def asScrollView(self):
        return self


class GridLayoutTests(unittest.TestCase):
    load_environment = fixture.FormStyleTests.load_environment
    get_players = fixture.FormStyleTests.get_players
    emit = fixture.FormStyleTests.emit
    tearDown = fixture.FormStyleTests.tearDown
    make_form = fixture.FormStyleTests.make_form

    def setUp(self):
        fixture.FormStyleTests.setUp(self)
        self.ui.setSize = types.MethodType(self.screen_class.setSize, self.ui)
        self.ui.setOffset = types.MethodType(self.screen_class.setOffset, self.ui)
        self.ui.setFormContent = types.MethodType(self.screen_class.setFormContent, self.ui)
        self.ui.setButtonProperties = lambda *args: None
        self.control_class = types.SimpleNamespace(typeId='button', path='button.path', options={})
        self.ui.controlManager.get = lambda name: self.control_class

    def create_layout(self, form, viewport_height=10):
        form.show('p1')
        data = self.payloads[-1]
        form_id = data['formId']['value']
        data['basePath'] = '/content'
        self.ui.forms[form_id] = data
        self.ui.observables.extend(data['observables'])
        self.panel = GeometryControl(height=viewport_height)
        self.content = GeometryControl(self.panel, height=viewport_height)
        self.panel.children['/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content'] = self.content
        self.ui.nodes['/panel/fm%s/content' % form_id] = self.panel

        def create(path, name, parent):
            child = GeometryControl(parent)
            parent.children['/' + name] = child
            return child

        self.ui.CreateChildControl = create
        self.ui.setFormContent(form_id, '/content')
        self.controls = [self.content.children['/c%s' % i] for i in range(len(data['controls']))]
        self.form_id = form_id
        return data

    def positions(self):
        return [control.GetPosition() for control in self.controls]

    def test_default_buttons_have_distinct_equal_columns_and_rows(self):
        form = self.make_form(grids=[1, 1])
        for i in range(4):
            form.button(str(i))
        self.create_layout(form)
        self.assertEqual(self.positions(), [(4, 0), (204, 0), (4, 32), (204, 32)])
        self.assertEqual([control.GetSize() for control in self.controls], [(192, 32)] * 4)
        self.assertEqual(self.content.GetSize()[1], 64)

    def test_unequal_columns_and_percentage_offset_use_column_width(self):
        form = self.make_form(grids=[1, 3])
        form.button('a', style={'offsetX': '10%'})
        form.button('b', style={'offsetX': '10%'})
        self.create_layout(form)
        self.assertEqual(self.positions(), [(10, 0), (130, 0)])
        self.assertEqual([control.GetSize()[0] for control in self.controls], [92, 292])

    def test_row_height_includes_y_offset_and_tallest_cell(self):
        form = self.make_form(grids=[1, 1])
        for height, offset in [(20, 10), (40, 0), (12, 5)]:
            form.button('a', style={'height': height, 'offsetY': offset})
        self.create_layout(form)
        self.assertEqual(self.positions(), [(4, 10), (204, 0), (4, 45)])
        self.assertEqual(self.content.GetSize()[1], 57)

    def test_dynamic_height_and_offset_reflow_whole_rows(self):
        height = self.system.observableManager.create(20)
        offset = self.system.observableManager.create(0)
        form = self.make_form(grids=[1, 1])
        form.button('a', style={'height': height, 'offsetY': offset})
        for i in range(3):
            form.button(str(i), style={'height': 20})
        self.create_layout(form)
        height.setValue(30)
        self.assertEqual(self.positions(), [(4, 0), (204, 0), (4, 30), (204, 30)])
        offset.setValue(10)
        self.assertEqual(self.positions(), [(4, 10), (204, 0), (4, 40), (204, 40)])
        self.assertEqual(self.content.GetSize()[1], 60)

    def test_dynamic_width_and_x_offset_keep_column_scaling_and_origin(self):
        width = self.system.observableManager.create('100%-8px')
        offset = self.system.observableManager.create(4)
        form = self.make_form(grids=[1, 1])
        form.button('a').button('b', style={'width': width, 'offsetX': offset})
        self.create_layout(form)
        width.setValue('50%-8px')
        offset.setValue(10)
        self.assertEqual(self.controls[1].GetSize()[0], 92)
        self.assertEqual(self.controls[1].GetPosition(), (210, 0))
        width.setValue('default')
        self.assertEqual(self.controls[1].GetSize()[0], 200)

    def test_hidden_controls_leave_layout_and_restoration_keeps_source_order(self):
        visible = self.system.observableManager.create(True)
        form = self.make_form(grids=[1, 1])
        form.button('a', style={'visible': visible}).button('b').button('c')
        self.create_layout(form)
        visible.setValue(False)
        self.assertFalse(self.controls[0].visible)
        self.assertEqual(self.positions()[1:], [(4, 0), (204, 0)])
        self.assertEqual(self.content.GetSize()[1], 32)
        visible.setValue(True)
        self.assertEqual(self.positions(), [(4, 0), (204, 0), (4, 32)])
        self.assertEqual(self.content.GetSize()[1], 64)

    def test_shared_observable_updates_all_cells_before_relayout(self):
        height = self.system.observableManager.create(20)
        visible = self.system.observableManager.create(True)
        form = self.make_form(grids=[1, 1])
        for i in range(4):
            form.button(str(i), style={'height': height, 'visible': visible})
        self.create_layout(form)
        height.setValue(35)
        self.assertEqual(self.positions(), [(4, 0), (204, 0), (4, 35), (204, 35)])
        visible.setValue(False)
        self.assertTrue(all(not control.visible for control in self.controls))
        self.assertEqual(self.content.GetSize()[1], 10)
        visible.setValue(True)
        self.assertEqual(self.content.GetSize()[1], 70)

    def test_last_cell_updates_and_empty_forms_are_safe(self):
        height = self.system.observableManager.create(20)
        form = self.make_form(grids=[1, 1]).button('a').button('b', style={'height': height})
        self.create_layout(form)
        height.setValue(50)
        self.assertEqual(self.content.GetSize()[1], 50)
        self.ui.moveNextControls(self.form_id, 1)
        self.assertEqual(self.content.GetSize()[1], 50)
        self.create_layout(self.make_form(grids=[1, 1]), viewport_height=100)
        self.ui.moveNextControls(self.form_id, -1)
        self.assertEqual(self.content.GetSize()[1], 100)

    def test_default_dimensions_are_not_mutated_by_repeated_layout(self):
        form = self.make_form(grids=[1, 3])
        form.button('a', style={'width': 'default'}).button('b', style={'width': 'default'})
        data = self.create_layout(form)
        defaults = [copy.deepcopy(control['defaultSize']) for control in data['controls']]
        for i in range(5):
            self.ui.moveNextControls(self.form_id, -1)
        self.assertEqual([control.GetSize()[0] for control in self.controls], [100, 300])
        self.assertEqual([control['defaultSize'] for control in data['controls']], defaults)

    def test_on_create_observes_completed_grid_layout(self):
        observed = []
        self.control_class.options['onCreate'] = lambda args: observed.append(args.control.GetPosition())
        self.create_layout(self.make_form(grids=[1, 1]).button('a').button('b'))
        self.assertEqual(observed, [(4, 0), (204, 0)])

    def test_invalid_weights_are_rejected_when_creating_form(self):
        for grids in ([], [0], [0, 0], [-1, 2], [True], ['1'], [float('nan')],
                      [float('inf')], [1e308, 1e308], [10 ** 1000], None):
            with self.subTest(grids=grids), self.assertRaises(ValueError):
                self.make_form(grids=grids)

    def test_fractional_weights_and_input_copy(self):
        grids = [0.5, 1.5]
        form = self.make_form(grids=grids).button('a').button('b')
        grids[0] = 0
        self.create_layout(form)
        self.assertEqual([control.GetSize()[0] for control in self.controls], [92, 292])
        form = self.make_form(grids=(1, 3)).button('a').button('b')
        self.create_layout(form)
        self.assertEqual(self.positions(), [(4, 0), (104, 0)])

    def test_invalid_client_payload_does_not_register_or_schedule_form(self):
        form = self.make_form()
        form.show('p1')
        data = self.payloads[-1]
        data['style']['grids'] = []
        with self.assertRaises(ValueError):
            self.ui.addForm(data)
        self.assertEqual(self.ui.forms, {})
        self.assertEqual(self.timers.queue, [])


if __name__ == '__main__':
    unittest.main()
