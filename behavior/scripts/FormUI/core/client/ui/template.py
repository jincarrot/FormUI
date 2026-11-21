# -*- coding: utf-8 -*-
from ...utils.template import BODY_MARKER, ROWS_MARKER, rowTemplateKey, templateKey, templateStructure, validateTemplateName
from ...utils.ui import getScrollingContent


def mountTemplate(screen, form, parent, rootName, base):
    request = form['template']
    count = request['count']
    root = None
    try:
        name = validateTemplateName(request['name'])
        if not 0 <= count <= len(form['controls']):
            raise ValueError('invalid compiled control count')
        structure = templateStructure(screen.controlManager, form['style']['class']['value'],
                                      form['controls'][:count])
        key = templateKey(name, structure)
        root = screen.CreateChildControl(key, rootName, parent)
        if not root:
            raise ValueError('matching resource not found')
        scrollPath = base.options['scrollingPanelPath']
        scroll = root.GetChildByPath(scrollPath) if scrollPath else root
        content = getScrollingContent(scroll) if scroll else None
        if not content:
            raise ValueError('scrolling content not found')
        body = content
        if not body.GetChildByPath('/' + BODY_MARKER):
            # A custom scrolling panel may supply its own fixed content template.
            if (content.GetChildByPath('/_formui_content') or
                    any(content.GetChildByPath('/' + node.slot) for node in structure.nodes)):
                raise ValueError('native content already uses a compiled control name')
            body = screen.CreateChildControl(key + '_body', '_formui_content', content)
            if not body or not body.GetChildByPath('/' + BODY_MARKER):
                raise ValueError('missing FormUI template marker')

        natives = {}
        def collect(node, address, owner):
            native = owner.GetChildByPath('/' + node.slot)
            if not native:
                raise ValueError('missing native control at %s' % (address,))
            natives[address] = native
            prefix = address if isinstance(address, tuple) else (address,)
            for child in node.children:
                collect(child, prefix + (child.slot,), native)
        for index, node in enumerate(structure.nodes):
            collect(node, index, body)
        # Publish only after the whole tree has been resolved, before any user callbacks.
        form['_compiledKey'] = key
        form['_compiledParent'] = body
        form['_compiledNodes'] = natives
        return root
    except Exception as error:
        if root and screen.RemoveChildControl(root) is False:
            raise RuntimeError('Could not remove invalid FormUI template %s' % request['name'])
        print('[FormUI] Using dynamic controls for %s: %s' % (request['name'], error))
        return None


def mountMenuRows(screen, content, windowKey, rowPath, count):
    """Keep the registered menu panel and its decoration. Mount its options in one call."""
    if content.GetChildByPath('/_formui_options'):
        return None
    group = None
    try:
        group = screen.CreateChildControl(rowTemplateKey(windowKey, rowPath, count), '_formui_options', content)
        if group and group.GetChildByPath('/' + ROWS_MARKER):
            rows = [group.GetChildByPath('/row_%s' % i) for i in range(count)]
            if all(rows):
                return rows
    except Exception as error:
        print('[FormUI] Using dynamic dropdown rows: %s' % error)
    if group and screen.RemoveChildControl(group) is False:
        raise RuntimeError('Could not remove invalid FormUI dropdown rows')
    return None
