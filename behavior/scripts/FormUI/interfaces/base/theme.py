# -*- coding: utf-8 -*-


class Theme:
    """Register static theme styles on the side that creates forms."""

    @staticmethod
    def register(name, styles, base='oreui', replace=False):
        from ...core.utils.environment import getSystem
        getSystem().screen.themes.register(name, styles, base, replace)

    @staticmethod
    def get(name):
        from ...core.utils.environment import getSystem
        return getSystem().screen.themes.get(name)

    @staticmethod
    def names():
        from ...core.utils.environment import getSystem
        return getSystem().screen.themes.names()

    @staticmethod
    def unregister(name):
        from ...core.utils.environment import getSystem
        screen = getSystem().screen
        if screen.getDefaultTheme() == name:
            raise ValueError('Clear the default theme before unregistering it')
        screen.themes.unregister(name)
