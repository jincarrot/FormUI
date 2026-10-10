# -*- coding: utf-8 -*-
"""Registered group composition, native geometry, bindings and routing."""
import importlib.util
import sys
import unittest
from pathlib import Path
import test_custom_controls as custom_fixture

from test_grid_layout import GeometryControl
from custom_ui_fixture import Label


class NativeControl(GeometryControl):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.path = path
        self.children = {'/label': Label(), '/value': Label()}
        self.slider = 0.0
        self.toggle = False
        self.text = ''
        self.handlers = {}

    def GetChildByPath(self, path):
        if not path:
            return self
        if path in self.children:
            return self.children[path]
        name, _, remaining = path.lstrip('/').partition('/')
        child = self.children.get('/' + name)
        return child.GetChildByPath('/' + remaining) if child and remaining else child

    def GetPath(self):
        return self.path

    def SetLayer(self, layer):
        self.layer = layer

    def asButton(self):
        return self

    asSlider = asButton
    asSwitchToggle = asButton
    asTextEditBox = asButton

    def AddTouchEventParams(self, *args):
        pass

    def SetButtonTouchUpCallback(self, callback):
        self.handlers['click'] = callback

    def SetButtonTouchMoveInCallback(self, callback):
        self.handlers['in'] = callback

    def SetButtonTouchMoveOutCallback(self, callback):
        self.handlers['out'] = callback

    def SetSliderValue(self, value):
        self.slider = value

    def GetSliderValue(self):
        return self.slider

    def SetToggleState(self, value, path):
        self.toggle = value

    def GetToggleState(self, path):
        return self.toggle

    def SetEditText(self, value):
        self.text = value

    def GetEditText(self):
        return self.text


class GroupControlTests(unittest.TestCase):
    load_environment = custom_fixture.CustomControlTests.load_environment
    get_players = custom_fixture.CustomControlTests.get_players
    emit = custom_fixture.CustomControlTests.emit
    tearDown = custom_fixture.CustomControlTests.tearDown
    make_form = custom_fixture.CustomControlTests.make_form
    add = custom_fixture.CustomControlTests.add
    close_ui = custom_fixture.CustomControlTests.close_ui
    load_public_registration = custom_fixture.CustomControlTests.load_public_registration

    def setUp(self):
        custom_fixture.CustomControlTests.setUp(self)
        public, _ = self.load_public_registration()
        self.public = public
        self.Group = sys.modules[public.__module__.rsplit('.', 1)[0] + '.controls'].Group
        core = Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/core'
        for suffix, file in (('.general.control', 'general/control.py'),
                             ('.general.managers.control', 'general/managers/control.py')):
            name = self.prefix + suffix
            spec = importlib.util.spec_from_file_location(name, core / file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.modules.append(name)
            spec.loader.exec_module(module)
        manager = module.ControlManager()
        for name, control in self.registry.items():
            manager.create(control.typeId, name, control.path, control.options)
        manager.create('label', 'label', 'label.path', {'labelPaths': ['/label']})
        manager.create('button', 'button', 'button.path', {'labelPaths': ['/label'], 'buttonPath': ''})
        manager.create('slider', 'slider', 'slider.path', {'sliderPath': '', 'labelPaths': ['/label'], 'valuePaths': ['/value']})
        manager.create('toggle', 'toggle', 'toggle.path', {'togglePath': '', 'labelPaths': ['/label']})
        manager.create('textfield', 'textfield', 'textfield.path', {'textfieldPath': '', 'labelPaths': ['/label']})
        self.system.controlManager = self.ui.controlManager = manager
        original = self.ui.CreateChildControl
        def create(path, name, parent):
            if name.startswith('fm'):
                root = original(path, name, parent)
                root.path = '/panel/' + name
                scroll = root.children['/content']
                scroll.path = root.path + '/content'
                content = next(iter(scroll.children.values()))
                content.path = scroll.path + '/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content'
                return root
            native = NativeControl(parent, parent.path + '/' + name)
            parent.children['/' + name] = native
            self.ui.nodes[native.path] = native
            self.native_customs.append(native)
            return native
        self.ui.CreateChildControl = create
        self.ui.RemoveChildControl = self.remove_native

    def remove_native(self, control):
        if getattr(control, 'parent', None):
            for key, child in list(control.parent.children.items()):
                if child is control:
                    del control.parent.children[key]
        path = getattr(control, 'path', '')
        for key in list(self.ui.nodes):
            if key == path or key.startswith(path + '/'):
                del self.ui.nodes[key]

    def register(self, name, controls, on_create=None):
        self.server_side = False
        self.public.register(name, 'panel.path', self.Group(controls, onCreate=on_create))
        self.server_side = True

    def group_form(self, name='group', children=None, **style):
        options = {'class': name, 'width': 200, 'height': 100, 'offsetX': 0}
        options.update(style)
        return self.make_form(width=400, height=200).group(children or {}, options)

    def child(self, form_id, *names):
        return self.ui.getControl(form_id, (0,) + names)

    def test_registration_validates_required_class_names_and_pairs(self):
        for value in ([], {'x': {}}, {'a/b': {'class': 'label'}},
                      {'x': {'class': 'label', 'offset': [1]}},
                      {'x': {'class': 'label', 'size': (1, 2)}},
                      {'x': {'class': 'label', 'other': 1}}):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.Group(value)

    def test_nested_dropdown_extent_tracks_ancestor_and_child_offsets(self):
        self.system.controlManager.create('dropdown', 'dropdown', 'dropdown.path', {
            'dropdownPath': '/box', 'contentPath': '/items', 'boxLabelPaths': ['/label'],
        })
        self.ui.setDropdownProperties = lambda *args: None
        offset = self.system.observableManager.create(20)
        visible = self.system.observableManager.create(True)
        self.register('group', {'menu': {'class': 'dropdown', 'offsetY': offset, 'size': ['100%', 20]}})
        fid, _ = self.add(self.group_form(offsetY=50, visible=visible))
        child = self.child(fid, 'menu')
        box = NativeControl(child, child.path + '/box')
        items = NativeControl(child, child.path + '/items')
        items.SetFullPosition('y', {'absoluteValue': 15, 'relativeValue': 0, 'followType': 'parent'})
        items.SetFullSize('y', {'absoluteValue': 250, 'relativeValue': 0, 'followType': 'parent'})
        child.children.update({'/box': box, '/items': items})
        content = child.parent.parent
        self.ui.onDropdownBoxClick(fid, (0, 'menu'))
        self.assertEqual(content.GetSize()[1], 335)
        offset.setValue(40)
        self.assertEqual(content.GetSize()[1], 355)
        visible.setValue(False)
        self.assertFalse(items.visible)
        self.assertNotIn('dropdown', self.ui.forms[fid])
        self.assertEqual(content.GetSize()[1], 200)

    def test_percentages_and_alias_precedence_are_relative_to_group(self):
        self.register('group', {'x': {'class': 'label', 'offset': [1, '10%'],
                                     'offsetX': 9, 'size': ['100%', '100%'], 'width': '50%'}})
        fid, _ = self.add(self.group_form())
        child = self.child(fid, 'x')
        self.assertEqual(child.GetPosition(), (9, 10))
        self.assertEqual(child.GetSize(), (100, 100))

    def test_group_root_size_and_offset_aliases_observable_scalars(self):
        width = self.system.observableManager.create(200)
        self.register('group', {'x': {'class': 'label', 'size': ['100%', '100%']}})
        form = self.make_form(width=400, height=200).group(style={
            'class': 'group', 'size': [100, 80], 'width': width,
            'offset': [5, 6], 'offsetY': 10})
        fid, _ = self.add(form)
        self.assertEqual(self.ui.getControl(fid, 0).GetPosition(), (5, 10))
        self.assertEqual(self.child(fid, 'x').GetSize(), (200, 80))
        width.setValue(300)
        self.assertEqual(self.child(fid, 'x').GetSize(), (300, 80))

    def test_pair_observables_keep_explicit_axis_overrides_on_update(self):
        size = self.system.observableManager.create(['100%', '50%'])
        offset = self.system.observableManager.create([1, 2])
        visible = self.system.observableManager.create(True)
        self.register('group', {'x': {'class': 'label', 'size': size, 'width': 40,
                                     'offset': offset, 'offsetY': 7, 'visible': visible}})
        fid, data = self.add(self.group_form())
        self.assertTrue(set((size._id, offset._id, visible._id)).issubset(data['observables']))
        size.setValue(['20%', '100%'])
        offset.setValue([10, 90])
        visible.setValue(False)
        child = self.child(fid, 'x')
        self.assertEqual(child.GetSize(), (40, 100))
        self.assertEqual(child.GetPosition(), (10, 7))
        self.assertFalse(child.visible)

    def test_observable_elements_and_parent_resize_update_all_instances(self):
        width = self.system.observableManager.create(200)
        offset = self.system.observableManager.create(1)
        self.register('group', {'x': {'class': 'label', 'offset': [offset, 0], 'size': ['50%', 20]}})
        form = self.group_form(width=width).group(style={'class': 'group', 'width': 300, 'height': 100})
        fid, _ = self.add(form)
        offset.setValue(9)
        width.setValue(240)
        self.assertEqual(self.child(fid, 'x').GetSize()[0], 120)
        self.assertEqual(self.ui.getControl(fid, (1, 'x')).GetSize()[0], 150)
        self.assertEqual(self.child(fid, 'x').GetPosition()[0], 9)
        self.assertEqual(self.ui.getControl(fid, (1, 'x')).GetPosition()[0], 9)

    def test_grid_fraction_only_scales_group_root(self):
        self.register('group', {'x': {'class': 'label', 'size': ['100%', 20]}})
        form = self.make_form(width=400, height=200, grids=[1, 3])
        form.group(style={'class': 'group', 'width': '100%', 'height': 40, 'offsetX': 0})
        form.group(style={'class': 'group', 'width': '100%', 'height': 40, 'offsetX': 0})
        fid, _ = self.add(form)
        self.assertEqual(self.child(fid, 'x').GetSize()[0], 100)
        self.assertEqual(self.ui.getControl(fid, (1, 'x')).GetSize()[0], 300)

    def test_named_child_labels_and_callbacks_are_isolated(self):
        self.register('group', {'label': {'class': 'label'}, 'button': {'class': 'button'}})
        value = self.system.observableManager.create('first')
        calls = []
        form = self.group_form(children={'label': {'label': value}, 'button': {'label': 'A', 'callbacks': {'onClick': lambda p: calls.append(('A', p))}}})
        form.group({'label': {'label': 'second'}, 'button': {'label': 'B', 'callbacks': {'onClick': lambda p: calls.append(('B', p))}}}, {'class': 'group'})
        fid, _ = self.add(form)
        value.setValue('changed')
        self.assertEqual(self.child(fid, 'label').children['/label'].text, 'changed')
        self.assertEqual(self.ui.getControl(fid, (1, 'label')).children['/label'].text, 'second')
        # The example was created on the server; emulate its callback dispatch.
        self.system.NotifyToServer = lambda event, data: form._btnCallbacks[data['callbackId']](data['playerId'])
        self.child(fid, 'button').handlers['click']({})
        self.ui.getControl(fid, (1, 'button')).handlers['click']({})
        self.assertEqual(calls, [('A', 'p1'), ('B', 'p1')])

    def test_nested_group_layout_and_custom_notification_instance_routing(self):
        self.register('inner', {'custom': {'class': 'custom', 'size': ['100%', '100%']}})
        self.register('group', {'inner': {'class': 'inner', 'size': ['50%', '50%']}})
        value = self.system.observableManager.create(0)
        fid, _ = self.add(self.group_form(children={'inner': {'children': {'custom': {'params': {'count': value}}}}}))
        self.assertEqual(self.child(fid, 'inner', 'custom').GetSize(), (100, 50))
        self.assertEqual(self.created[0].params, {'count': 0})
        value.setValue(3)
        self.assertEqual(self.updated[0].newValue, 3)
        self.assertIs(self.updated[0].control, self.child(fid, 'inner', 'custom'))

    def test_inputs_use_nested_data_and_close_removes_records(self):
        self.register('group', {name: {'class': name} for name in ('slider', 'toggle', 'textfield')})
        value = self.system.observableManager.create(0)
        state = self.system.observableManager.create(False)
        text = self.system.observableManager.create('')
        fid, _ = self.add(self.group_form(children={'slider': {'value': value, 'maxValue': 10}, 'toggle': {'state': state}, 'textfield': {'value': text}}))
        calls = []
        self.system.NotifyToServer = lambda event, data: calls.append((event, data))
        self.ui.onSliderUpdate(fid, (0, 'slider'), 6)
        self.ui.onToggleUpdate(fid, (0, 'toggle'), True)
        self.ui.onTextfieldUpdate(fid, (0, 'textfield'), 'new')
        self.assertEqual([data['value'] for event, data in calls], [6, True, 'new'])
        self.assertEqual(len(self.ui.sliders), 1)
        self.close_ui(fid)
        self.assertEqual((self.ui.sliders, self.ui.toggles, self.ui.textfields), ([], [], []))
        self.assertEqual(self.ui.observables, [])
        self.assertEqual(self.ui._Screen__nativeControls, {})

    def test_class_observable_rebuilds_child_with_current_values(self):
        cls = self.system.observableManager.create('label')
        text = self.system.observableManager.create('value')
        self.register('group', {'x': {'class': cls, 'size': ['50%', 20]}})
        fid, _ = self.add(self.group_form(children={'x': {'label': text}}))
        old = self.child(fid, 'x')
        cls.setValue('button')
        new = self.child(fid, 'x')
        self.assertIsNot(old, new)
        self.assertEqual(new.children['/label'].text, 'value')
        self.assertEqual(new.GetSize(), (100, 20))
        text.setValue('next')
        self.assertEqual(new.children['/label'].text, 'next')

    def test_template_observable_update_before_show_is_used(self):
        width = self.system.observableManager.create(10)
        self.register('group', {'x': {'class': 'label', 'width': width}})
        width.setValue(70)
        fid, _ = self.add(self.group_form())
        self.assertEqual(self.child(fid, 'x').GetSize()[0], 70)

    def test_circular_references_and_unknown_children_fail_before_creation(self):
        self.register('group', {'x': {'class': 'group'}})
        with self.assertRaisesRegex(ValueError, 'Circular'):
            self.add(self.group_form())
        self.assertEqual(self.ui.forms, {})
        self.register('plain', {'x': {'class': 'label'}})
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.add(self.group_form(name='plain', children={'missing': {}}))

    def test_input_polling_updates_all_group_children(self):
        self.register('group', {name: {'class': name} for name in ('slider', 'toggle', 'textfield')})
        value = self.system.observableManager.create(0)
        state = self.system.observableManager.create(False)
        text = self.system.observableManager.create('')
        fid, _ = self.add(self.group_form(children={'slider': {'value': value, 'maxValue': 10}, 'toggle': {'state': state}, 'textfield': {'value': text}}))
        self.child(fid, 'slider').slider = 0.6
        self.child(fid, 'toggle').toggle = True
        self.child(fid, 'textfield').text = 'typed'
        calls = []
        self.system.NotifyToServer = lambda event, data: calls.append((event, data))
        self.ui.Update()
        self.assertEqual([data['value'] for event, data in calls], [True, 6, 'typed'])

    def test_class_update_while_waiting_for_creation_uses_new_type(self):
        cls = self.system.observableManager.create('label')
        self.register('group', {'x': {'class': cls}})
        form = self.group_form(children={'x': {'label': 'new button'}})
        form.show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        cls.setValue('button')
        self.timers.drain()
        child = self.child(data['formId']['value'], 'x')
        self.assertIn('click', child.handlers)
        self.assertEqual(child.children['/label'].text, 'new button')

    def test_creation_callbacks_run_children_before_group_after_layout(self):
        seen = []
        self.system.controlManager.get('label').options['onCreate'] = lambda args: seen.append(('child', args.control.GetSize()))
        self.register('group', {'x': {'class': 'label', 'size': ['50%', '50%']}}, lambda args: seen.append(('group', args.control.GetSize())))
        self.add(self.group_form())
        self.assertEqual(seen, [('child', (100, 50)), ('group', (200, 100))])

    def test_group_root_pair_observable_drives_percentage_children(self):
        size = self.system.observableManager.create([200, 100])
        offset = self.system.observableManager.create([5, 6])
        self.register('group', {'x': {'class': 'label', 'size': ['50%', '100%']}})
        form = self.make_form(width=400, height=200).group(style={'class': 'group', 'size': size, 'offset': offset, 'offsetY': 9})
        fid, _ = self.add(form)
        size.setValue([300, 80])
        offset.setValue([10, 90])
        self.assertEqual(self.ui.getControl(fid, 0).GetSize(), (300, 80))
        self.assertEqual(self.ui.getControl(fid, 0).GetPosition(), (10, 9))
        self.assertEqual(self.child(fid, 'x').GetSize(), (150, 80))

    def test_custom_updates_while_waiting_keep_order_in_nested_group(self):
        value = self.system.observableManager.create(0)
        self.register('group', {'x': {'class': 'custom'}})
        form = self.group_form(children={'x': {'params': {'value': value}}})
        form.show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        value.setValue(1)
        value.setValue(2)
        self.timers.drain()
        self.assertEqual(self.created[0].params, {'value': 2})
        self.assertEqual([(args.oldValue, args.newValue) for args in self.updated], [(0, 1), (1, 2)])

    def test_button_label_binding_uses_registered_button_subpath(self):
        self.system.controlManager.get('button').options['buttonPath'] = '/button'
        create = self.ui.CreateChildControl
        def wrapper(path, name, parent):
            native = create(path, name, parent)
            if path == 'button.path':
                native.children['/button'] = NativeControl(native, native.path + '/button')
            return native
        self.ui.CreateChildControl = wrapper
        self.register('group', {'x': {'class': 'button'}})
        text = self.system.observableManager.create('before')
        fid, _ = self.add(self.group_form(children={'x': {'label': text}}))
        button = self.child(fid, 'x').GetChildByPath('/button')
        self.assertEqual(button.children['/label'].text, 'before')
        text.setValue('after')
        self.assertEqual(button.children['/label'].text, 'after')

    def test_client_owned_input_in_server_form_updates_local_observable(self):
        observable_module = sys.modules[self.observable_class.__module__]
        previous_id = observable_module.ObId
        self.server_side = False
        observable_module.ObId = -1
        try:
            value = self.system.observableManager.create(0)
        finally:
            observable_module.ObId = previous_id
            self.server_side = True
        self.register('group', {'x': {'class': 'slider'}})
        fid, _ = self.add(self.group_form(children={'x': {'value': value, 'maxValue': 10}}))
        calls = []
        self.system.NotifyToServer = lambda *args: calls.append(args)
        self.ui.onSliderUpdate(fid, (0, 'x'), 6)
        self.assertEqual(value.getValue(), 6)
        self.assertEqual(calls, [])

    def test_class_replacement_can_mount_another_nested_group(self):
        self.register('a', {'leaf': {'class': 'label', 'width': '100%'}})
        self.register('b', {'leaf': {'class': 'label', 'width': '50%'}})
        cls = self.system.observableManager.create('a')
        self.register('group', {'inner': {'class': cls, 'size': ['100%', '100%']}})
        fid, _ = self.add(self.group_form())
        old = self.child(fid, 'inner', 'leaf')
        cls.setValue('b')
        new = self.child(fid, 'inner', 'leaf')
        self.assertIsNot(old, new)
        self.assertEqual(new.GetSize()[0], 100)
        self.assertIs(self.ui.nodes[new.path], new)

    def test_server_registration_serializes_observable_definitions(self):
        width = self.system.observableManager.create(42)
        sent = []
        self.system.BroadcastToAllClient = lambda event, data: sent.append((event, data))
        self.public.register('group', 'panel.path', self.Group({'x': {'class': 'label', 'width': width}}))
        data = sent[0][1]
        self.assertEqual(data['type'], 'group')
        self.assertEqual(data['options']['controls']['x']['width']['obId'], width._id)
        self.assertEqual(data['options']['controls']['x']['width']['value'], 42)


if __name__ == '__main__':
    unittest.main()
