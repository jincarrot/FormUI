# -*- coding: utf-8 -*-
"""Static grid configuration and deterministic placement, independent of the SDK."""
from .ui import validateGrids, _finiteNumber

try:
    _INTEGERS = (int, long)
except NameError:
    _INTEGERS = (int,)


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, _INTEGERS) or value < minimum:
        raise ValueError('%s must be an integer >= %s' % (name, minimum))
    return value


def _tracks(value, name):
    if isinstance(value, _INTEGERS) and not isinstance(value, bool):
        _integer(value, name, 1)
        if value > 256:
            raise ValueError('%s supports at most 256 tracks' % name)
        return [1] * value
    weights = validateGrids(value)
    if len(weights) > 256:
        raise ValueError('%s supports at most 256 tracks' % name)
    return weights


def validateGrid(config):
    """Rows/columns are counts or positive weights; gap/padding are pixel values."""
    if not isinstance(config, dict):
        raise TypeError('grid layout must be a dict')
    unknown = set(config) - set(('columns', 'rows', 'gap', 'padding'))
    if unknown:
        raise ValueError('Unknown grid layout fields: %s' % sorted(unknown))
    result = {key: _tracks(config.get(key, 1), key) for key in ('columns', 'rows')}
    for key in ('gap', 'padding'):
        value = _finiteNumber(config.get(key, 0), key)
        if value < 0:
            raise ValueError('%s must be nonnegative' % key)
        result[key] = value
    return result


def validateCell(cell, layout=None):
    if not isinstance(cell, dict):
        raise TypeError('grid position must be a dict with row and column')
    unknown = set(cell) - set(('row', 'column', 'rowSpan', 'columnSpan'))
    if unknown:
        raise ValueError('Unknown grid position fields: %s' % sorted(unknown))
    if 'row' not in cell or 'column' not in cell:
        raise ValueError('grid position requires row and column (zero-based)')
    result = {key: _integer(cell.get(key, 1), key, 1 if key.endswith('Span') else 0)
              for key in ('row', 'column', 'rowSpan', 'columnSpan')}
    if layout is not None:
        for axis, tracks in (('row', 'rows'), ('column', 'columns')):
            if result[axis] + result[axis + 'Span'] > len(layout[tracks]):
                raise ValueError('grid position exceeds %s' % tracks)
    return result


def planCells(positions, layout):
    """Reserve explicit cells first; place remaining entries in row-major order.

    Hidden controls retain their cells. Explicit overlap is rejected; forms on the
    screen are independent windows and do not share an occupancy map.
    """
    occupied, result = set(), {}
    def reserve(key, cell):
        cells = set((row, col)
                    for row in range(cell['row'], cell['row'] + cell['rowSpan'])
                    for col in range(cell['column'], cell['column'] + cell['columnSpan']))
        if occupied.intersection(cells):
            raise ValueError('Overlapping grid position for %s' % (key,))
        occupied.update(cells)
        result[key] = cell
    for key, cell in positions:
        if cell is not None:
            reserve(key, validateCell(cell, layout))
    available = ((row, col) for row in range(len(layout['rows']))
                 for col in range(len(layout['columns'])) if (row, col) not in occupied)
    for key, cell in positions:
        if cell is None:
            try:
                row, col = next(available)
            except StopIteration:
                raise ValueError('Grid has no free cell for %s' % (key,))
            reserve(key, {'row': row, 'column': col, 'rowSpan': 1, 'columnSpan': 1})
    return result


def cellRect(layout, cell, size):
    """Return (x, y, width, height) in pixels; clamp undersized viewports to zero."""
    values = []
    for axis, tracks, length in (('column', 'columns', size[0]), ('row', 'rows', size[1])):
        weights = layout[tracks]
        gap, padding = layout['gap'], layout['padding']
        usable = max(0.0, length - 2 * padding)
        # Reduce gaps in tiny windows so all cells remain within the available area.
        actualGap = min(gap, usable / (len(weights) - 1)) if len(weights) > 1 else 0
        unit = max(0.0, usable - actualGap * (len(weights) - 1)) / float(sum(weights))
        start, span = cell[axis], cell[axis + 'Span']
        origin = min(padding, length / 2.0) + sum(weights[:start]) * unit + start * actualGap
        extent = sum(weights[start:start + span]) * unit + (span - 1) * actualGap
        values.append((origin, extent))
    return values[0][0], values[1][0], values[0][1], values[1][1]
