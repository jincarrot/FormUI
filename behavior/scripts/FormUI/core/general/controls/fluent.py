# -*- coding: utf-8 -*-
"""Fluent Qt inspired controls, registered during client UI initialization."""

BUTTON_OPTIONS = {
    'buttonPath': '/button',
    'labelPaths': ('/default/label', '/hover/label', '/pressed/label'),
}
CONTROL_DEFINITIONS = (
    ('primary_button', 'button', BUTTON_OPTIONS),
    ('button', 'button', BUTTON_OPTIONS),
    ('outlined_button', 'button', BUTTON_OPTIONS),
    ('hyperlink_button', 'button', BUTTON_OPTIONS),
    ('danger_button', 'button', BUTTON_OPTIONS),
    ('label', 'label', {'labelPaths': ['/label']}),
    ('divider', 'divider', {}),
    ('toggle', 'toggle', {'togglePath': '/toggle/this_toggle', 'labelPaths': ['/label']}),
    ('slider', 'slider', {'sliderPath': '/slider', 'labelPaths': ['/label'], 'valuePaths': ['/value']}),
    ('textfield', 'textfield', {'textfieldPath': '/textfield', 'labelPaths': ['/label']}),
    ('dropdown', 'dropdown', {
        'dropdownPath': '/dropdown_box', 'contentPath': '/content_panel', 'labelPaths': ['/label'],
        'boxLabelPaths': ['/default/label', '/hover/label', '/pressed/label'],
        'itemLabelPaths': ['/button_label'], 'itemControl': 'fui_fluent.dropdown_item',
    }),
)


class FluentUI(object):
    """Register light/dark themes; window title bars contain only a close button."""

    def __init__(self):
        from copy import deepcopy
        from ...utils.environment import getClientSystem
        manager = getClientSystem().controlManager
        for prefix in ('', 'dark_'):
            for name, controlType, options in CONTROL_DEFINITIONS:
                identifier = prefix + name
                instanceOptions = deepcopy(options)
                if controlType == 'dropdown':
                    instanceOptions['itemControl'] = 'fui_fluent.' + prefix + 'dropdown_item'
                manager.create(controlType, 'fluent:' + identifier,
                               'fui_fluent.' + identifier, instanceOptions)
        for theme in ('light', 'dark'):
            name = theme + '_panel'
            manager.create('scrolling_panel', 'fluent:' + name, 'fui_fluent.' + name, {
                'scrollingPanelPath': '/content', 'titlePath': '/header/title',
                'closeBtnPath': '/header/close',
            })
