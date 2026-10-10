"""Validate Fluent resources and the requested close-only window title bar."""
import unittest
import test_flutter_ui as themes


class FluentUITests(themes.FlutterUITests):
    style_name = 'fluent'
    registration_class = 'FluentUI'
    primary_button = 'primary_button'
    switch_size = [20, 10]
    asset_count = 13

    def test_title_bar_contains_only_close_button_and_red_hover_feedback(self):
        for theme, prefix in (('light', ''), ('dark', 'dark_')):
            root = self.resolve('fui_fluent.' + theme + '_panel')
            header = self.child(root, '/header')
            buttons = []
            for entry in header['controls']:
                name = next(iter(entry)).split('@')[0]
                child = self.child(header, '/' + name)
                if child['type'] == 'button':
                    buttons.append(name)
            self.assertEqual(buttons, ['close'])
            self.assertEqual(self.child(header, '/title')['type'], 'label')
            self.child(root, '/body/background')
            self.child(root, '/border')
            close = self.child(header, '/close')
            self.assertEqual(self.child(close, '/hover/background')['color'],
                             [0.768627, 0.168627, 0.109804])
            self.assertEqual(self.child(close, '/hover/icon')['color'], [1, 1, 1])
            self.assertIn('fui_fluent.' + prefix + 'scroll', self.templates)

    def test_default_fonts_and_thin_control_corners_fit(self):
        def visit(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ('font_scale_factor', '$font_scale_factor'):
                        self.assertGreaterEqual(value, 1.0)
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)
        for reference, (_, _, template) in self.templates.items():
            if reference.startswith('fui_fluent.'):
                visit(template)
        for prefix in ('', 'dark_'):
            switch = self.resolve('fui_fluent.' + prefix + 'switch_checked')
            track = self.child(switch, '/track')
            self.assertLessEqual(sum(track['nineslice_size'][::2]), self.switch_size[1])
            slider = self.resolve('fui_fluent.' + prefix + 'slider_native')
            track = self.child(slider, '/track')
            self.assertLessEqual(sum(track['nineslice_size'][::2]), track['size'][1])


if __name__ == '__main__':
    unittest.main()
