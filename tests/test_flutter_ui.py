"""Validate built-in theme registration, SDK paths and shipped texture assets."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

import test_group_controls as fixture

ROOT = Path(__file__).resolve().parents[1]


class FlutterUITests(unittest.TestCase):
    style_name = 'flutter'
    registration_class = 'FlutterUI'
    primary_button = 'filled_button'
    switch_size = [19.55, 11.05]
    asset_count = 11

    def setUp(self):
        self.fixture = fixture.GroupControlTests()
        self.fixture.setUp()
        name = self.fixture.prefix + '.general.controls.' + self.style_name
        spec = importlib.util.spec_from_file_location(name, ROOT / (
            'behavior/scripts/FormUI/core/general/controls/' + self.style_name + '.py'))
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[name] = self.module
        self.fixture.modules.append(name)
        manager = self.fixture.system.controlManager
        with patch.object(manager, 'create', wraps=manager.create) as create:
            spec.loader.exec_module(self.module)
            self.assertEqual(create.call_count, 0)  # No registration during imports.
            getattr(self.module, self.registration_class)()
            self.assertEqual(create.call_count, 24)
        self.manager = manager
        self.templates = {}
        definitions = json.loads((ROOT / 'resource/ui/_ui_defs.json').read_text())
        self.assertIn('ui/' + self.style_name + '.json', definitions['ui_defs'])
        for file in definitions['ui_defs']:
            data = json.loads((ROOT / 'resource' / file).read_text(encoding='utf-8'))
            for name, template in data.items():
                if name == 'namespace':
                    continue
                self.templates[data['namespace'] + '.' + name.split('@')[0]] = (data['namespace'], name, template)

    def tearDown(self):
        self.fixture.tearDown()

    def resolve(self, reference, chain=()):
        if reference not in self.templates:  # Engine-provided native template.
            return {}
        self.assertNotIn(reference, chain)
        namespace, name, template = self.templates[reference]
        result = {}
        if '@' in name:
            base = name.split('@')[1]
            if '.' not in base:
                base = namespace + '.' + base
            result.update(self.resolve(base, chain+(reference,)))
        result.update(copy.deepcopy(template))
        return result

    def child(self, parent, path, namespace=None):
        namespace = namespace or 'fui_' + self.style_name
        node = parent
        for segment in path.strip('/').split('/'):
            child = next((entry for entry in node.get('controls', [])
                          if next(iter(entry)).split('@')[0] == segment), None)
            self.assertIsNotNone(child, path)
            name, override = next(iter(child.items()))
            node = {}
            if '@' in name:
                base = name.split('@')[1]
                if '.' not in base:
                    base = namespace + '.' + base
                node.update(self.resolve(base))
            node.update(override)
        return node

    def test_all_registered_templates_and_native_control_paths_exist(self):
        for control in self.manager.getRegisteredData():
            if not control['name'].startswith(self.style_name + ':'):
                continue
            with self.subTest(control=control['name']):
                self.assertIn(control['path'], self.templates)
                root = self.resolve(control['path'])
                options = control['options']
                if control['type'] == 'button':
                    native = self.child(root, options['buttonPath'])
                    self.assertEqual(native['type'], 'button')
                    for path in options['labelPaths']:
                        self.assertEqual(self.child(native, path)['type'], 'label')
                elif control['type'] == 'scrolling_panel':
                    self.child(root, options['scrollingPanelPath'])
                    self.assertEqual(self.child(root, options['titlePath'])['type'], 'label')
                    self.assertEqual(self.child(root, options['closeBtnPath'])['type'], 'button')
                elif control['type'] == 'dropdown':
                    native = self.child(root, options['dropdownPath'])
                    self.assertEqual(native['type'], 'button')
                    self.assertFalse(self.child(root, options['contentPath'])['visible'])
                    for path in options['boxLabelPaths']:
                        self.child(native, path)
                    self.assertIn(options['itemControl'], self.templates)
                    item = self.resolve(options['itemControl'])
                    for path in options['itemLabelPaths']:
                        self.child(item, path)
                elif control['type'] == 'toggle':
                    # /this_toggle comes from the engine's common_toggles.switch_toggle.
                    native = self.child(root, '/toggle')
                    self.assertEqual(native['size'], self.switch_size)
                    for key in ('$checked_control', '$unchecked_control'):
                        self.assertIn(native[key], self.templates)
                elif control['type'] in ('slider', 'textfield'):
                    path = options['sliderPath' if control['type'] == 'slider' else 'textfieldPath']
                    self.assertEqual(self.child(root, path)['type'],
                                     'slider' if control['type'] == 'slider' else 'edit_box')
                for path in options.get('labelPaths', []):
                    if control['type'] != 'button':
                        self.child(root, path)

    def test_local_inheritance_and_visual_references_resolve(self):
        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if '@' in key:
                        base = key.split('@')[1]
                        if '.' not in base:
                            base = 'fui_' + self.style_name + '.' + base
                        if base.startswith(('fui_' + self.style_name + '.', 'fui_ore_', 'fui.')):
                            self.assertIn(base, self.templates)
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str) and value.startswith(('fui_' + self.style_name + '.', 'fui_ore_')):
                self.assertIn(value, self.templates)
        for reference, (_, name, template) in self.templates.items():
            if reference.startswith('fui_' + self.style_name + '.'):
                self.resolve(reference)
                visit({name: template})

    def test_texture_files_are_valid_and_nine_slice_corners_fit(self):
        ui = json.loads((ROOT / ('resource/ui/' + self.style_name + '.json')).read_text())
        assets = set()
        def visit(value):
            if isinstance(value, dict):
                if str(value.get('texture', '')).startswith('textures/ui/' + self.style_name + '/'):
                    assets.add(value['texture'])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(ui)
        self.assertEqual(len(assets), self.asset_count)
        for asset in assets:
            path = ROOT / 'resource' / (asset+'.png')
            data = path.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width, height = struct.unpack('>II', data[16:24])
            compressed = bytearray()
            offset = 8
            while offset < len(data):
                length = struct.unpack('>I', data[offset:offset+4])[0]
                kind = data[offset+4:offset+8]
                payload = data[offset+8:offset+8+length]
                self.assertEqual(struct.unpack('>I', data[offset+8+length:offset+12+length])[0],
                                 zlib.crc32(kind+payload) & 0xffffffff)
                if kind == b'IDAT':
                    compressed.extend(payload)
                offset += length+12
            pixels = zlib.decompress(compressed)
            self.assertEqual(len(pixels), height*(1+width*4))
            self.assertLess(pixels[4], 255)  # Transparent/antialiased corners.
            meta = path.with_suffix('.json')
            if meta.exists():
                metadata = json.loads(meta.read_text())
                self.assertEqual(metadata['base_size'], [width/4, height/4])
                self.assertLess(max(metadata['nineslice_size'])*2, min(metadata['base_size']))

    def test_theme_options_are_independent_and_reregistration_keeps_other_styles(self):
        light = self.manager.get(self.style_name + ':' + self.primary_button)
        dark = self.manager.get(self.style_name + ':dark_' + self.primary_button)
        light.options['labelPaths'] = ['changed']
        self.assertEqual(dark.options['labelPaths'][0], '/default/label')
        existing = self.manager.get('button')
        getattr(self.module, self.registration_class)()
        self.assertIs(self.manager.get('button'), existing)
        self.assertEqual(self.manager.get(self.style_name + ':' + self.primary_button).options['labelPaths'][0], '/default/label')

    def test_dropdown_rows_start_at_menu_top_when_menu_height_increases(self):
        for prefix in ('', 'dark_'):
            control = self.manager.get(self.style_name + ':' + prefix + 'dropdown')
            item = self.resolve(control.options['itemControl'])
            self.assertEqual(item['anchor_from'], 'top_middle')
            self.assertEqual(item['anchor_to'], 'top_middle')
            self.assertEqual(item['offset'], [0, 0])
            # Center anchors would add (menuHeight - rowHeight) / 2 to every row.
            # Top anchors keep the first row at zero for one or many options.
            row_height = item['size'][1]
            for count in (1, 3, 8):
                menu_height = count * row_height + 2
                fractions = {'top_middle': 0, 'center': .5}
                anchor_offset = (fractions[item['anchor_from']] * menu_height
                                 - fractions[item['anchor_to']] * row_height)
                positions = [anchor_offset + index * row_height for index in range(count)]
                self.assertEqual(positions[0], 0)
                self.assertEqual(positions[-1] + row_height, menu_height - 2)

    def test_switch_textures_have_circular_ends_without_nine_slice_scaling(self):
        for prefix in ('', 'dark_'):
            for checked in ('checked', 'unchecked'):
                for hover in ('', '_hover'):
                    visual = self.resolve('fui_' + self.style_name + '.' + prefix + 'switch_' + checked + hover)
                    for name in ('track', 'outline') if checked == 'unchecked' else ('track',):
                        image = self.child(visual, '/' + name)
                        self.assertEqual(image['nineslice_size'], [0, 0, 0, 0])
                        self.assertNotIn('base_size', image)
                        self.assertFalse(image['keep_ratio'])
        path = ROOT / 'resource/textures/ui' / self.style_name / 'switch.png'
        data = path.read_bytes()
        width, height = struct.unpack('>II', data[16:24])
        self.assertAlmostEqual(width/height, self.switch_size[0]/self.switch_size[1])
        self.assertGreaterEqual(height, self.switch_size[1]*4)
        compressed = bytearray()
        offset = 8
        while offset < len(data):
            length = struct.unpack('>I', data[offset:offset+4])[0]
            if data[offset+4:offset+8] == b'IDAT':
                compressed.extend(data[offset+8:offset+8+length])
            offset += length+12
        pixels = zlib.decompress(compressed)
        # A quarter-height scanline intersects a circular cap near the left
        # edge. A pointed/diamond end would start much farther to the right.
        row = height//4
        row_start = row*(width*4+1)
        self.assertEqual(pixels[row_start], 0)
        left = next(x for x in range(width) if pixels[row_start+1+x*4+3] >= 128)
        radius = height/2
        expected = radius-math.sqrt(radius**2-(row+.5-radius)**2)
        self.assertLessEqual(abs(left-expected), 1)


if __name__ == '__main__':
    unittest.main()
