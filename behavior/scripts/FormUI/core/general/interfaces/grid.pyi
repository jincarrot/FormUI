from typing import Literal, TypeAlias, TypedDict

GridTracks: TypeAlias = int | list[int | float] | tuple[int | float, ...]

class GridLayout(TypedDict, total=False):
    columns: GridTracks
    rows: GridTracks
    gap: int | float
    padding: int | float

class _GridOrigin(TypedDict):
    row: int
    column: int

class GridPosition(_GridOrigin, total=False):
    rowSpan: int
    columnSpan: int

class _FormLayoutWithCombineUI(GridLayout):
    combineUI: bool

FormLayout: TypeAlias = GridLayout | _FormLayoutWithCombineUI | Literal[False]
