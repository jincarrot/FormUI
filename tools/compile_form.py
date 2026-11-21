"""Export a FormUI Python factory as a reusable Bedrock JSON UI control."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class BuildSystem:
    """Use the real FormUI builders and registries without starting the game."""

    def NotifyToServer(self, event, data):
        if event != 'setDefaultStyle':
            raise ValueError('Game network calls are unavailable while compiling a form')

    def applyObservableUpdate(self, data):
        self.controlManager.applyObservableUpdate(data['id'], data['value'])


def install_build_system():
    sys.path.insert(0, str(ROOT / 'behavior' / 'scripts'))
    from FormUI.core.utils import environment
    system = BuildSystem()
    environment.registerSystem = lambda: None
    environment.isServer = lambda: False
    environment.getSystem = environment.getClientSystem = lambda: system

    from FormUI.core.general.managers.form import FormManager
    from FormUI.core.general.managers.control import ControlManager
    from FormUI.core.general.managers.observable import ObservableManager
    from FormUI.core.general.screen import Screen
    system.screen = Screen()
    system.formManager = FormManager()
    system.controlManager = ControlManager()
    system.observableManager = ObservableManager()

    # OreUI registers on import. The other two follow the client's UIInit order.
    from FormUI.core.general.controls import oreui
    from FormUI.core.general.controls.flutter import FlutterUI
    from FormUI.core.general.controls.fluent import FluentUI
    FlutterUI()
    FluentUI()
    from FormUI import lib
    sys.modules['scripts.FormUI'] = sys.modules['FormUI']
    sys.modules['scripts.FormUI.lib'] = lib


def load_entry(source, entry_name):
    source = source.resolve(strict=True)
    parts = [source.stem]
    directory = source.parent
    while (directory / '__init__.py').is_file():
        parts.insert(0, directory.name)
        directory = directory.parent
    sys.path[:0] = [str(directory), str(source.parent), str(ROOT / 'behavior')]
    # Use the named source even when another package has a module with the same name.
    module_name = '.'.join(parts)
    if len(parts) > 1:
        importlib.import_module('.'.join(parts[:-1]))
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ValueError('Expected a Python source file: %s' % source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    entry = module
    for part in entry_name.split('.'):
        entry = getattr(entry, part)
    return entry


def build(source, entry_name, name, args, kwargs):
    from FormUI.core.general.form import Form
    entry = load_entry(source, entry_name)
    if isinstance(entry, Form):
        if args or kwargs:
            raise ValueError('Factory arguments cannot be used with a Form variable')
        result = entry
    else:
        result = entry(*args, **kwargs)
    results = result if isinstance(result, (list, tuple)) else (result,)
    forms = [value for value in results if isinstance(value, Form)]
    if len(forms) != 1:
        raise ValueError('The factory must return one Form, optionally alongside its state')
    return forms[0].toJsonUI(name)


def write_json(path, value, indent=2):
    encoded = (json.dumps(value, indent=indent, ensure_ascii=False) + '\n').encode('utf-8')
    if path.is_file() and path.read_bytes() == encoded:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    temporary = Path(temp.name)
    try:
        with temp:
            temp.write(encoded)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def pack_lock(pack):
    # Serialize read/merge/write across CLI processes without shipping a lock file in the pack.
    digest = hashlib.sha256(os.fsencode(os.path.normcase(str(pack)))).hexdigest()
    lock = Path(tempfile.gettempdir()) / ('formui-' + digest + '.lock')
    with lock.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            if stream.tell() == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def save(pack, name, document):
    pack = pack.resolve(strict=True)
    namespace, control = name.split('.')
    resource = 'ui/formui_generated/%s/%s.json' % (namespace, control)
    output = pack / resource
    definitions = pack / 'ui' / '_ui_defs.json'
    with pack_lock(pack):
        manifest = json.loads(definitions.read_text(encoding='utf-8-sig')) if definitions.exists() else {'ui_defs': []}
        if not isinstance(manifest, dict) or not isinstance(manifest.get('ui_defs'), list):
            raise ValueError('Expected a ui_defs array in %s' % definitions)
        if output.exists():
            previous = json.loads(output.read_text(encoding='utf-8-sig'))
            # Both the versioned window and its body belong to this public control.
            if (not isinstance(previous, dict) or previous.get('namespace') != namespace
                    or not any(key.startswith(control + '__formui_v1_') and key.endswith('_body')
                               for key in previous)):
                raise ValueError('Output belongs to a different control: %s' % output)
        write_json(output, document)
        if resource not in manifest['ui_defs']:
            manifest['ui_defs'].append(resource)
            write_json(definitions, manifest, indent=4)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Python file containing the form factory')
    parser.add_argument('entry', help='Factory function or Form variable, e.g. create_settings')
    parser.add_argument('name', help='JSON UI identifier, e.g. my_forms.settings')
    parser.add_argument('--resource-pack', type=Path, default=ROOT / 'resource')
    parser.add_argument('--args', type=json.loads, default=[], help='Positional arguments as a JSON array')
    parser.add_argument('--kwargs', type=json.loads, default={}, help='Keyword arguments as a JSON object')
    options = parser.parse_args()
    if not isinstance(options.args, list) or not isinstance(options.kwargs, dict):
        parser.error('--args must be a JSON array and --kwargs must be a JSON object')
    # Importing user factories should not add bytecode to a shippable behavior pack.
    sys.dont_write_bytecode = True
    install_build_system()
    try:
        document = build(options.source, options.entry, options.name, options.args, options.kwargs)
        output = save(options.resource_pack, options.name, document)
    except (OSError, ImportError, AttributeError, TypeError, ValueError) as error:
        parser.exit(1, 'FormUI: %s\n' % error)
    print('%s -> %s' % (options.name, output))


if __name__ == '__main__':
    main()
