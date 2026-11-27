# -*- coding: utf-8 -*-
"""The native structure shared by the desktop exporter and the game client."""
from collections import namedtuple
import re

from .ui import STRING_TYPES, getFormContentPath


_RESOURCE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\Z')
BODY_MARKER = '_formui_body_v1'
BODY_CHILD = '_formui_content'
ROWS_MARKER = '_formui_rows_v1'
DEFAULT_CONTENT = 'fui_ore_panels.scrolling_content'
TemplateStructure = namedtuple('TemplateStructure', 'panel nodes contentPath')
TemplateNode = namedtuple('TemplateNode', 'slot path kind rowPath children')


def validateTemplateName(name):
    if not isinstance(name, STRING_TYPES) or not _RESOURCE.match(name):
        raise ValueError('Expected a JSON UI identifier such as my_forms.settings')
    return name


def templateStructure(manager, base, controls):
    """Describe native types and addresses. Instance values and callback IDs are independent."""
    def node(slot, className, parents):
        cls = manager.get(className)
        if cls is None:
            raise ValueError('Unregistered control: %s' % className)
        children = []
        if cls.typeId == 'group':
            if className in parents:
                raise ValueError('Circular Group reference: %s' % className)
            for name, definition in sorted(cls.options['controls'].items()):
                if '@' in name or '/' in name:
                    raise ValueError('Invalid JSON UI child name: %s' % name)
                children.append(node(name, definition['class']['value'], parents + (className,)))
        return TemplateNode(slot, cls.path, cls.typeId, cls.options.get('itemControl', ''), children)

    nodes = [node('c%s' % i, entry['style']['class']['value'], ())
             for i, entry in enumerate(controls)]
    contentPath = getFormContentPath(base) if base.typeId == 'panel' else None
    return TemplateStructure(base.path, nodes, contentPath)


def _digest(value):
    import hashlib
    import json
    # ASCII canonical JSON gives Python 2 in-game and Python 3 on the desktop the same key.
    encoded = json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()[:24]


def templateKey(name, structure):
    signature = (structure.panel, structure.nodes)
    # Scroll roots retain the same identifiers used by existing resource packs.
    if structure.contentPath is not None:
        signature += (structure.contentPath,)
    return '%s__formui_v1_%s' % (name, _digest(signature))


def rowTemplateKey(windowKey, rowPath, count):
    namespace = windowKey.split('.')[0]
    return '%s._formui_rows_%s' % (namespace, _digest([windowKey, rowPath, count]))


def _panel(controls):
    return {'type': 'input_panel', 'is_swallow': True, 'anchor_from': 'top_left', 'anchor_to': 'top_left',
            'size': ['100%', '100%'], 'controls': controls}


def _marker(name):
    return {name: {'type': 'input_panel', 'is_swallow': True, 'size': [0, 0], 'visible': False}}


def exportTemplate(name, structure, controls):
    namespace, public = validateTemplateName(name).split('.')
    fullKey = templateKey(name, structure)
    key = fullKey.split('.')[1]
    body = key + '_body'
    bodyReference = namespace + '.' + body
    rootProperties = {'$formui_content': bodyReference}
    if structure.panel == 'fui.panel' and structure.contentPath == '':
        rootProperties['controls'] = [{BODY_CHILD + '@' + bodyReference: {}}]
    document = {
        'namespace': namespace,
        public + '@' + structure.panel: rootProperties,
        key + '@' + name: {},
    }

    def emit(node, data):
        slot, path, kind, rowPath, children = node
        properties = {}
        if kind == 'group' and children:
            instances = data.get('children', {})
            entries = [emit(child, instances.get(child.slot, {})) for child in children]
            if path == 'fui.group':
                properties['controls'] = entries
            else:
                # Preserve decorations and other controls provided by custom Group templates.
                properties['modifications'] = [
                    {'array_name': 'controls', 'operation': 'insert_back', 'value': entries}]
        elif kind in ('listview', 'dropdown'):
            items = data.get('items', [])
            count = len(items['value'] if isinstance(items, dict) else items)
            fullRowKey = rowTemplateKey(fullKey, rowPath, count)
            rowKey = fullRowKey.split('.')[1]
            if rowKey not in document and (count or kind == 'listview'):
                rows = [{'row_%s@%s' % (i, rowPath): {}} for i in range(count)]
                document[rowKey] = _panel([_marker(ROWS_MARKER)] + rows)
                document[rowKey]['$formui_content'] = DEFAULT_CONTENT
            if kind == 'listview':
                properties['$formui_content'] = fullRowKey
        return {slot + '@' + path: properties}

    entries = [emit(node, data) for node, data in zip(structure.nodes, controls)]
    document[body] = _panel([_marker(BODY_MARKER)] + entries)
    # Nested scrolling panels have their own contents, including custom descendants.
    document[body]['$formui_content'] = DEFAULT_CONTENT
    return document
