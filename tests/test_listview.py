# -*- coding: utf-8 -*-
"""ListView production rendering, Observable transport and native lifecycle."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import test_group_controls as fixture
from custom_ui_fixture import Label

ROOT = Path(__file__).resolve().parents[1]
SCROLL_PATH = '/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content'


class EmptyLabel(Label):
    def SetVisible(self, visible):
        self.visible = visible


class ListViewTests(unittest.TestCase):
    def setUp(self):
        self.fx = fixture.GroupControlTests()
        self.fx.setUp()
        self.ui, self.system = self.fx.ui, self.fx.system
        self.create = self.system.observableManager.create
        descriptors = sys.modules[self.fx.public.__module__.rsplit('.', 1)[0] + '.controls']
        self.fx.server_side = False
        self.fx.public.register('oreui:listview', 'listview.path',
                                descriptors.ListView(itemControl='listview.item'))
        self.fx.server_side = True
        original = self.ui.CreateChildControl

        def create(path, name, parent):
            node = original(path, name, parent)
            if path == 'listview.path':
                node.children['/empty'] = EmptyLabel()
                scroll = fixture.NativeControl(node, node.path + '/content')
                content = fixture.NativeControl(scroll, scroll.path + SCROLL_PATH)
                scroll.children[SCROLL_PATH] = content
                node.children['/content'] = scroll
            elif path == 'listview.item':
                node.children['/button_label'] = Label()
                node.children['/selected'] = fixture.NativeControl(node, node.path + '/selected')
            return node
        self.ui.CreateChildControl = create

    def tearDown(self):
        self.fx.tearDown()

    def form(self, items, value=None, **style):
        return self.fx.make_form(width=400, height=300).listview('物品', items, value, style)

    def state(self, fid, index=0):
        return self.ui._Screen__listViews[fid][index]

    def rows(self, fid, index=0):
        return self.state(fid, index)['rows']

    def click(self, row):
        row.handlers['click']({})

    def selected(self, fid, index=0):
        return [key for row, key in self.rows(fid, index)
                if row.children['/selected'].visible]

    def items(self):
        return [{'label': '苹果', 'value': 'apple/path'}, {'label': '石头', 'value': 7}]

    def test_chain_and_plain_items_are_independent_and_paths_use_indices(self):
        items = self.items()
        form = self.form(items, 7)
        self.assertIs(form.listview('空', []), form)
        items[0]['label'] = 'mutated'
        fid, _ = self.fx.add(form)
        rows = self.rows(fid)
        self.assertEqual(rows[0][0].children['/button_label'].text, '苹果')
        self.assertTrue(rows[0][0].path.endswith('/row_0'))
        self.assertEqual(self.selected(fid), [7])
        self.assertEqual(rows[1][0].GetPosition()[1], 32)
        self.assertEqual(rows[0][0].parent.GetSize()[1], 64)

    def test_dynamic_items_reorder_preserves_selection_and_deletes_old_rows(self):
        items, value = self.create(self.items()), self.create(7)
        fid, _ = self.fx.add(self.form(items, value))
        old = self.rows(fid)[0][0]
        items.setValue(list(reversed(self.items())))
        self.assertEqual([key for row, key in self.rows(fid)], [7, 'apple/path'])
        self.assertEqual(self.selected(fid), [7])
        self.assertIsNot(old, self.rows(fid)[1][0])
        self.click(old)
        self.assertEqual(value.getValue(), 7)
        items.setValue([self.items()[0]])
        self.assertEqual(self.selected(fid), [])
        self.assertEqual(value.getValue(), 7)  # No implicit writeback on data refresh.

    def test_empty_and_repopulate_refresh_empty_hint_and_scroll_extent(self):
        items = self.create(self.items())
        hint = self.create('没有匹配结果')
        fid, _ = self.fx.add(self.form(items, emptyText=hint))
        root = self.ui.getControl(fid, 0)
        items.setValue([])
        self.assertTrue(root.children['/empty'].visible)
        self.assertEqual(root.children['/empty'].text, '没有匹配结果')
        hint.setValue('请添加条目')
        self.assertEqual(root.children['/empty'].text, '请添加条目')
        items.setValue(self.items())
        self.assertFalse(root.children['/empty'].visible)
        self.assertEqual(len(self.rows(fid)), 2)

    def test_selection_only_updates_markers_without_recreating_rows(self):
        value = self.create(None)
        fid, _ = self.fx.add(self.form(self.items(), value))
        original = self.rows(fid)[0][0]
        value.setValue('apple/path')
        self.assertEqual(self.selected(fid), ['apple/path'])
        self.assertIs(self.rows(fid)[0][0], original)
        value.setValue(None)
        self.assertEqual(self.selected(fid), [])

    def test_client_click_writes_binding_once_and_subscriber_receives_new_value(self):
        self.fx.server_side = False
        value = self.create(None)
        seen = []
        value.subscribe(seen.append)
        fid, _ = self.fx.add(self.form(self.items(), value))
        self.click(self.rows(fid)[1][0])
        self.click(self.rows(fid)[1][0])
        self.assertEqual(value.getValue(), 7)
        self.assertEqual(seen, [7])
        self.assertEqual(self.selected(fid), [7])

    def test_server_click_sends_update_and_renders_local_selection(self):
        value = self.create(None)
        fid, _ = self.fx.add(self.form(self.items(), value))
        sent = []
        self.system.NotifyToServer = lambda event, data: sent.append((event, data))
        self.click(self.rows(fid)[0][0])
        self.assertEqual(sent, [('applyObservableUpdate', {'obId': value._id, 'value': 'apple/path'})])
        self.assertEqual(self.selected(fid), ['apple/path'])

    def test_plain_selection_changes_locally_without_network_write(self):
        fid, _ = self.fx.add(self.form(self.items()))
        sent = []
        self.system.NotifyToServer = lambda *args: sent.append(args)
        self.click(self.rows(fid)[1][0])
        self.assertEqual(self.selected(fid), [7])
        self.assertEqual(sent, [])

    def test_updates_before_native_creation_use_latest_data(self):
        items = self.create([])
        form = self.form(items)
        form.show('p1')
        data = self.fx.payloads[-1]
        self.ui.addForm(data)
        items.setValue(self.items())
        self.fx.timers.drain()
        self.assertEqual(len(self.rows(data['formId']['value'])), 2)

    def test_row_height_and_outer_geometry_are_independent(self):
        row_height, outer_height = self.create(24), self.create(150)
        fid, _ = self.fx.add(self.form(self.items(), itemHeight=row_height, height=outer_height))
        row_height.setValue(40)
        self.assertEqual(self.rows(fid)[1][0].GetPosition()[1], 40)
        self.assertEqual(self.rows(fid)[0][0].parent.GetSize()[1], 80)
        self.assertEqual(self.ui.getControl(fid, 0).GetSize()[1], 150)
        outer_height.setValue(200)
        self.assertEqual(self.ui.getControl(fid, 0).GetSize()[1], 200)

    def test_close_clears_native_state_and_late_callbacks(self):
        value = self.create(None)
        fid, _ = self.fx.add(self.form(self.items(), value))
        old = self.rows(fid)[0][0]
        self.fx.close_ui(fid)
        self.assertNotIn(fid, self.ui._Screen__listViews)
        self.click(old)
        value.setValue(7)
        self.assertNotIn(fid, self.ui.forms)

    def test_reentrant_subscriber_can_close_form(self):
        self.fx.server_side = False
        value = self.create(None)
        fid, _ = self.fx.add(self.form(self.items(), value))
        value.subscribe(lambda new: self.fx.close_ui(fid))
        self.click(self.rows(fid)[0][0])
        self.assertNotIn(fid, self.ui.forms)

    def test_group_lists_support_observable_items_and_binding_updates(self):
        items, value = self.create(self.items()), self.create(7)
        self.fx.register('list_group', {'list': {
            'class': 'oreui:listview', 'size': ['100%', 140],
        }})
        form = self.fx.group_form('list_group', {'list': {
            'label': '背包', 'items': items, 'value': value,
        }})
        fid, _ = self.fx.add(form)
        self.assertEqual(self.selected(fid, (0, 'list')), [7])
        items.setValue([])
        self.assertEqual(self.rows(fid, (0, 'list')), [])

    def test_validation_rejects_duplicate_keys_nested_bindings_and_invalid_height(self):
        invalid = [None, {}, [{'label': 'a'}], [{'label': 'a', 'value': True}],
                   [{'label': 'a', 'value': 1}, {'label': 'b', 'value': 1}],
                   [{'label': self.create('a'), 'value': 1}]]
        for items in invalid:
            with self.subTest(items=items), self.assertRaises((TypeError, ValueError)):
                self.form(items)
        for height in (0, -1, float('inf'), float('nan'), '20', True):
            with self.subTest(height=height), self.assertRaises(ValueError):
                self.form([], itemHeight=height)

    def test_invalid_dynamic_data_does_not_partially_replace_native_rows(self):
        items = self.create(self.items())
        fid, _ = self.fx.add(self.form(items))
        old_rows = list(self.rows(fid))
        items.setValue([{'label': 'missing value'}])
        self.assertEqual(self.rows(fid), old_rows)
        items.setValue([])
        self.assertEqual(self.rows(fid), [])

    def test_generated_resources_match_builder_and_all_themes_have_selection(self):
        path = ROOT / 'tools/generate_listview_ui.py'
        spec = importlib.util.spec_from_file_location('listview_builder', path)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        for theme in ('oreui', 'flutter', 'fluent'):
            data = json.loads((ROOT / 'resource/ui' / (theme + '_listviews.json')).read_text(encoding='utf-8'))
            self.assertEqual(data, builder.build(theme))
            for prefix in (('',) if theme == 'oreui' else ('', 'dark_')):
                row = data[prefix + 'listview_item' + ('' if theme == 'oreui' else '@common.button')]
                self.assertTrue(any('selected@fui.w' in child for child in row['controls']))


if __name__ == '__main__':
    unittest.main()
