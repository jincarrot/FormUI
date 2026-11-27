# -*- coding: utf-8 -*-
"""Grid rendering shared by windows, form contents and nested Groups."""
from ...utils.grid import validateGrid, validateCell, planCells, cellRect
from ...utils.type import unwrapWrappedValue
from ...utils.ui import getSizeDict


def _value(style, key):
    return unwrapWrappedValue(style.get(key))


class GridLayoutMixin(object):
    def _resetGridCaches(self):
        self._gridPlans = {}
        self._gridWatches = {}

    def _validateGridData(self, form):
        plans = {'root': None, 'content': None, 'groups': {}}
        style = form['style']
        position = _value(style, 'grid')
        if position is not None:
            config = unwrapWrappedValue(form.get('screenGrid'))
            if config is None:
                raise ValueError('Form grid position requires a screen grid snapshot')
            layout = validateGrid(config)
            plans['root'] = (layout, validateCell(position, layout))

        def validateChildren(address, parentStyle, children):
            config = _value(parentStyle, 'layout')
            positions = [(key, _value(data['style'], 'grid')) for key, data in children]
            if config is not None:
                layout = validateGrid(config)
                plan = (layout, planCells(positions, layout))
                if address is None:
                    plans['content'] = plan
                else:
                    plans['groups'][address] = plan
            elif any(cell is not None for key, cell in positions):
                raise ValueError('Child grid position requires a parent layout')
            for key, data in children:
                if 'children' in data:
                    childAddress = key if address is None else (
                        (address,) if not isinstance(address, tuple) else address) + (key,)
                    validateChildren(childAddress, data['style'], sorted(data['children'].items()))
        validateChildren(None, style, list(enumerate(form['controls'])))
        return plans

    def _setGridPlans(self, formId, plans):
        self._gridPlans[formId] = plans
        watch = self._gridWatches.get(formId)
        if watch is not None:
            # Children may have been remounted; root/content natives are unchanged.
            watch['groups'] = {}
            if not plans['root']:
                watch.pop('root', None)
            if not plans['content']:
                watch.pop('content', None)
            if len(watch) == 1:
                self._gridWatches.pop(formId, None)

    def _getGridPlans(self, formId):
        if formId not in self._gridPlans:
            self._setGridPlans(formId, self._validateGridData(self.forms[formId]))
        return self._gridPlans[formId]

    def _gridWatch(self, formId):
        return self._gridWatches.setdefault(formId, {'groups': {}})

    def _setGridGeometry(self, data, native, layout, cell, viewport):
        x, y, width, height = cellRect(layout, cell, viewport)
        style = data['style']
        size = (width, height)
        def dimension(key, axis, default):
            spec = getSizeDict(style[key]['value'])
            if spec is None:
                spec = default
            if spec is None:
                return native.GetSize()[axis] if key in ('width', 'height') else 0
            follow = spec.get('followType', 'parent')
            relativeAxis = axis if follow == 'parent' else (0 if follow == 'x' else 1)
            return spec.get('absoluteValue', 0) + spec.get('relativeValue', 0) * size[relativeAxis]
        native.SetAnchorFrom('top_left')
        native.SetAnchorTo('top_left')
        for index, axis in enumerate(('x', 'y')):
            extent = dimension(('width', 'height')[index], index, data['defaultSize'][index])
            offset = dimension(('offsetX', 'offsetY')[index], index, data['defaultOffset'][index])
            native.SetFullSize(axis, {'relativeValue': 0.0, 'absoluteValue': max(0, extent), 'followType': 'parent'})
            native.SetFullPosition(axis, {'relativeValue': 0.0, 'absoluteValue': (x, y)[index] + offset, 'followType': 'parent'})

    def _layoutRootGrid(self, formId, native=None, viewport=None):
        form = self.forms[formId]
        plan = self._getGridPlans(formId)['root']
        if plan is None:
            return False
        native = native or self._formControl(formId)
        config, position = plan
        size = viewport if viewport is not None else tuple(self._formParent().GetSize())
        self._setGridGeometry(form, native, config, position, size)
        form['_gridScreenSize'] = size
        self._gridWatch(formId)['root'] = native
        return True

    def _layoutFormGrid(self, formId, viewportControl, content):
        form = self.forms[formId]
        plan = self._getGridPlans(formId)['content']
        if plan is None:
            return False
        layout, cells = plan
        viewport = tuple(viewportControl.GetSize())
        form['_gridViewport'] = viewport
        self._gridWatch(formId)['content'] = viewportControl
        scrolling = form.get('_scrolling', True)
        bottom = viewport[1]
        for index, data in enumerate(form['controls']):
            native = self.getControl(formId, index)
            if native is None:
                continue
            self._setGridGeometry(data, native, layout, cells[index], viewport)
            visible = bool(data['style']['visible']['value'])
            native.SetVisible(visible)
            if scrolling and visible:
                bottom = max(bottom, native.GetPosition()[1] + native.GetSize()[1] + layout['padding'])
        if scrolling:
            form['_layoutHeight'] = bottom
            content.SetFullSize('y', {'relativeValue': 0.0, 'absoluteValue': bottom, 'followType': 'parent'})
        self._updateDropdownExtent(formId)
        return True

    def _layoutGroupCell(self, formId, address, data, native, planned):
        parentAddress = address[0] if len(address) == 2 else address[:-1]
        parent = self._getControlData(formId, parentAddress)
        plan = self._getGridPlans(formId)['groups'].get(parentAddress)
        if plan is None:
            return False
        if parentAddress not in planned:
            layout, cells = plan
            group = self.getControl(formId, parentAddress)
            viewport = tuple(group.GetSize())
            parent['_gridGroupSize'] = viewport
            self._gridWatch(formId)['groups'][parentAddress] = (parent, group)
            planned[parentAddress] = (layout, cells, viewport)
        layout, cells, viewport = planned[parentAddress]
        self._setGridGeometry(data, native, layout, cells[address[-1]], viewport)
        return True

    def _updateGridLayouts(self):
        """Reflow only when the actual screen or content viewport changes size."""
        screenSize = None
        for formId, watch in list(self._gridWatches.items()):
            form = self.forms[formId]
            changed = False
            if 'root' in watch:
                if screenSize is None:
                    screenSize = tuple(self._formParent().GetSize())
                if screenSize != form['_gridScreenSize']:
                    self._layoutRootGrid(formId, watch['root'], screenSize)
                    changed = True
            if 'content' in watch:
                changed = changed or tuple(watch['content'].GetSize()) != form['_gridViewport']
            if not changed:
                for data, group in watch['groups'].values():
                    if tuple(group.GetSize()) != data['_gridGroupSize']:
                        changed = True
                        break
            if changed:
                self._relayoutForm(formId)
                self._layoutGroups(formId)
