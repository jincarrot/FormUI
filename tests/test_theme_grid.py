# -*- coding: utf-8 -*-
"""Theme ownership and actual window/control geometry through the production API."""
import importlib.util
from pathlib import Path
import sys
import unittest

import test_group_controls as groups
import test_live_form_controls as live
from test_grid_layout import dimension

ROOT = Path(__file__).resolve().parents[1]


class ThemeAndGridApiTests(unittest.TestCase):
    def setUp(self):
        self.fx = groups.GroupControlTests()
        self.fx.setUp()
        self.screen = self.fx.system.screen
        self.form = self.fx.system.formManager.create
        base = self.fx.public.__module__.rsplit('.', 1)[0]
        def load(name):
            spec = importlib.util.spec_from_file_location(base + '.' + name,
                ROOT / 'behavior/scripts/FormUI/interfaces/base' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            self.fx.modules.append(spec.name)
            spec.loader.exec_module(module)
            return module
        self.Theme = load('theme').Theme
        self.Screen = load('screen').Screen
        self.Form = load('form').Form
        self.unwrap = sys.modules[self.fx.prefix + '.utils.type'].unwrapWrappedValue

    def tearDown(self):
        self.fx.tearDown()

    def payload(self, form):
        form.show('p1')
        return self.unwrap(self.fx.payloads[-1])

    def test_custom_theme_inherits_classes_and_merges_style_fields(self):
        self.Theme.register('demo', {'button': {'height': 40}, 'label': 'project:label'}, base='fluent-dark')
        form = self.form('A', theme='demo').button('B').label('C')
        data = self.payload(form)
        self.assertEqual(data['style']['class'], 'fluent:dark_panel')
        self.assertEqual(data['controls'][0]['style']['class'], 'fluent:dark_primary_button')
        self.assertEqual(data['controls'][0]['style']['height'], 40)
        self.assertEqual(data['controls'][1]['style']['class'], 'project:label')

    def test_public_factory_forwards_theme_position_and_layout_on_both_sides(self):
        sys.modules[self.fx.prefix + '.config'].SystemNameServer = 'server'
        self.Theme.register('demo', {})
        self.Screen.setGrid(2, 2)
        for server_side in (True, False):
            self.fx.server_side = server_side
            data = self.payload(self.Form.create('public', theme='demo',
                grid={'row': 1, 'column': 1}, layout={'columns': 3, 'rows': 1}))
            self.assertEqual(data['style']['grid']['row'], 1)
            self.assertEqual(data['style']['layout']['columns'], [1, 1, 1])

    def test_theme_precedence_snapshot_and_inheritance_are_independent(self):
        source = {'button': {'height': 40, 'extra': ['a']}}
        self.Theme.register('parent', source)
        self.Theme.register('child', {'button': {'width': 80}}, base='parent')
        self.screen.setDefaultStyle('button', {'height': 22, 'offsetX': 3})
        form = self.form('A', theme='child')
        source['button']['extra'].append('b')
        self.Theme.get('child')['button']['extra'].append('c')
        self.Theme.register('parent', {'button': {'height': 99}}, replace=True)
        self.Theme.unregister('child')
        form.button('old').button('explicit', style={'height': 50})
        controls = self.payload(form)['controls']
        self.assertEqual(controls[0]['style']['height'], 40)
        self.assertEqual(controls[0]['style']['width'], 80)
        self.assertEqual(controls[0]['style']['offsetX'], 3)
        self.assertEqual(controls[0]['style']['extra'], ['a'])
        self.assertEqual(controls[1]['style']['height'], 50)

    def test_theme_errors_are_atomic_and_builtins_are_immutable(self):
        self.Theme.register('demo', {'button': {'height': 40}})
        invalid = [
            ('demo', {}, 'oreui', False), ('oreui', {}, None, True),
            ('', {}, None, False), ('bad', {'buton': {}}, None, False),
            ('bad', {}, 'missing', False), ('bad', {'button': {'class': ''}}, None, False),
            ('bad', {'button': {'height': float('nan')}}, None, False),
            ('bad', {'button': {'height': self.fx.system.observableManager.create(1)}}, None, False),
        ]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises((TypeError, ValueError)):
                self.Theme.register(*args)
        self.assertEqual(self.Theme.get('demo')['button']['height'], 40)
        self.assertNotIn('bad', self.Theme.names())
        with self.assertRaises(ValueError):
            self.Theme.unregister('fluent')

    def test_default_theme_applies_only_to_new_forms_and_can_be_cleared(self):
        self.Theme.register('demo', {'label': {'fontSize': 1.5}})
        original = self.form('original')
        self.Screen.setDefaultTheme('demo')
        self.assertEqual(self.Screen.getDefaultTheme(), 'demo')
        themed = self.form('themed')
        explicit = self.form('explicit', theme='flutter')
        with self.assertRaises(ValueError):
            self.Theme.unregister('demo')
        with self.assertRaises(ValueError):
            self.Screen.setDefaultTheme('missing')
        self.assertEqual(self.Screen.getDefaultTheme(), 'demo')
        self.Screen.setDefaultTheme()
        self.assertIsNone(self.Screen.getDefaultTheme())
        self.Theme.unregister('demo')
        self.assertEqual(self.payload(themed.label('text'))['controls'][0]['style']['fontSize'], 1.5)
        self.assertEqual(self.payload(original.label('text'))['controls'][0]['style']['fontSize'], 'default')
        self.assertEqual(self.payload(explicit)['style']['class'], 'flutter:light_panel')

    def test_theme_registries_do_not_leak_to_another_screen_manager(self):
        self.Theme.register('demo', {})
        other = self.screen.__class__()
        self.assertNotIn('demo', other.themes.names())
        self.assertIsNone(other.getGrid())

    def test_screen_grid_is_copied_into_each_form_and_clear_preserves_old_form(self):
        columns = [1, 3]
        self.Screen.setGrid(columns, 2, gap=4, padding=8)
        form = self.form('A', grid={'row': 0, 'column': 0})
        columns[0] = 99
        self.Screen.getGrid()['columns'][0] = 55
        self.Screen.clearGrid()
        data = self.payload(form.button('B', grid={'row': 1, 'column': 1}))
        self.assertEqual(data['screenGrid']['columns'], [1, 3])
        self.assertEqual(data['style']['layout']['columns'], [1, 3])
        self.assertEqual(data['style']['width'], '100%')
        self.assertIsNone(self.Screen.getGrid())
        self.assertIsNone(self.payload(self.form('new'))['style']['layout'])

    def test_local_layout_and_legacy_opt_out_do_not_change_global_grid(self):
        self.Screen.setGrid(12, 12)
        local = self.payload(self.form('local', layout={'columns': [1, 2], 'rows': 3}))
        legacy = self.payload(self.form('legacy', layout=False).button('B'))
        grids = self.payload(self.form('columns', {'grids': [1, 2]}))
        self.assertEqual(local['style']['layout']['columns'], [1, 2])
        self.assertIsNone(legacy['style']['layout'])
        self.assertEqual(legacy['controls'][0]['style']['height'], 'default')
        self.assertIsNone(grids['style']['layout'])
        self.assertEqual(len(self.Screen.getGrid()['columns']), 12)

    def test_invalid_grid_configuration_rejected_without_changing_global(self):
        self.Screen.setGrid(2, 3)
        for columns in (0, True, [], [0], [-1], [float('inf')], 257, '12'):
            with self.subTest(columns=columns), self.assertRaises((TypeError, ValueError)):
                self.Screen.setGrid(columns=columns)
        for kwargs in ({'gap': -1}, {'padding': float('nan')}, {'rows': False}):
            with self.assertRaises((TypeError, ValueError)):
                self.Screen.setGrid(**kwargs)
        self.assertEqual(self.Screen.getGrid()['columns'], [1, 1])

    def test_position_validation_and_cell_conflicts_happen_before_show(self):
        with self.assertRaises(ValueError):
            self.form('root', grid={'row': 0, 'column': 0})
        with self.assertRaises(ValueError):
            self.form('plain').button('B', grid={'row': 0, 'column': 0})
        form = self.form('grid', layout={'columns': 2, 'rows': 2})
        for grid in ({}, {'row': 0}, {'row': -1, 'column': 0},
                     {'row': True, 'column': 0}, {'row': 2, 'column': 0},
                     {'row': 0, 'column': 0, 'rowSpan': 0},
                     {'row': 0, 'column': 1, 'columnSpan': 2},
                     {'row': 0, 'column': 0, 'col': 1}):
            with self.subTest(grid=grid), self.assertRaises((TypeError, ValueError)):
                form.label('bad', grid=grid)
        form.label('first', grid={'row': 0, 'column': 0, 'columnSpan': 2})
        with self.assertRaises(ValueError):
            form.label('overlap', grid={'row': 0, 'column': 1})
        form.label('second').label('third')
        with self.assertRaises(ValueError):
            form.label('no room')
        self.assertEqual(len(self.payload(form)['controls']), 3)

    def test_every_control_method_accepts_grid_and_keyword_wins_over_style(self):
        form = self.form('all', layout={'columns': 2, 'rows': 5})
        actions = [
            lambda cell: form.button('B', grid=cell),
            lambda cell: form.toggle('T', True, grid=cell),
            lambda cell: form.label('L', grid=cell),
            lambda cell: form.divider(grid=cell),
            lambda cell: form.slider('S', 1, grid=cell),
            lambda cell: form.textfield('T', '', grid=cell),
            lambda cell: form.dropdown('D', [], None, grid=cell),
            lambda cell: form.listview('L', [], grid=cell),
            lambda cell: form.group(style={'class': 'group'}, grid=cell),
            lambda cell: form.custom(style={'class': 'custom', 'grid': {'row': 99, 'column': 99}}, grid=cell),
        ]
        for index, action in enumerate(actions):
            cell = {'row': index // 2, 'column': index % 2}
            self.assertIs(action(cell), form)
            cell['row'] = 99
        data = self.payload(form)
        self.assertEqual(len(data['controls']), 10)
        self.assertEqual(data['controls'][9]['style']['grid']['row'], 4)


class GridRenderingTests(unittest.TestCase):
    def setUp(self):
        self.fx = groups.GroupControlTests()
        self.fx.setUp()
        self.ui = self.fx.ui
        self.screen = self.fx.system.screen

    def tearDown(self):
        self.fx.tearDown()

    def form(self, layout=None, **style):
        config = {'class': 'root', 'width': 400, 'height': 200}
        config.update(style)
        return self.fx.system.formManager.create('grid', config, layout=layout)

    def control(self, fid, index):
        return self.ui.getControl(fid, index)

    def test_weighted_columns_spans_padding_and_gap_resolve_to_native_pixels(self):
        form = self.form({'columns': [1, 3], 'rows': 2, 'gap': 10, 'padding': 10})
        form.button('wide', style={'class': 'button'}, grid={'row': 1, 'column': 0, 'columnSpan': 2})
        form.button('left', style={'class': 'button'}).button('right', style={'class': 'button'})
        fid, _ = self.fx.add(form)
        controls = [self.control(fid, i) for i in range(3)]
        self.assertEqual([c.GetPosition() for c in controls], [(10, 105), (10, 10), (112.5, 10)])
        self.assertEqual([c.GetSize() for c in controls], [(380, 85), (92.5, 85), (277.5, 85)])
        self.assertTrue(all(c.anchor_from == c.anchor_to == 'top_left' for c in controls))

    def test_window_position_uses_screen_grid_and_local_grid_uses_window_viewport(self):
        self.screen.setGrid(4, 3)
        form = self.fx.system.formManager.create('window', {'class': 'root'},
            grid={'row': 1, 'column': 1, 'columnSpan': 2, 'rowSpan': 2},
            layout={'columns': 2, 'rows': 2})
        form.button('B', style={'class': 'button'}, grid={'row': 1, 'column': 1})
        fid, _ = self.fx.add(form)
        root = self.ui.GetBaseUIControl('/panel/fm%s' % fid)
        self.assertEqual(root.GetPosition(), (100, 100))
        self.assertEqual(root.GetSize(), (200, 200))
        self.assertEqual(self.control(fid, 0).GetPosition(), (100, 100))
        self.assertEqual(self.control(fid, 0).GetSize(), (100, 100))
        self.ui.nodes['/panel'].size['x'] = dimension(absolute=800)
        self.ui.nodes['/panel'].size['y'] = dimension(absolute=600)
        self.ui.Update()
        self.assertEqual(root.GetPosition(), (200, 200))
        self.assertEqual(root.GetSize(), (400, 400))
        self.assertEqual(self.control(fid, 0).GetSize(), (200, 200))

    def test_percent_dimensions_and_observable_offsets_use_cell_dimensions(self):
        width = self.fx.system.observableManager.create('50%')
        offset = self.fx.system.observableManager.create(0)
        form = self.form({'columns': 2, 'rows': 2})
        form.button('B', style={'class': 'button', 'width': width, 'height': '50%x', 'offsetX': offset},
                    grid={'row': 1, 'column': 1})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.control(fid, 0).GetSize(), (100, 100))
        width.setValue('100%-8px')
        offset.setValue(4)
        self.assertEqual(self.control(fid, 0).GetSize(), (192, 100))
        self.assertEqual(self.control(fid, 0).GetPosition(), (204, 100))

    def test_hidden_cells_keep_their_slots_and_on_create_observes_final_geometry(self):
        visible = self.fx.system.observableManager.create(True)
        seen = []
        self.ui.controlManager.get('button').options['onCreate'] = lambda args: seen.append(args.control.GetPosition())
        form = self.form({'columns': 2, 'rows': 1})
        form.button('first', style={'class': 'button', 'visible': visible})
        form.button('second', style={'class': 'button'})
        fid, _ = self.fx.add(form)
        self.assertEqual(seen, [(0, 0), (200, 0)])
        visible.setValue(False)
        self.assertFalse(self.control(fid, 0).visible)
        self.assertEqual(self.control(fid, 1).GetPosition(), (200, 0))
        visible.setValue(True)
        self.assertEqual(self.control(fid, 0).GetPosition(), (0, 0))

    def test_grid_root_observable_geometry_reflows_children(self):
        self.screen.setGrid(2, 1)
        width = self.fx.system.observableManager.create('100%')
        offset = self.fx.system.observableManager.create(0)
        form = self.fx.system.formManager.create('root', {'class': 'root', 'width': width, 'offsetX': offset},
            grid={'row': 0, 'column': 1}, layout={'columns': 2, 'rows': 1})
        form.button('B', style={'class': 'button'}, grid={'row': 0, 'column': 1})
        fid, _ = self.fx.add(form)
        width.setValue('50%')
        offset.setValue(8)
        root = self.ui.GetBaseUIControl('/panel/fm%s' % fid)
        self.assertEqual(root.GetPosition(), (208, 0))
        self.assertEqual(root.GetSize(), (100, 300))
        self.assertEqual(self.control(fid, 0).GetSize(), (50, 300))

    def test_nested_group_grids_use_their_immediate_parent(self):
        self.fx.register('inner', {
            'b': {'class': 'button', 'size': ['100%', '100%'], 'grid': {'row': 1, 'column': 0}},
        })
        self.fx.register('outer', {
            'nested': {'class': 'inner', 'size': ['100%', '100%'],
                       'grid': {'row': 0, 'column': 1}, 'layout': {'columns': 1, 'rows': 2}},
            'label': {'class': 'label', 'size': ['100%', '100%']},
        })
        form = self.form().group(style={'class': 'outer', 'width': 400, 'height': 200,
                                       'offsetX': 0, 'layout': {'columns': 2, 'rows': 1}})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.control(fid, (0, 'nested')).GetPosition(), (200, 0))
        self.assertEqual(self.control(fid, (0, 'nested', 'b')).GetPosition(), (0, 100))
        self.assertEqual(self.control(fid, (0, 'nested', 'b')).GetSize(), (200, 100))
        self.assertEqual(self.control(fid, (0, 'label')).GetPosition(), (0, 0))

    def test_group_keyword_position_wins_and_group_percent_resize_reflows_children(self):
        self.fx.register('group', {
            'b': {'class': 'button', 'size': ['100%', '100%'], 'grid': {'row': 0, 'column': 1}},
        })
        form = self.form({'columns': 2, 'rows': 1})
        form.group(style={'class': 'group', 'grid': {'row': 0, 'column': 0},
                          'layout': {'columns': 2, 'rows': 1}},
                   grid={'row': 0, 'column': 1})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.control(fid, 0).GetPosition(), (200, 0))
        self.assertEqual(self.control(fid, (0, 'b')).GetSize(), (100, 200))
        # A separate legacy form containing a grid Group still tracks parent resizing.
        legacy = self.form(width='100%').group(style={
            'class': 'group', 'width': '100%', 'height': 100, 'offsetX': 0,
            'layout': {'columns': 2, 'rows': 1},
        })
        other, _ = self.fx.add(legacy)
        self.ui.nodes['/panel'].size['x'] = dimension(absolute=800)
        self.ui.Update()
        self.assertEqual(self.control(other, (0, 'b')).GetSize(), (400, 100))

    def test_default_offset_without_native_position_is_zero_in_grid(self):
        original = self.ui.CreateChildControl
        def create(path, name, parent):
            control = original(path, name, parent)
            if not name.startswith('fm'):
                control.GetFullPosition = lambda axis: None
            return control
        self.ui.CreateChildControl = create
        form = self.form({'columns': 2, 'rows': 1})
        form.button('B', style={'class': 'button', 'offsetX': 'default', 'offsetY': 'default'},
                    grid={'row': 0, 'column': 1})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.control(fid, 0).GetPosition(), (200, 0))

    def test_group_without_parent_grid_rejects_child_position_before_scheduling(self):
        self.fx.register('bad', {'b': {'class': 'button', 'grid': {'row': 0, 'column': 0}}})
        with self.assertRaises(ValueError):
            self.fx.add(self.form().group(style={'class': 'bad'}))
        self.assertEqual(self.ui.forms, {})
        self.assertEqual(self.fx.timers.queue, [])

    def test_small_viewport_clamps_cells_instead_of_negative_sizes(self):
        form = self.form({'columns': 2, 'rows': 2, 'gap': 100, 'padding': 100}, width=40, height=30)
        form.button('B', style={'class': 'button'}, grid={'row': 1, 'column': 1})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.control(fid, 0).GetSize(), (0, 0))
        self.assertEqual(self.control(fid, 0).GetPosition(), (20, 15))

    def test_bad_received_grid_does_not_register_form_or_schedule_timers(self):
        form = self.form({'columns': 2, 'rows': 2}).button(
            'B', style={'class': 'button'}, grid={'row': 0, 'column': 0})
        form.show('p1')
        data = self.fx.payloads[-1]
        data['controls'][0]['style']['grid']['row']['value'] = 9
        with self.assertRaises(ValueError):
            self.ui.addForm(data)
        self.assertEqual(self.ui.forms, {})
        self.assertEqual(self.fx.timers.queue, [])


class LiveGridTests(unittest.TestCase):
    def setUp(self):
        self.fx = live.LiveFormControlTests()
        self.fx.setUp()

    def tearDown(self):
        self.fx.tearDown()

    def test_live_and_pending_appends_reserve_explicit_cells_and_relayout(self):
        form = self.fx.system.formManager.create('live', {'class': 'root', 'width': 400, 'height': 200},
                                                 layout={'columns': 2, 'rows': 2})
        form.button('auto', style={'class': 'button'})
        form.show('p1')
        self.fx.ui.addForm(self.fx.payloads[-1])
        form.button('pending', style={'class': 'button'}, grid={'row': 0, 'column': 0})
        self.fx.timers.drain()
        fid = self.fx.events[0][1]['formId']['value']
        self.assertEqual(self.fx.ui.getControl(fid, 0).GetPosition(), (200, 0))
        form.button('live', style={'class': 'button'}, grid={'row': 1, 'column': 1})
        self.assertEqual(self.fx.ui.getControl(fid, 2).GetPosition(), (200, 100))
        previous = len(self.fx.events)
        with self.assertRaises(ValueError):
            form.button('overlap', style={'class': 'button'}, grid={'row': 0, 'column': 0})
        self.assertEqual(len(self.fx.events), previous)


if __name__ == '__main__':
    unittest.main()
