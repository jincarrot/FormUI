# -*- coding: utf-8 -*-
"""Material-inspired built-in controls; registered at client UI initialization."""

BUTTON_OPTIONS = {
    'buttonPath': '/button',
    'labelPaths': ('/default/label', '/hover/label', '/pressed/label'),
}
CONTROL_DEFINITIONS = (
    ('filled_button', 'button', BUTTON_OPTIONS),
    ('tonal_button', 'button', BUTTON_OPTIONS),
    ('outlined_button', 'button', BUTTON_OPTIONS),
    ('text_button', 'button', BUTTON_OPTIONS),
    ('danger_button', 'button', BUTTON_OPTIONS),
    ('label', 'label', {'labelPaths': ['/label']}),
    ('divider', 'divider', {}),
    ('toggle', 'toggle', {'togglePath': '/toggle/this_toggle', 'labelPaths': ['/label']}),
    ('slider', 'slider', {'sliderPath': '/slider', 'labelPaths': ['/label'], 'valuePaths': ['/value']}),
    ('textfield', 'textfield', {'textfieldPath': '/textfield', 'labelPaths': ['/label']}),
    ('dropdown', 'dropdown', {
        'dropdownPath': '/dropdown_box', 'contentPath': '/content_panel', 'labelPaths': ['/label'],
        'boxLabelPaths': ['/default/label', '/hover/label', '/pressed/label'],
        'itemLabelPaths': ['/button_label'], 'itemControl': 'fui_flutter.dropdown_item',
    }),
)


class FlutterUI(object):
    """Register light/dark native templates without changing global default styles."""

    def __init__(self):
        from copy import deepcopy
        from ...utils.environment import getClientSystem
        manager = getClientSystem().controlManager
        for prefix in ('', 'dark_'):
            for name, controlType, options in CONTROL_DEFINITIONS:
                identifier = prefix + name
                instanceOptions = deepcopy(options)
                if controlType == 'dropdown':
                    instanceOptions['itemControl'] = 'fui_flutter.' + prefix + 'dropdown_item'
                manager.create(controlType, 'flutter:' + identifier,
                               'fui_flutter.' + identifier, instanceOptions)
        for theme in ('light', 'dark'):
            name = theme + '_panel'
            manager.create('scrolling_panel', 'flutter:' + name, 'fui_flutter.' + name, {
                'scrollingPanelPath': '/content', 'titlePath': '/header/title',
                'closeBtnPath': '/header/close',
            })
