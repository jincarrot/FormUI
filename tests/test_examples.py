"""Exercise the chat examples with real Form/Observable/Group implementations."""
import importlib.util
import io
import json
import math
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch
import zlib
import test_live_form_controls as fixture

ROOT = Path(__file__).resolve().parents[1]


class DemoSystem:
    def __init__(self, namespace, name):
        self.listeners = []
        self.messages = []

    def ListenForEvent(self, *args):
        self.listeners.append(args)

    def NotifyToClient(self, player, event, data):
        self.messages.append((player, event, data))

    def NotifyToServer(self, event, data):
        self.messages.append((event, data))


class Node:
    def __init__(self, path, size=(240, 224)):
        self.path, self.size = path, size
        self.children = {}
        self.angle = 0
        self.text = ''

    def child(self, name, size=(240, 224)):
        node = Node(self.path + '/' + name, size)
        self.children[name] = node
        return node

    def GetChildByPath(self, path):
        node = self
        for name in path.strip('/').split('/'):
            node = node.children[name]
        return node

    def GetSize(self):
        return self.size

    def GetPath(self):
        return self.path

    def SetSize(self, size):
        self.size = size

    def Rotate(self, angle):
        self.angle = angle

    def SetText(self, text):
        self.text = text

    def SetTextColor(self, color):
        self.color = color

    def AddTouchEventParams(self):
        pass

    def SetButtonTouchUpCallback(self, callback):
        self.click = callback

    def asImage(self):
        return self

    asButton = asImage
    asLabel = asImage


class Frames:
    def __init__(self):
        self.pending = []

    def addRepeatFunc(self, callback, times):
        if times != 1:
            raise AssertionError('Schedule one subsequent frame at a time')
        self.pending.append(callback)

    def tick(self):
        callbacks, self.pending = self.pending, []
        for callback in callbacks:
            callback()


class ExampleTests(unittest.TestCase):
    load_environment = fixture.LiveFormControlTests.load_environment
    get_players = fixture.LiveFormControlTests.get_players
    emit = fixture.LiveFormControlTests.emit
    make_form = fixture.LiveFormControlTests.make_form
    add = fixture.LiveFormControlTests.add
    register = fixture.LiveFormControlTests.register
    group_form = fixture.LiveFormControlTests.group_form
    remove_native = fixture.LiveFormControlTests.remove_native
    load_public_registration = fixture.LiveFormControlTests.load_public_registration
    notify_server = fixture.LiveFormControlTests.notify_server
    deliver = fixture.LiveFormControlTests.deliver

    def setUp(self):
        fixture.LiveFormControlTests.setUp(self)
        # Public factories delegate to the production managers, as FormUI.lib does.
        descriptors = sys.modules[self.public.__module__.rsplit('.', 1)[0] + '.controls']
        self.system.screen = sys.modules[self.prefix + '.general.screen'].Screen()
        lib = types.ModuleType('FormUI.lib')
        lib.Control = self.public
        lib.Form = types.SimpleNamespace(create=self.system.formManager.create)
        lib.Observable = types.SimpleNamespace(create=self.system.observableManager.create)
        style_spec = importlib.util.spec_from_file_location('example_style_constants',
            ROOT / 'behavior/scripts/FormUI/core/general/controls/innerStyles.py')
        style_constants = importlib.util.module_from_spec(style_spec)
        style_spec.loader.exec_module(style_constants)
        lib.Screen = types.SimpleNamespace(
            setDefaultStyle=lambda kind, style: self.system.screen.setDefaultStyle(kind, style, True),
            closeAllForms=self.system.screen.closeAllForms)
        for name in ('Custom', 'Group', 'Label'):
            setattr(lib, name, getattr(descriptors, name))
        package = types.ModuleType('FormUI')
        package.__path__ = []
        self.lib_patch = patch.dict(sys.modules, {
            'FormUI': package, 'FormUI.lib': lib, 'FormUI.innerStyles': style_constants,
        })
        self.lib_patch.start()
        server = sys.modules['mod.server.extraServerApi']
        client = sys.modules['mod.client.extraClientApi']
        server.GetServerSystemCls = client.GetClientSystemCls = lambda: DemoSystem
        self.feedback = []
        server.GetLevelId = lambda: 'level'
        server.GetEngineCompFactory = lambda: types.SimpleNamespace(
            CreateMsg=lambda player: types.SimpleNamespace(
                NotifyOneMessage=lambda target, text: self.feedback.append((target, text))),
            CreateGame=lambda level: self.timers)
        client.GetLevelId = lambda: 'level'
        self.example_prefix = '_formui_examples'
        example_package = types.ModuleType(self.example_prefix)
        example_package.__path__ = [str(ROOT / 'behavior/scripts')]
        sys.modules[self.example_prefix] = example_package
        self.modules.append(self.example_prefix)
        self.examples = []
        self.shared = self.load_example('example_shared')
        self.flutter_example = self.load_example('example_flutter')
        self.fluent_example = self.load_example('example_fluent')
        self.styles_example = self.load_example('example_styles')
        self.client_example = self.load_example('example_c')
        self.server_example = self.load_example('example_s')

    def load_example(self, filename):
        name = self.example_prefix + '.' + filename
        spec = importlib.util.spec_from_file_location(name, ROOT / 'behavior/scripts' / (filename + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        self.modules.append(name)
        spec.loader.exec_module(module)
        return module

    def tearDown(self):
        self.lib_patch.stop()
        fixture.LiveFormControlTests.tearDown(self)

    def make_client(self):
        self.server_side = False
        result = self.client_example.ExampleClient('FormUIExample', 'ExampleClient')
        result.ready = True
        return result

    def test_chat_ignores_normal_messages_and_targets_only_sender(self):
        self.server_side = True
        server = self.server_example.ExampleServer('FormUIExample', 'ExampleServer')
        normal = {'playerId': 'p1', 'message': 'hello fui client'}
        server.onChat(normal)
        self.assertNotIn('cancel', normal)
        for text, action in [('fui client', 'show'), ('FUI animation', 'animation'),
                             ('fui cancel-client', 'cancel'), ('fui flutter', 'flutter'),
                             ('fui flutter-dark', 'flutter-dark'), ('fui fluent', 'fluent'),
                             ('fui fluent-dark', 'fluent-dark'), ('fui compare', 'compare')]:
            data = {'playerId': 'p2', 'message': text}
            server.onChat(data)
            self.assertTrue(data['cancel'])
            self.assertEqual(server.messages[-1], ('p2', 'runClientDemo', {'action': action}))
        self.assertTrue(any(event[2] == 'ServerChatEvent' for event in server.listeners))

    def test_both_showcases_build_against_production_api_and_callbacks(self):
        self.make_client()  # Register client-side Custom used by both endpoints.
        reports = []
        for side in ('client', 'server'):
            with self.subTest(side=side):
                self.server_side = side == 'server'
                self.shared.register_groups('example_' + side)
                session = self.shared.DemoSession(side, 'p1', reports.append, lambda callback: None)
                session.show()
                self.assertTrue(session.form.isShowing('p1'))
                session.increment('p1')
                session.increment('p1')
                self.assertEqual(session.count.getValue(), 2)
                self.assertEqual(session.derivedWidth.getValue(), 50)
                self.assertTrue(session.derivedVisible.getValue())
                session.text.setValue('new text')
                self.assertIn('new text', session.status.getValue())
                session.toggleSubscription('p1')
                session.text.setValue('unsubscribed')
                self.assertEqual(session.status.getValue(), '文本订阅已取消')
                session.toggleSubscription('p1')
                session.text.setValue('subscribed again')
                self.assertIn('subscribed again', session.status.getValue())
                for _ in range(5):
                    session.changeRange('p1')
                session.changeFont('p1')
                session.changeGroup('p1')
                session.changeContainers('p1')
                session.changeRoot('p1')
                session.restoreRoot('p1')
                session.appendControls('p1')
                session.defaultStyle('p1')
                session.repeatShow('p1')
                self.assertIn('正确被拒绝', reports[-1])
                session.queryShowing('p1')
                self.assertIn('True', reports[-1])
                session.openPopup('p1')
                self.assertEqual(len(session.popups), 1)
                group = self.system.controlManager.get('example_' + side + ':group')
                self.assertEqual(group.typeId, 'group')

    def test_server_sessions_isolate_players_and_shared_form_uses_list_targets(self):
        server = self.server_example.ExampleServer('FormUIExample', 'ExampleServer')
        for player in ('p1', 'p2'):
            server.onChat({'playerId': player, 'message': 'fui server'})
        one, two = server.sessions['p1'], server.sessions['p2']
        one.increment('p1')
        self.assertEqual((one.count.getValue(), two.count.getValue()), (1, 0))
        self.assertFalse(one.form.isShowing('p2'))
        server.onChat({'playerId': 'p1', 'message': 'fui all'})
        self.assertTrue(server.shared.isShowing('p1'))
        self.assertTrue(server.shared.isShowing('p2'))
        previous = len(self.payloads)
        server.onChat({'playerId': 'p1', 'message': 'fui all'})
        self.assertEqual(len(self.payloads), previous)
        self.assertIn('均已显示', self.feedback[-1][1])

    def test_reopen_waits_for_close_ack_and_reuses_form(self):
        server = self.server_example.ExampleServer('FormUIExample', 'ExampleServer')
        server.onChat({'playerId': 'p1', 'message': 'fui server'})
        session = server.sessions['p1']
        fid = self.payloads[0]['formId']['value']
        self.system.NotifyToClient = lambda *args: None  # Simulate delayed network close.
        scheduled = []
        session.schedule = scheduled.append
        session.closeAndReopen('p1')
        self.assertEqual(scheduled, [])
        self.assertTrue(session.form.isShowing('p1'))
        self.emit('formClose%s' % fid, {'playerId': 'p1', 'closeReason': 'api'})
        self.assertFalse(session.form.isShowing('p1'))
        self.assertEqual(len(scheduled), 1)
        scheduled.pop()()
        self.assertTrue(session.form.isShowing('p1'))
        self.assertEqual(session.showCount, 2)

    def test_client_creation_request_can_be_queued_until_ui_ready(self):
        client = self.make_client()
        client.ready = False
        client.onCommand({'action': 'animation'})
        self.assertIsNone(client.animation)
        client.onUiReady({})
        self.timers.drain()
        self.assertTrue(client.ready)
        self.assertTrue(client.animation['form'].isShowing())

    def test_client_full_showcase_includes_animation_and_is_reused(self):
        client = self.make_client()
        client.onCommand({'action': 'show'})
        session = client.session
        self.assertIs(client.showcaseMotion['form'], session.form)
        self.assertEqual(client.showcaseMotion['angle'].getValue(), 0)
        previous = len(self.payloads)
        client.onCommand({'action': 'show'})
        self.assertIs(client.session, session)
        self.assertEqual(len(self.payloads), previous)

    def test_flutter_previews_build_and_reuse_the_same_form(self):
        client = self.make_client()
        for action in ('flutter', 'flutter-dark'):
            client.onCommand({'action': action})
            form = client.flutterForms[action]
            payload = self.payloads[-1]
            self.assertEqual(payload['style']['class']['value'],
                             'flutter:dark_panel' if action.endswith('dark') else 'flutter:light_panel')
            self.assertEqual(len(payload['controls']), 16)
            self.assertTrue(all(control['style']['class']['value'].startswith('flutter:')
                                for control in payload['controls']))
            count = len(self.payloads)
            client.onCommand({'action': action})
            self.assertIs(client.flutterForms[action], form)
            self.assertEqual(len(self.payloads), count)
            # Public button callbacks still receive playerId.
            callback = payload['controls'][2]['callbacks']['onClick']['value']
            form._btnCallbacks[callback]('p1')
            status = self.system.observableManager.get(payload['controls'][1]['label']['obId'])
            self.assertIn('playerId=p1', status.getValue())

    def test_fluent_previews_reuse_forms_bind_values_and_close_both_themes(self):
        client = self.make_client()
        for action in ('fluent', 'fluent-dark'):
            client.onCommand({'action': action})
            form = client.fluentForms[action]
            payload = self.payloads[-1]
            self.assertEqual(payload['style']['class']['value'],
                             'fluent:dark_panel' if action.endswith('dark') else 'fluent:light_panel')
            self.assertEqual(len(payload['controls']), 16)
            self.assertTrue(all(control['style']['class']['value'].startswith('fluent:')
                                for control in payload['controls']))
            count = len(self.payloads)
            client.onCommand({'action': action})
            self.assertIs(client.fluentForms[action], form)
            self.assertEqual(len(self.payloads), count)
            callback = payload['controls'][2]['callbacks']['onClick']['value']
            form._btnCallbacks[callback]('p1')
            status = self.system.observableManager.get(payload['controls'][1]['label']['obId'])
            self.assertIn('playerId=p1', status.getValue())
            enabled = self.system.observableManager.get(payload['controls'][8]['state']['obId'])
            enabled.setValue(False)
            visible_id = payload['controls'][14]['style']['visible']['obId']
            self.assertEqual(visible_id, payload['controls'][8]['state']['obId'])
            self.assertFalse(self.system.observableManager.get(visible_id).getValue())
        with patch.object(client.fluentForms['fluent'], 'close') as light_close, \
                patch.object(client.fluentForms['fluent-dark'], 'close') as dark_close:
            client.onCommand({'action': 'close'})
            light_close.assert_called_once()
            dark_close.assert_called_once()

    def test_style_comparison_shows_three_equal_forms_without_hiding_each_other(self):
        self.ui.Create()
        client = self.make_client()
        client.onCommand({'action': 'compare'})
        panels = self.payloads[-3:]
        self.assertEqual(len({panel['formId']['value'] for panel in panels}), 3)
        self.assertEqual([panel['title']['value'] for panel in panels], ['OreUI', 'Flutter', 'Fluent'])
        self.assertEqual([panel['style']['class']['value'] for panel in panels],
                         ['oreui:light_panel_thin', 'flutter:light_panel', 'fluent:light_panel'])
        self.assertEqual([panel['style']['offsetX']['value'] for panel in panels], ['-32%', '0%', '32%'])
        baseline = None
        for panel, prefix in zip(panels, ('oreui:', 'flutter:', 'fluent:')):
            self.assertEqual(panel['style']['width']['value'], '30%')
            self.assertEqual(panel['style']['height']['value'], '88%')
            self.assertFalse(panel['style']['hideOtherForms']['value'])
            self.assertTrue(panel['style']['visible']['value'])
            self.assertEqual(len(panel['controls']), 12)
            self.assertTrue(all(control['style']['class']['value'].startswith(prefix)
                                for control in panel['controls']))
            content = [{key: value for key, value in control.items() if key not in ('style', 'callbacks')}
                       for control in panel['controls']]
            if baseline is None:
                baseline = content
            else:
                self.assertEqual(content, baseline)
        self.assertTrue(all(form.isShowing() for form in client.styleComparison.forms))

    def test_style_comparison_shared_inputs_and_buttons_update_all_three_snapshots(self):
        self.ui.Create()
        client = self.make_client()
        client.onCommand({'action': 'compare'})
        comparison = client.styleComparison
        panels = self.payloads[-3:]
        for panel in panels:
            self.ui.forms[panel['formId']['value']] = panel
            self.ui.observables.extend(panel['observables'])
        for index, key, value in ((2, 'value', 'Alex'), (3, 'value', 2),
                                  (4, 'state', False), (5, 'value', 25)):
            ids = {panel['controls'][index][key]['obId'] for panel in panels}
            self.assertEqual(len(ids), 1)
            self.system.observableManager.get(next(iter(ids))).setValue(value)
            self.assertEqual([panel['controls'][index][key]['value'] for panel in panels], [value]*3)
        self.assertEqual([panel['controls'][7]['label']['value'] for panel in panels],
                         ['Alex / 实时预览']*3)
        callback = panels[1]['controls'][9]['callbacks']['onClick']['value']
        comparison.forms[1]._btnCallbacks[callback]('p1')
        self.assertEqual([panel['controls'][8]['label']['value'] for panel in panels], ['点击次数：1']*3)
        self.assertEqual([panel['controls'][1]['label']['value'] for panel in panels], ['点击者：p1']*3)
        callback = panels[2]['controls'][10]['callbacks']['onClick']['value']
        comparison.forms[2]._btnCallbacks[callback]('p1')
        for index, key, expected in ((2, 'value', 'Steve'), (3, 'value', 1),
                                     (4, 'state', True), (5, 'value', 60)):
            self.assertEqual([panel['controls'][index][key]['value'] for panel in panels], [expected]*3)
        self.assertEqual(comparison.count.getValue(), 0)

    def test_style_comparison_reopens_only_closed_panel_and_closes_all_from_a_button(self):
        self.ui.Create()
        client = self.make_client()
        client.onCommand({'action': 'compare'})
        comparison = client.styleComparison
        original = tuple(comparison.forms)
        panels = self.payloads[-3:]
        previous = len(self.payloads)
        client.onCommand({'action': 'compare'})
        self.assertEqual(len(self.payloads), previous)
        fid = panels[1]['formId']['value']
        self.emit('formClose%s' % fid, {'playerId': 'p1', 'closeReason': 'user'})
        self.assertFalse(comparison.forms[1].isShowing())
        comparison.name.setValue('Alex')
        client.onCommand({'action': 'compare'})
        self.assertEqual(tuple(comparison.forms), original)
        self.assertEqual(len(self.payloads), previous + 1)
        self.assertEqual(self.payloads[-1]['controls'][2]['value']['value'], 'Alex')
        with patch.object(original[0], 'close') as oreui_close, \
                patch.object(original[1], 'close') as flutter_close, \
                patch.object(original[2], 'close') as fluent_close:
            callback = panels[0]['controls'][11]['callbacks']['onClick']['value']
            original[0]._btnCallbacks[callback]('p1')
            for close in (oreui_close, flutter_close, fluent_close):
                close.assert_called_once_with('p1')
            oreui_close.reset_mock()
            flutter_close.reset_mock()
            fluent_close.reset_mock()
            client.onCommand({'action': 'close'})
            for close in (oreui_close, flutter_close, fluent_close):
                close.assert_called_once_with(None)

    def test_style_comparison_waits_for_one_screen_and_cancels_pending_shows(self):
        self.make_client()
        callbacks = []
        ready = [False]
        screen = types.SimpleNamespace(isFormScreen=lambda: True, isAllReady=lambda: ready[0])
        engine = sys.modules['mod.client.extraClientApi']
        with patch.object(engine, 'GetTopScreen', return_value=screen):
            comparison = self.styles_example.StyleComparison(callbacks.append)
            self.assertEqual(comparison.show(), 3)
            self.assertEqual(len(self.payloads), 1)
            self.assertEqual(len(comparison.pending), 2)
            self.assertEqual(comparison.show(), 0)
            self.assertEqual(len(callbacks), 1)
            ready[0] = True
            callbacks.pop(0)()
            self.assertEqual(len(self.payloads), 3)
            self.assertFalse(comparison.pending)
            self.assertTrue(all(form.isShowing() for form in comparison.forms))
            ready[0] = False
            second = self.styles_example.StyleComparison(callbacks.append)
            self.assertEqual(second.show(), 3)
            self.assertEqual(len(self.payloads), 4)
            with patch.object(second.forms[0], 'close') as close:
                second.close()
                close.assert_called_once_with(None)
            ready[0] = True
            callbacks.pop(0)()
            self.assertEqual(len(self.payloads), 4)
            self.assertFalse(second.pending)

    def test_custom_native_label_updates_use_snapshots_and_append_only_once(self):
        client = self.make_client()
        client.onCommand({'action': 'show'})
        session = client.session
        root = Node('/label-instance')
        root.child('label')
        root.child('detail')
        params = {'text': 'initial', 'history': [1], 'palette': {'color': [0.2, 0.2, 0.2]},
                  'sessionKey': session.key, 'appendOnCreate': True}
        # Client additions call appendFormControl locally, without a network event.
        with patch.object(self.system, 'appendFormControl', wraps=self.system.appendFormControl) as append:
            client.onLabelCreate(types.SimpleNamespace(control=root, params=params))
            self.assertEqual(root.children['label'].text, 'initial')
            self.assertTrue(session.createdAppend)
            self.assertEqual(append.call_count, 1)
            client.onLabelCreate(types.SimpleNamespace(control=root, params=params))
            self.assertEqual(append.call_count, 1)
        params['text'] = 'updated'
        params['palette'] = {'color': [0.05, 0.4, 0.65]}
        client.onLabelUpdate(types.SimpleNamespace(
            control=root, params=params, key='text', oldValue='initial', newValue='updated'))
        self.assertEqual(root.children['label'].text, 'updated')
        self.assertEqual(root.children['label'].color, (0.05, 0.4, 0.65))
        self.assertEqual(root.children['detail'].text, 'text：initial -> updated')

    def test_custom_label_receives_list_from_serialized_showcase(self):
        client = self.make_client()
        client.onCommand({'action': 'show'})
        payload = self.payloads[0]
        unwrap = sys.modules[self.prefix + '.utils.type'].unwrapWrappedValue
        group = next(control for control in payload['controls'] if 'children' in control)
        custom = next(control for control in payload['controls']
                      if control.get('params', {}).get('appendOnCreate', {}).get('value'))
        root = Node('/serialized-label')
        root.child('label')
        root.child('detail')
        for params in (group['children']['custom']['params'], custom['params']):
            snapshot = unwrap(params)
            self.assertEqual(snapshot['history'], client.session.history.getValue())
            client.renderLabel(root, snapshot)
            self.assertEqual(root.children['detail'].text, '列表长度：1')

    def test_custom_label_reports_invalid_history_without_aborting_creation(self):
        client = self.make_client()
        client.onCommand({'action': 'show'})
        original = list(client.session.history.getValue())
        root = Node('/invalid-label')
        root.child('label')
        root.child('detail')
        for history in (True, False):
            with self.subTest(history=history):
                output = io.StringIO()
                with patch('sys.stdout', output):
                    client.onLabelCreate(types.SimpleNamespace(
                        control=root, params={'text': 'test', 'history': history}))
                self.assertIn('history 类型异常：bool', root.children['detail'].text)
                self.assertIn('invalid history', output.getvalue())
                self.assertIn('sourceId=%r' % client.session.history._id, output.getvalue())
                self.assertIn('sourceValue=%r' % original, output.getvalue())
                self.assertEqual(client.session.history.getValue(), original)

    def test_inscribed_square_vertices_are_on_outer_edges_for_all_angles(self):
        for angle in range(-360, 721):
            outer, inner = self.client_example.square_sizes(angle, 120)
            self.assertGreaterEqual(inner, outer / math.sqrt(2) - 1e-10)
            self.assertLessEqual(inner, outer + 1e-10)
            theta = math.radians(angle)
            for x, y in ((-inner/2, -inner/2), (-inner/2, inner/2),
                         (inner/2, -inner/2), (inner/2, inner/2)):
                # Transform each stationary vertex into rotating-square coordinates.
                local_x = x * math.cos(theta) + y * math.sin(theta)
                local_y = -x * math.sin(theta) + y * math.cos(theta)
                self.assertAlmostEqual(max(abs(local_x), abs(local_y)), outer / 2)

    def test_animation_button_frames_pause_manual_angle_and_stale_instance(self):
        client = self.make_client()
        client.showAnimation()
        state = client.animation
        root = Node('/animation')
        canvas = root.child('canvas', (240, 168))
        outer, inner = canvas.child('rotating'), canvas.child('fixed')
        root.child('angle')
        button = root.child('play').child('button')
        for name in ('default', 'hover', 'pressed'):
            button.child(name).child('label')
        frames = Frames()
        params = {'instanceKey': 'standalone', 'angle': 0.0, 'running': False}
        for key in ('angle', 'running'):
            def changed(new, key=key):
                previous = params[key]
                params[key] = new
                client.onSquaresUpdate(types.SimpleNamespace(
                    control=root, params=dict(params), key=key, oldValue=previous, newValue=new))
            state[key].subscribe(changed)
        client.onSquaresCreate(types.SimpleNamespace(control=root, screenNode=frames, params=dict(params)))
        frames.tick()
        self.assertEqual(outer.angle, 0)
        button.click({})
        frames.tick()
        self.assertEqual((outer.angle, inner.angle), (2, 0))
        self.assertEqual(state['angle'].getValue(), 2)
        self.assertEqual(len(frames.pending), 1)
        button.click({})
        frames.tick()
        self.assertEqual(outer.angle, 2)
        state['angle'].setValue(45)
        self.assertAlmostEqual(inner.size[0], outer.size[0] / math.sqrt(2))
        canvas.size = (120, 168)
        frames.tick()
        self.assertAlmostEqual(outer.size[0], 79.2)
        client.forgetMotion('standalone')
        frames.tick()
        self.assertEqual(frames.pending, [])

    def test_texture_is_exact_white_outline_with_transparent_interior(self):
        png = (ROOT / 'resource/textures/ui/square.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        offset, compressed, dimensions = 8, bytearray(), None
        while offset < len(png):
            size = struct.unpack('>I', png[offset:offset+4])[0]
            kind = png[offset+4:offset+8]
            data = png[offset+8:offset+8+size]
            if kind == b'IHDR':
                dimensions = struct.unpack('>IIBBBBB', data)
            elif kind == b'IDAT':
                compressed.extend(data)
            offset += 12 + size
        self.assertEqual(dimensions, (256, 256, 8, 6, 0, 0, 0))
        rows = zlib.decompress(compressed)
        for y in range(256):
            self.assertEqual(rows[y*1025], 0)
            for x in range(256):
                pixel = rows[y*1025+1+x*4:y*1025+5+x*4]
                alpha = 255 if min(x, y, 255-x, 255-y) < 4 else 0
                self.assertEqual(pixel, bytes((255, 255, 255, alpha)))

    def test_ui_definitions_include_templates_and_texture(self):
        definitions = json.loads((ROOT / 'resource/ui/_ui_defs.json').read_text())
        self.assertIn('ui/fui_examples.json', definitions['ui_defs'])
        templates = json.loads((ROOT / 'resource/ui/fui_examples.json').read_text())
        self.assertEqual(templates['square_image']['texture'], 'textures/ui/square')
        self.assertEqual(templates['square_image']['rotate_pivot'], [0.5, 0.5])


if __name__ == '__main__':
    unittest.main()
