from typing import Any, Literal, TypeAlias

ThemeKind: TypeAlias = Literal[
    'scrolling_panel', 'button', 'toggle', 'label', 'divider',
    'slider', 'textfield', 'dropdown', 'listview',
]

class Theme:
    @staticmethod
    def register(name: str, styles: dict[ThemeKind, str | dict[str, Any]], base: str | None = 'oreui', replace: bool = False) -> None: ...
    @staticmethod
    def get(name: str) -> dict[str, dict[str, Any]]: ...
    @staticmethod
    def names() -> list[str]: ...
    @staticmethod
    def unregister(name: str) -> None: ...
