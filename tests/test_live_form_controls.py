"""Live additions, pending close cancellation, font scaling and static options."""
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path
import test_group_controls as groups
from test_client_observable_delivery import FakeClientSystem


class LiveFormControlTests(unittest.TestCase):
    load_environment = groups.GroupControlTests.load_environment
    get_players = groups.GroupControlTests.get_players
    emit = groups.GroupControlTests.emit
    tearDown = groups.GroupControlTests.tearDown
    make_form = groups.GroupControlTests.make_form
    add = groups.GroupControlTests.add
    register = groups.GroupControlTests.register
    group_form = groups.GroupControlTests.group_form
    remove_native = groups.GroupControlTests.remove_native
    load_public_registration = groups.GroupControlTests.load_public_registration

    def setUp(self):
        groups.GroupControlTests.setUp(self)
        self.engine = sys.modules['mod.client.extraClientApi']
        self.engine.GetClientSystemCls = lambda: FakeClientSystem
        self.engine.GetEngineNamespace = lambda: 'engine'
        self.engine.GetEngineSystemName = lambda: 'engineClient'
        self.engine.GetTopScreen = lambda: self.top
        self.engine.PushScreen = lambda *args: None
        self.top = self.ui
        config = sys.modules[self.prefix + '.config']
        config.SystemNameServer = 'server'
        screen_name = self.prefix + '.general.screen'
        screen_spec = importlib.util.spec_from_file_location(screen_name, Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/core/general/screen.py')
        screen_module = importlib.util.module_from_spec(screen_spec)
        sys.modules[screen_name] = screen_module
        self.modules.append(screen_name)
        screen_spec.loader.exec_module(screen_module)
        name = self.prefix + '.client.system'
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/core/client/system.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        self.modules.append(name)
        spec.loader.exec_module(module)
        self.client = module.Client('test', 'client')
        self.client.controlManager = self.system.controlManager
        self.client._registerFormScreen(self.ui)
        self.client.NotifyToServer = self.notify_server
        self.client.BroadcastEvent = lambda event, data: self.emit(event, data)
        sys.modules[self.prefix + '.utils.environment'].getClientSystem = lambda: self.client
        self.system.NotifyToClient = lambda target, event, data: self.deliver(event, data)
        self.system.NotifyToMultiClients = lambda targets, event, data: self.deliver(event, data)
        self.system.appendFormControl = self.client.appendFormControl
        self.system.closeForm = self.client.closeForm
        self.system.BroadcastToAllClient = lambda event, data: self.deliver(event, data)
        self.events = []
        self.cancelled = []
        self.timers.CancelTimer = self.cancelled.append

    def notify_server(self, event, data):
        if event == 'buttonTriggerCallback':
            self.server_class.onButtonTrigger(self.system, data)
        else:
            self.emit(event, data)

    def deliver(self, event, data):
        self.events.append((event, copy.deepcopy(data)))
        if event == 'appendFormControl':
            self.client.appendFormControl(copy.deepcopy(data))
        elif event == 'closeForm':
            self.client.closeForm(data)
        elif event == 'applyObservableUpdate':
            self.client.applyObservableUpdate(data)
        elif event == 'registerControl':
            self.client.registerControl(copy.deepcopy(data))
        else:
            self.payloads.append(copy.deepcopy(data))

    def test_server_additions_mount_without_recreating_existing_controls(self):
        seen = []
        form = self.make_form(width=400, height=200).button('first', style={'class': 'button'})
        fid, data = self.add(form)
        first = self.ui.getControl(fid, 0)
        text = self.system.observableManager.create('new')
        form.button('second', {'onClick': seen.append}, {'class': 'button'})
        form.label(text, {'class': 'label', 'fontSize': 1.5})
        self.assertIs(self.ui.getControl(fid, 0), first)
        self.assertEqual(len(data['controls']), 3)
        button = self.ui.getControl(fid, 1)
        button.handlers['click']({})
        self.assertEqual(seen, ['p1'])
        label = self.ui.getControl(fid, 2).children['/label']
        self.assertEqual((label.text, label.font_scale), ('new', 1.5))
        text.setValue('changed')
        self.assertEqual(label.text, 'changed')

    def test_client_additions_and_new_groups_keep_instance_bindings(self):
        self.register('group', {'title': {'class': 'label', 'size': ['50%', 20]}})
        self.server_side = False
        form = self.make_form(width=400, height=200)
        fid, _ = self.add(form)
        text = self.system.observableManager.create('group title')
        form.group({'title': {'label': text}}, {'class': 'group', 'width': 200, 'height': 60})
        child = self.ui.getControl(fid, (0, 'title'))
        self.assertEqual(child.GetSize(), (100, 20))
        text.setValue('updated')
        self.assertEqual(child.children['/label'].text, 'updated')

    def test_all_add_methods_deliver_params_and_keep_native_interactions(self):
        from test_group_controls import NativeControl
        kinds = ('button', 'toggle', 'divider', 'label', 'slider', 'textfield', 'dropdown', 'group')
        self.system.controlManager.create('divider', 'divider', 'divider.path', {})
        self.system.controlManager.create('dropdown', 'dropdown', 'dropdown.path', {
            'dropdownPath': '', 'contentPath': '/items', 'labelPaths': ['/label'],
            'boxLabelPaths': ['/label'], 'itemLabelPaths': ['/label'], 'itemControl': 'item.path',
        })
        original = self.ui.CreateChildControl
        def create(path, name, parent):
            native = original(path, name, parent)
            if path == 'dropdown.path':
                native.children['/items'] = NativeControl(native, native.path + '/items')
            elif path == 'item.path':
                native.children['/button_label'] = native.children['/label']
            return native
        self.ui.CreateChildControl = create
        self.register('group', {})
        value = self.system.observableManager.create({'items': [7]})
        for server_side in (True, False):
            with self.subTest(server_side=server_side):
                self.server_side = server_side
                self.client.formManager = self.system.formManager
                created, clicked = {}, []
                for kind in kinds:
                    self.system.controlManager.get(kind).options['onCreate'] = (
                        lambda args, kind=kind: created.setdefault(kind, args))
                form = self.make_form(width=400, height=400)
                for kind in kinds:
                    params = {'kind': kind, 'nested': {'values': [value]}}
                    style = {'class': kind, 'height': 30}
                    if kind == 'button':
                        result = form.button('button', {'onClick': clicked.append}, style, params)
                    elif kind == 'toggle':
                        result = form.toggle('toggle', True, style, params)
                    elif kind == 'divider':
                        result = form.divider(style, params)
                    elif kind == 'label':
                        result = form.label('label', style, params)
                    elif kind == 'slider':
                        result = form.slider('slider', 30, 0, 100, 1, style, params)
                    elif kind == 'textfield':
                        result = form.textfield('textfield', 'text', style, params)
                    elif kind == 'dropdown':
                        result = form.dropdown('dropdown', [{'label': 'one', 'value': 1}], 1, style, params)
                    else:
                        result = form.group({}, style, params)
                    self.assertIs(result, form)
                    params['later'] = 'not part of the added control'
                fid, data = self.add(form)
                self.assertEqual(set(created), set(kinds))
                for index, kind in enumerate(kinds):
                    args = created[kind]
                    self.assertEqual(args.params, {'kind': kind, 'nested': {'values': [{'items': [7]}]}})
                    self.assertIs(args.control, self.ui.getControl(fid, index))
                    self.assertNotIn(index, self.ui._Screen__customControls.get(fid, {}))
                    args.params['nested']['values'][0]['items'].append(99)
                    self.assertEqual(data['controls'][index]['params']['nested']['values'][0]['value'],
                                     {'items': [7]})
                self.assertEqual(value.getValue(), {'items': [7]})
                created['button'].control.handlers['click']({})
                self.assertEqual(clicked, ['p1'])
                self.assertTrue(created['toggle'].control.toggle)
                self.assertEqual(created['label'].control.children['/label'].text, 'label')
                self.assertEqual(created['slider'].control.slider, 0.3)
                self.assertEqual(created['textfield'].control.text, 'text')
                item = created['dropdown'].control.children['/items'].children['/item_1']
                self.assertEqual(item.children['/button_label'].text, 'one')
                self.assertIn('click', item.handlers)

    def test_params_default_isolated_and_invalid_values_rejected_for_all_methods(self):
        calls = (
            lambda form, **kw: form.button('button', **kw),
            lambda form, **kw: form.toggle('toggle', True, **kw),
            lambda form, **kw: form.divider(**kw),
            lambda form, **kw: form.label('label', **kw),
            lambda form, **kw: form.slider('slider', 0, **kw),
            lambda form, **kw: form.textfield('textfield', '', **kw),
            lambda form, **kw: form.dropdown('dropdown', [], 0, **kw),
            lambda form, **kw: form.group(**kw),
        )
        for call in calls:
            for invalid in (None, [], 'invalid'):
                with self.subTest(call=call, invalid=invalid), self.assertRaises(TypeError):
                    call(self.make_form(), params=invalid)
        created = []
        def on_create(args):
            created.append(dict(args.params))
            args.params['local'] = True
        self.system.controlManager.get('button').options['onCreate'] = on_create
        form = self.make_form().button('first', style={'class': 'button'})
        form.button('second', style={'class': 'button'})
        fid, data = self.add(form)
        form.button('appended', style={'class': 'button'}, params={'id': 3})
        self.assertEqual(created, [{}, {}, {'id': 3}])
        self.assertEqual([item['params'] for item in data['controls'][:2]], [{}, {}])

    def test_pending_ordinary_and_group_params_do_not_block_custom_updates(self):
        created = []
        value = self.system.observableManager.create(0)
        self.system.controlManager.get('button').options['onCreate'] = created.append
        self.register('group', {'button': {'class': 'button'}, 'custom': {'class': 'custom'}},
                      on_create=created.append)
        form = self.make_form().button('ordinary', style={'class': 'button'}, params={'count': value})
        form.group({'button': {'label': 'nested', 'params': {'count': value}},
                    'custom': {'params': {'count': value}}},
                   {'class': 'group'}, {'count': value})
        form.custom({'count': value}, {'class': 'custom'})
        form.show('p1')
        self.ui.addForm(self.payloads[-1])
        value.setValue(1)
        value.setValue(2)
        self.timers.drain()
        self.assertEqual([args.params for args in created], [{'count': 2}] * 3)
        self.assertEqual(len(self.created), 2)
        self.assertEqual([args.params for args in self.created], [{'count': 2}] * 2)
        self.assertEqual([(args.oldValue, args.newValue) for args in self.updated],
                         [(0, 1), (0, 1), (1, 2), (1, 2)])
        value.setValue(3)
        self.assertEqual([(args.oldValue, args.newValue) for args in self.updated[-2:]], [(2, 3)] * 2)
        self.assertEqual(created[0].params, {'count': 2})
        fid = self.payloads[-1]['formId']['value']
        self.assertFalse(self.ui._Screen__pendingCustomUpdates.get(fid))

    def test_group_child_params_validation(self):
        for invalid in (None, [], 'invalid'):
            with self.subTest(invalid=invalid), self.assertRaises(TypeError):
                self.make_form().group({'button': {'params': invalid}}, {'class': 'group'})

    def test_button_creation_style_snapshots_are_per_instance_and_preserve_bindings(self):
        created = []
        clicked = []
        self.system.controlManager.get('button').options['onCreate'] = created.append
        width = self.system.observableManager.create('50%')
        metadata = self.system.observableManager.create({'tags': ['first']})
        form = self.make_form(width=400, height=200)
        form.button('first', {'onClick': clicked.append}, {
            'class': 'button', 'name': 'first', 'width': width,
            'metadata': {'payload': metadata},
        }).button('second', style={
            'class': 'button', 'name': 'second', 'width': '25%',
        })
        fid, data = self.add(form)
        first, second = created
        self.assertEqual((first.style['name'], second.style['name']), ('first', 'second'))
        self.assertEqual(first.style['width'], '50%')
        self.assertEqual(second.style['width'], '25%')
        self.assertEqual(first.style['metadata'], {'payload': {'tags': ['first']}})
        self.assertIs(first.control, self.ui.getControl(fid, 0))
        self.assertIs(second.control, self.ui.getControl(fid, 1))
        self.assertEqual(first.params, {})

        first.style['name'] = 'local change'
        first.style['metadata']['payload']['tags'].append('local change')
        self.assertEqual(metadata.getValue(), {'tags': ['first']})
        self.assertEqual(data['controls'][0]['style']['name']['value'], 'first')
        self.assertEqual(data['controls'][0]['style']['metadata']['payload']['value'],
                         {'tags': ['first']})
        first.control.handlers['click']({})
        self.assertEqual(clicked, ['p1'])

        width.setValue('75%')
        self.assertEqual(first.style['width'], '50%')  # Creation snapshot stays fixed.
        self.assertEqual(data['controls'][0]['style']['width']['value'], '75%')
        form.button('appended', style={'class': 'button', 'name': 'appended', 'width': width})
        self.assertEqual((created[-1].style['name'], created[-1].style['width']),
                         ('appended', '75%'))

    def test_group_creation_callbacks_get_each_instances_normalized_style(self):
        created = []
        offset = self.system.observableManager.create(12)
        self.system.controlManager.get('button').options['onCreate'] = created.append
        self.register('group', {'button': {
            'class': 'button', 'size': ['50%', 24], 'offset': [offset, 8],
        }}, on_create=created.append)
        fid, _ = self.add(self.group_form(width=180, height=60))
        child, group = created
        self.assertIs(child.control, self.ui.getControl(fid, (0, 'button')))
        self.assertEqual(child.style, {
            'class': 'button', 'width': '50%', 'height': 24,
            'offsetX': 12, 'offsetY': 8, 'visible': True,
        })
        self.assertIs(group.control, self.ui.getControl(fid, 0))
        self.assertEqual((group.style['class'], group.style['width'], group.style['height']),
                         ('group', 180, 60))

    def test_additions_in_oncreate_are_mounted_after_initial_creation(self):
        seen = []
        form = self.make_form(width=400, height=200)
        def create(args):
            seen.append(args.control)
            form.label('from create', {'class': 'label'})
        self.system.controlManager.get('button').options['onCreate'] = create
        form.button('first', style={'class': 'button'})
        fid, data = self.add(form)
        self.assertEqual(len(seen), 1)
        self.assertEqual(len(data['controls']), 2)
        self.assertEqual(self.ui.getControl(fid, 1).children['/label'].text, 'from create')

    def test_additions_while_root_creation_is_waiting_are_not_duplicated(self):
        form = self.make_form(width=400, height=200)
        form.show('p1')
        data = self.payloads[-1]
        self.ui.addForm(data)
        form.button('while waiting', style={'class': 'button'})
        self.timers.drain()
        self.assertEqual(len(data['controls']), 1)
        self.assertEqual(len(self.native_customs), 1)
        self.assertIsNotNone(self.ui.getControl(data['formId']['value'], 0))

    def test_pending_screen_additions_receive_observable_updates_before_creation(self):
        form = self.make_form(width=400, height=200)
        form.show('p1')
        self.top = None
        payload = self.payloads[-1]
        self.client.showForm(payload)
        text = self.system.observableManager.create('old')
        form.label(text, {'class': 'label'})
        text.setValue('latest')
        self.ui.Create()
        self.top = self.ui
        self.timers.drain()
        self.assertEqual(self.ui.getControl(payload['formId']['value'], 0).children['/label'].text, 'latest')

    def test_close_before_delayed_creation_cancels_and_cannot_resurrect(self):
        form = self.make_form(width=400, height=200)
        seen = []
        form.show('p1').onClose(lambda args: seen.append(args.closeReason))
        payload = self.payloads[-1]
        self.ui.addForm(payload)
        form.close('p1')
        self.timers.drain()  # Invoke cancelled callbacks too, to exercise stale callback guards.
        self.assertEqual(self.ui.forms, {})
        self.assertEqual(self.ui._Screen__loadingForms, [])
        self.assertFalse(form.isShowing('p1'))
        self.assertEqual(seen, ['api'])
        self.assertTrue(self.cancelled)
        self.assertIsNone(self.ui.GetBaseUIControl('/panel/fm%s' % payload['formId']['value']))

    def test_cancelled_callbacks_do_not_close_or_recreate_a_reopened_form(self):
        form = self.make_form(width=400, height=200)
        form.show('p1')
        self.ui.addForm(self.payloads[-1])
        form.close('p1')
        form.show('p1')
        latest = self.payloads[-1]
        self.ui.addForm(latest)
        self.timers.drain()
        fid = latest['formId']['value']
        self.assertIs(self.ui.forms[fid], latest)
        self.assertTrue(form.isShowing('p1'))
        self.assertIsNotNone(self.ui.GetBaseUIControl('/panel/fm%s' % fid))

    def test_pending_push_can_be_closed_before_a_screen_is_ready(self):
        form = self.make_form(width=400, height=200)
        form.show('p1')
        self.top = None
        self.client.showForm(self.payloads[-1])
        form.close('p1')
        self.ui.Create()
        self.top = self.ui
        self.timers.drain()
        self.assertEqual(self.ui.forms, {})
        self.assertFalse(form.isShowing('p1'))
        self.assertEqual(self.client._Client__pendingForms, [])

    def test_close_in_creation_callback_stops_later_callbacks_and_additions(self):
        form = self.make_form(width=400, height=200)
        seen = []
        def create(args):
            seen.append(args.control)
            form.close('p1')
        self.system.controlManager.get('button').options['onCreate'] = create
        form.button('first', style={'class': 'button'}).button('second', style={'class': 'button'})
        self.add(form)
        self.assertEqual(len(seen), 1)
        self.assertEqual(self.ui.forms, {})
        self.assertFalse(form.isShowing('p1'))

    def test_fontsize_updates_and_default_reset(self):
        scale = self.system.observableManager.create(1.25)
        form = self.make_form(width=400, height=200).label('text', {'class': 'label', 'fontSize': scale})
        fid, _ = self.add(form)
        label = self.ui.getControl(fid, 0).children['/label']
        self.assertEqual(label.font_scale, 1.25)
        scale.setValue(2)
        self.assertEqual(label.font_scale, 2)
        scale.setValue('default')
        self.assertEqual(label.font_scale, 1)
        for invalid in (-1, float('nan'), 'normal'):
            with self.assertRaises(ValueError):
                self.make_form().label('bad', {'fontSize': invalid})

    def test_dropdown_options_reject_observables_in_forms_and_groups(self):
        text = self.system.observableManager.create('label')
        number = self.system.observableManager.create(1)
        for items in ([{'label': text, 'value': 1}], [{'label': 'one', 'value': number}],
                      self.system.observableManager.create([{'label': 'one', 'value': 1}])):
            with self.assertRaises(TypeError):
                self.make_form().dropdown('bad', items, number)
            with self.assertRaises(TypeError):
                self.make_form().group({'menu': {'items': items}}, {'class': 'group'})

    def test_late_client_receives_latest_registration_defaults_and_group_values(self):
        self.system.controlManager = type(self.system.controlManager)()
        width = self.system.observableManager.create(10)
        self.public.registerScrollingPanel('server:panel', 'panel.path')
        self.public.registerLabel('server:label', 'label.path')
        self.public.registerGroup('server:group', 'fui.group', {'controls': {
            'title': {'class': 'server:label', 'width': width},
        }})
        width.setValue(20)
        received = []
        self.system.NotifyToClient = lambda player, event, data: received.append((player, event, data))
        self.server_class.onRequestControls(self.system, {'playerId': 'late'})
        self.assertTrue(all(player == 'late' and event == 'registerControl' for player, event, _ in received))
        registrations = {data['name']: data for _, _, data in received}
        self.assertEqual(registrations['server:panel']['type'], 'scrolling_panel')
        self.assertIn('scrollingPanelPath', registrations['server:panel']['options'])
        self.assertEqual(registrations['server:label']['options']['labelPaths'], ['/label'])
        self.assertEqual(registrations['server:group']['options']['controls']['title']['width']['value'], 20)
        registrations['server:group']['options']['controls']['title']['width']['value'] = 999
        width.setValue(30)
        self.public.registerLabel('server:label', 'new.path')
        received[:] = []
        self.server_class.onRequestControls(self.system, {'playerId': 'reconnected'})
        registrations = {data['name']: data for _, _, data in received}
        self.assertEqual(registrations['server:label']['path'], 'new.path')
        self.assertEqual(registrations['server:group']['options']['controls']['title']['width']['value'], 30)

    def test_uiinit_requests_registrations_after_registering_ui(self):
        package_name = self.prefix + '.general.controls'
        package = types.ModuleType(package_name)
        package.__path__ = [str(Path(__file__).resolve().parents[1] / 'behavior/scripts/FormUI/core/general/controls')]
        sys.modules[package_name] = package
        self.modules.append(package_name)
        module = types.ModuleType(package_name + '.oreui')
        module.OreUI = lambda: None
        sys.modules[module.__name__] = module
        self.modules.append(module.__name__)
        seen = []
        self.engine.RegisterUI = lambda *args: seen.append('registered')
        self.client.NotifyToServer = lambda event, data: seen.append((event, data))
        self.client.UIInit({})
        self.assertEqual(seen, ['registered', ('requestControls', {'playerId': 'p1'})])
        self.modules.append(package_name + '.flutter')
        self.modules.append(package_name + '.fluent')
        self.assertTrue(self.client.controlManager.has('flutter:filled_button'))
        self.assertTrue(self.client.controlManager.has('flutter:dark_dropdown'))
        self.assertTrue(self.client.controlManager.has('fluent:primary_button'))
        self.assertTrue(self.client.controlManager.has('fluent:dark_panel'))

    def test_close_all_cancels_all_forms_waiting_for_a_screen(self):
        forms = [self.make_form(width=400, height=200) for _ in range(2)]
        self.top = None
        for form in forms:
            form.show('p1')
            self.client.showForm(self.payloads[-1])
        self.client.closeForm({'closeAll': True})
        self.ui.Create()
        self.top = self.ui
        self.timers.drain()
        self.assertEqual(self.client._Client__pendingForms, [])
        self.assertEqual(self.ui.forms, {})
        self.assertTrue(all(not form.isShowing('p1') for form in forms))

    def test_not_ready_form_screen_keeps_data_pending_until_create(self):
        form = self.make_form(width=400, height=200)
        form.show('p1')
        self.client.showForm(self.payloads[-1])
        self.assertEqual(self.ui.forms, {})
        self.assertEqual(len(self.client._Client__pendingForms), 1)
        form.close('p1')
        self.ui.Create()
        self.timers.drain()
        self.assertEqual(self.ui.forms, {})

    def test_close_all_with_pending_and_mounted_forms_pops_only_once(self):
        active = self.make_form(width=400, height=200)
        self.add(active)
        waiting = self.make_form(width=400, height=200)
        waiting.show('p1')
        self.top = None
        self.client.showForm(self.payloads[-1])
        self.top = self.ui
        pops = []
        self.engine.PopScreen = lambda: pops.append('pop')
        self.client.closeForm({'closeAll': True})
        self.timers.drain()
        self.assertEqual(pops, ['pop'])
        self.assertFalse(active.isShowing('p1'))
        self.assertFalse(waiting.isShowing('p1'))
        self.assertEqual(self.ui.forms, {})


if __name__ == '__main__':
    unittest.main()
