# -*- coding: utf-8 -*-
"""Theme snapshots. Registries belong to a Screen manager, never a shared module."""
from .type import copyContainers
from .ui import STRING_TYPES, _finiteNumber

BUILTIN_THEMES = ('oreui', 'flutter', 'flutter-dark', 'fluent', 'fluent-dark')
THEME_KINDS = ('scrolling_panel', 'button', 'toggle', 'label', 'divider',
               'slider', 'textfield', 'dropdown', 'listview')


def resolveTheme(theme):
    if theme is None:
        return {}
    try:
        strings = (basestring,)
    except NameError:
        strings = (str,)
    supported = BUILTIN_THEMES
    if not isinstance(theme, strings) or theme not in supported:
        raise ValueError('theme must be one of: %s' % ', '.join(supported))
    if theme == 'oreui':
        return {
            'scrolling_panel': 'oreui:light_panel_thin', 'button': 'oreui:normal_btn_thin',
            'toggle': 'oreui:toggle_thin', 'label': 'oreui:label', 'divider': 'oreui:divider_in',
            'slider': 'oreui:slider', 'textfield': 'oreui:textfield',
            'dropdown': 'oreui:dropdown', 'listview': 'oreui:listview',
        }
    namespace = theme.split('-')[0]
    prefix = 'dark_' if theme.endswith('-dark') else ''
    classes = {kind: namespace + ':' + prefix + kind
               for kind in ('toggle', 'label', 'divider', 'slider', 'textfield', 'dropdown', 'listview')}
    classes['button'] = namespace + ':' + prefix + ('filled_button' if namespace == 'flutter' else 'primary_button')
    classes['scrolling_panel'] = namespace + ':' + ('dark_panel' if prefix else 'light_panel')
    return classes


def _plain(value):
    """Themes are reusable static data; instance bindings belong in Form styles."""
    if value is None or isinstance(value, STRING_TYPES) or isinstance(value, bool):
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _plain(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, STRING_TYPES):
                raise TypeError('theme style keys must be strings')
            _plain(item)
    else:
        _finiteNumber(value, 'theme style value')


class ThemeRegistry(object):
    def __init__(self):
        self._themes = {}

    def get(self, name):
        if not isinstance(name, STRING_TYPES):
            raise ValueError('theme name must be a string')
        if name in BUILTIN_THEMES:
            return {kind: {'class': cls} for kind, cls in resolveTheme(name).items()}
        if name not in self._themes:
            raise ValueError('Unknown theme: %s' % name)
        return copyContainers(self._themes[name])

    def register(self, name, styles, base='oreui', replace=False):
        if not isinstance(name, STRING_TYPES) or not name.strip():
            raise ValueError('theme name must be a nonempty string')
        if name in BUILTIN_THEMES:
            raise ValueError('Built-in themes cannot be replaced')
        if name in self._themes and not replace:
            raise ValueError('Theme already registered: %s' % name)
        if not isinstance(styles, dict):
            raise TypeError('theme styles must be a dict')
        unknown = set(styles) - set(THEME_KINDS)
        if unknown:
            raise ValueError('Unknown theme control kinds: %s' % sorted(unknown))
        result = self.get(base) if base is not None else {}
        for kind, style in styles.items():
            if isinstance(style, STRING_TYPES):
                style = {'class': style}
            if not isinstance(style, dict):
                raise TypeError('theme control style must be a class string or a dict')
            _plain(style)
            if 'class' in style and (not isinstance(style['class'], STRING_TYPES) or not style['class']):
                raise ValueError('theme class must be a nonempty string')
            result.setdefault(kind, {}).update(copyContainers(style))
        self._themes[name] = result

    def unregister(self, name):
        if name in BUILTIN_THEMES:
            raise ValueError('Built-in themes cannot be removed')
        if name not in self._themes:
            raise ValueError('Unknown theme: %s' % name)
        del self._themes[name]

    def names(self):
        return list(BUILTIN_THEMES) + sorted(self._themes)
