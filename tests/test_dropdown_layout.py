"""Dropdown scroll extent in grid cells and root default geometry restoration."""
import unittest
import test_grid_layout as grid
import test_custom_controls as custom
from custom_ui_fixture import Label


class DropdownLayoutTests(unittest.TestCase):
    load_environment = grid.GridLayoutTests.load_environment
    get_players = grid.GridLayoutTests.get_players
    emit = grid.GridLayoutTests.emit
    tearDown = grid.GridLayoutTests.tearDown
    make_form = grid.GridLayoutTests.make_form
    create_layout = grid.GridLayoutTests.create_layout

    def setUp(self):
        grid.GridLayoutTests.setUp(self)
        self.ui.setDropdownProperties = lambda *args: None
        self.control_class.typeId = 'dropdown'
        self.control_class.options.update(dropdownPath='/box', contentPath='/items', boxLabelPaths=['/label'])

    def menu(self, index, height=80):
        root = self.controls[index]
        box = grid.GeometryControl(root)
        box.children['/label'] = Label()
        items = grid.GeometryControl(root, height=height)
        items.position['y'] = grid.dimension(absolute=15)
        items.visible = False
        root.children.update({'/box': box, '/items': items})
        root.children['/box/label'] = box.children['/label']
        return box, items

    def make_dropdowns(self, count=6, **style):
        form = self.make_form(grids=[1, 1])
        for index in range(count):
            options = {'height': 20}
            options.update(style if index == 1 else {})
            form.dropdown(str(index), [], 0, options)
        return form

    def test_menu_uses_actual_bottom_in_both_columns(self):
        self.create_layout(self.make_dropdowns())
        for index in (0, 1):
            box, items = self.menu(index)
            self.ui.onDropdownBoxClick(self.form_id, index)
            self.assertEqual(self.content.GetSize()[1], 95)
            self.assertFalse(box.visible)
            self.assertTrue(items.visible)
            self.assertEqual(self.controls[2].GetPosition()[1], 20)
            self.ui.onDropdownItemClick(self.form_id, index, 1, 'selected')
            self.assertEqual(self.content.GetSize()[1], 60)
            self.assertTrue(box.visible)
            self.assertFalse(items.visible)
            self.assertNotIn('dropdown', self.ui.forms[self.form_id])
            self.assertEqual(self.ui.forms[self.form_id]['controls'][index]['value']['value'], 1)

    def test_menu_within_existing_rows_needs_no_extra_scroll_height(self):
        self.create_layout(self.make_dropdowns(height=100))
        self.menu(1, height=30)
        before = self.content.GetSize()[1]
        self.ui.onDropdownBoxClick(self.form_id, 1)
        self.assertEqual(self.content.GetSize()[1], before)
        self.ui.onDropdownItemClick(self.form_id, 1, 1, 'selected')
        self.assertNotIn('dropdown', self.ui.forms[self.form_id])

    def test_switching_menus_and_relayout_do_not_accumulate_height(self):
        offset = self.system.observableManager.create(0)
        self.create_layout(self.make_dropdowns(offsetY=offset))
        first_box, first_items = self.menu(0, 150)
        self.menu(1)
        self.ui.onDropdownBoxClick(self.form_id, 0)
        self.assertEqual(self.content.GetSize()[1], 165)
        self.ui.onDropdownBoxClick(self.form_id, 1)
        self.assertTrue(first_box.visible)
        self.assertFalse(first_items.visible)
        self.assertEqual(self.content.GetSize()[1], 95)
        offset.setValue(10)
        self.assertEqual(self.content.GetSize()[1], 105)
        self.ui._relayoutForm(self.form_id)
        self.assertEqual(self.content.GetSize()[1], 105)

    def test_hiding_open_menu_restores_extent_and_clears_state(self):
        visible = self.system.observableManager.create(True)
        self.create_layout(self.make_dropdowns(visible=visible))
        box, items = self.menu(1, 150)
        self.ui.onDropdownBoxClick(self.form_id, 1)
        visible.setValue(False)
        self.assertFalse(items.visible)
        self.assertTrue(box.visible)
        self.assertNotIn('dropdown', self.ui.forms[self.form_id])
        self.assertEqual(self.content.GetSize()[1], 60)


class RootGeometryTests(unittest.TestCase):
    load_environment = custom.CustomControlTests.load_environment
    get_players = custom.CustomControlTests.get_players
    emit = custom.CustomControlTests.emit
    tearDown = custom.CustomControlTests.tearDown
    make_form = custom.CustomControlTests.make_form
    add = custom.CustomControlTests.add
    close_ui = custom.CustomControlTests.close_ui
    setUp = custom.CustomControlTests.setUp

    def tick(self):
        for _ in range(10):
            self.ui.Update()

    def test_default_restoration_after_new_values_cancels_previous_transitions(self):
        width = self.system.observableManager.create(150)
        height = self.system.observableManager.create(120)
        offset = self.system.observableManager.create(10)
        fid, data = self.add(self.make_form(width=width, height=height, offsetX=offset, offsetY=offset))
        root = self.ui.GetBaseUIControl('/panel/fm%s' % fid)
        self.assertEqual(root.GetSize(), (150, 120))
        self.assertEqual(root.GetPosition(), (10, 10))
        width.setValue(200)
        height.setValue(180)
        offset.setValue(20)
        width.setValue('default')
        height.setValue('default')
        offset.setValue('default')
        self.tick()
        self.assertEqual(root.GetSize(), (400, 200))
        self.assertEqual(root.GetPosition(), (0, 0))
        self.assertEqual(data['defaultSize'][1]['absoluteValue'], 200)
        scroll = root.GetChildByPath('/content')
        content = next(iter(scroll.children.values()))
        self.assertEqual(content.GetSize()[1], 200)

    def test_default_handles_native_missing_offset_and_follow_fields(self):
        original = self.ui.CreateChildControl
        def create(path, name, parent):
            root = original(path, name, parent)
            if name.startswith('fm'):
                get_size = root.GetFullSize
                root.GetFullSize = lambda axis: {key: value for key, value in get_size(axis).items() if key != 'followType'}
                get_position = root.GetFullPosition
                root.GetFullPosition = lambda axis: get_position(axis) if root.GetPosition() != (0, 0) else None
            return root
        self.ui.CreateChildControl = create
        width = self.system.observableManager.create(100)
        offset = self.system.observableManager.create(5)
        fid, data = self.add(self.make_form(width=width, height=100, offsetX=offset, offsetY=offset))
        self.assertEqual(data['defaultOffset'], (None, None))
        width.setValue('default')
        offset.setValue('default')
        # Call directly as well, so an exception cannot be hidden by Observable dispatch.
        self.ui._applyFormObservableUpdate(fid, width._id, 'default')
        self.ui._applyFormObservableUpdate(fid, offset._id, 'default')
        self.tick()
        root = self.ui.GetBaseUIControl('/panel/fm%s' % fid)
        self.assertEqual(root.GetSize()[0], 400)
        self.assertEqual(root.GetPosition(), (0, 0))


if __name__ == '__main__':
    unittest.main()
