"""Public style imports remain independent of game systems and match registrars."""
import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / 'behavior/scripts/FormUI/core/general/controls'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InnerStylesTests(unittest.TestCase):
    def test_every_flutter_and_fluent_registration_has_a_style_constant(self):
        styles = load('builtin_style_constants', CONTROLS / 'innerStyles.py')
        for name, cls in (('flutter', styles.FlutterStyles), ('fluent', styles.FluentStyles)):
            registrar = load('builtin_' + name, CONTROLS / (name + '.py'))
            expected = {name + ':' + prefix + control[0]
                        for prefix in ('', 'dark_') for control in registrar.CONTROL_DEFINITIONS}
            expected.update((name + ':light_panel', name + ':dark_panel'))
            constants = {value for key, value in vars(cls).items() if not key.startswith('_')}
            self.assertEqual(constants, expected)
            self.assertIsInstance(getattr(styles.InnerStyles, name), cls)
        self.assertEqual(styles.InnerStyles.oreui.GreenBtn, 'oreui:green_btn_thin')

    def test_public_module_and_lib_exports_have_identical_objects_without_native_imports(self):
        script = textwrap.dedent('''
            import builtins, sys, types
            original_import = builtins.__import__
            def guard(name, *args, **kwargs):
                if name == 'mod' or name.startswith('mod.'):
                    raise AssertionError('style imports must not load game APIs: ' + name)
                return original_import(name, *args, **kwargs)
            builtins.__import__ = guard
            from FormUI import innerStyles
            from FormUI.innerStyles import InnerStyles, OreUIStyles, FlutterStyles, FluentStyles
            from FormUI.core.general.controls import innerStyles as original
            for name in innerStyles.__all__:
                assert getattr(innerStyles, name) is getattr(original, name)
            assert InnerStyles.flutter.DarkToggle == 'flutter:dark_toggle'
            assert InnerStyles.fluent.PrimaryBtn == 'fluent:primary_button'
            # Replace the existing lib bootstrap while testing its real exports.
            # Standalone innerStyles import above required no such replacement.
            environment = types.ModuleType('FormUI.core.utils.environment')
            environment.isServer = lambda: False
            sys.modules[environment.__name__] = environment
            sys.modules['register'] = types.ModuleType('register')
            from FormUI import lib
            for name in innerStyles.__all__:
                assert getattr(lib, name) is getattr(innerStyles, name)
        ''')
        result = subprocess.run([sys.executable, '-S', '-B', '-c', script],
                                env=dict(os.environ, PYTHONPATH=str(ROOT / 'behavior/scripts')),
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_literal_type_annotations_match_runtime_constants(self):
        styles = load('builtin_style_constants', CONTROLS / 'innerStyles.py')
        tree = ast.parse((CONTROLS / 'innerStyles.pyi').read_text(encoding='utf-8'))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name == 'InnerStyles':
                continue
            cls = getattr(styles, node.name)
            annotations = {field.target.id: ast.literal_eval(field.annotation.slice.slice)
                           for field in node.body if isinstance(field, ast.AnnAssign)}
            constants = {key: value for key, value in vars(cls).items() if not key.startswith('_')}
            self.assertEqual(annotations, constants)


if __name__ == '__main__':
    unittest.main()
