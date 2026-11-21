# -*- coding: utf-8 -*-
import math
from copy import deepcopy
from collections import deque

from ...general.enums.controlType import ControlType
from ...utils.ui import getScrollingContent, getSizeDict, getSliderPercentage, getSliderValue, getStepedValue, validateGrids, getFontScale, validateDropdownItems, validateListViewItems, validateListViewHeight, getTopScreenNode, notifyFormClosed
from ...utils.type import unwrapWrappedValue, wrapDict, wrapVariable
from ...utils.group import groupStyle, iterControls
from .grid import GridLayoutMixin
from .bindings import BindingMixin

import mod.client.extraClientApi as c

ScreenNode = c.GetScreenNodeCls()

class _Screen(GridLayoutMixin, BindingMixin):
    _panelPath = '/panel'
    _showLoadingIndicator = True

    def _initRenderer(self, system, ready=False):
        self.controlManager = system.controlManager
        self._system = system
        self._destroyed = False
        self._resetForms()
        self.__allready = ready

    def isAllReady(self):
        return self.__allready and not self._destroyed

    def Create(self):
        self._resetForms()
        self.__allready = True

    def _resetForms(self):
        self.forms = {}
        self.__formOrder = []
        self.toggles = []
        self.sliders = []
        self.textfields = []
        self.observables = []
        self._resetBindings()
        self._resetGridCaches()
        self.__pendingCustomUpdates = {}
        self.__customControls = {}
        self.__nativeControls = {}
        self.__creatingForms = set()
        self.__flushingCustomUpdates = set()
        self.__deferredFormUpdates = {}
        self.__geometryTransitions = {}
        self.__creationTimers = {}
        self.__pendingControlMounts = {}
        self.__loadingForms = []
        self.__listViews = {}
        self.__repeatFuncs = []
        self.__loadingVisible = None
        self.__loadingControl = None
        self.__inputRecords = {}

    def _formControl(self, formId, path=''):
        return self.GetBaseUIControl('%s/fm%s%s' % (self._panelPath, formId, path))

    def _formParent(self):
        return self.GetBaseUIControl(self._panelPath)

    def addForm(self, formData, pendingCustomUpdates=()):
        formId = formData['formId']['value']
        if self._destroyed:
            raise RuntimeError('FormUI host screen has closed')
        if formId in self.forms:
            raise RuntimeError('该表单已经被显示出来了，关闭后才能再次调用 show()。')
        validateGrids([entry['value'] for entry in formData['style']['grids']])
        for control in formData['controls']:
            self._prepareGroup(control)
        gridPlans = self._validateGridData(formData)

        style = formData['style']
        formData['basePath'] = self.controlManager.get(style['class']['value']).options['scrollingPanelPath']

        self.forms[formId] = formData
        self.__formOrder.append(formId)
        try:
            self._setGridPlans(formId, gridPlans)
            self._refreshFormBindings(formId)
            self.__pendingCustomUpdates[formId] = deque(pendingCustomUpdates)
            if formData.get('options', {}).get('combineUI'):
                parent = self._formParent()
                if not parent:
                    raise RuntimeError('FormUI host panel is unavailable')
                self._mountForm(formId, formData, parent)
                return
            self._scheduleFormCreation(formId, formData)
        except Exception as error:
            if self.forms.get(formId) is not formData:
                # A creation callback already closed this display and sent its receipt.
                print('[FormUI] Error after form %s was closed: %s' % (formId, error))
                return
            self._removeForm(formId)
            raise

    def _scheduleFormCreation(self, formId, formData):
        comp = c.GetEngineCompFactory().CreateGame(c.GetLevelId())
        timerId = {'after': None, 'repeat': None}
        self.__creationTimers[formId] = timerId
        def create(formData):
            if self.forms.get(formId) is not formData:
                if timerId['repeat'] is not None:
                    comp.CancelTimer(timerId['repeat'])
                return
            parent = self._formParent()
            if parent:
                comp.CancelTimer(timerId['repeat'])
                self.__creationTimers.pop(formId, None)
                self.__loadingForms.remove(formId)
                try:
                    self._mountForm(formId, formData, parent)
                except Exception:
                    if self.forms.get(formId) is formData:
                        self._closeForm(formId, 'unavailable')
                    raise

        def after(formData):
            if self.forms.get(formId) is formData:
                timerId['repeat'] = comp.AddRepeatedTimer(0.05, create, formData)
        timerId['after'] = comp.AddTimer(0.05 * len(self.__loadingForms), after, formData)
        self.__loadingForms.append(formId)

    def _mountForm(self, formId, formData, parent):
        style = formData['style']
        base = self.controlManager.get(style['class']['value'])
        self.__creatingForms.add(formId)
        try:
            root = None
            rootName = 'fm%s' % formId
            if formData.get('template'):
                from .template import mountTemplate
                root = mountTemplate(self, formData, parent, rootName, base)
            if root is None:
                if self.forms.get(formId) is not formData:
                    return
                root = self.CreateChildControl(base.path, rootName, parent)
            if not root:
                raise RuntimeError('FormUI could not create the form root')
            if self.forms.get(formId) is not formData:
                if not self._destroyed:
                    self.RemoveChildControl(root)
                return
            formData['defaultSize'] = deepcopy((root.GetFullSize('x'), root.GetFullSize('y')))
            formData['defaultOffset'] = deepcopy((root.GetFullPosition('x'), root.GetFullPosition('y')))
            if not self._layoutRootGrid(formId, root):
                self.setSize(formId, -1, 'x', getSizeDict(style['width']['value']), root)
                self.setSize(formId, -1, 'y', getSizeDict(style['height']['value']), root)
                self.setOffset(formId, -1, 'x', getSizeDict(style['offsetX']['value']), root)
                self.setOffset(formId, -1, 'y', getSizeDict(style['offsetY']['value']), root)
            close = root.GetChildByPath(base.options['closeBtnPath'])
            if close:
                close = close.asButton()
                close.AddTouchEventParams({'formId': formId})
                def onClose(data):
                    if self.forms.get(formId) is formData:
                        self.onClose(data)
                close.SetButtonTouchUpCallback(onClose)
            self.setFormTitle(formId, base.options['titlePath'], formData['title']['value'])
            self.setFormContent(formId, base.options['scrollingPanelPath'])
            if self.forms.get(formId) is formData:
                self.setLayer(formId, -1, style['layer']['value'], root)
                self._refreshFormVisibility()
        finally:
            if self.forms.get(formId) is formData:
                self.__creatingForms.discard(formId)
        if self.forms.get(formId) is formData:
            self._mountAddedControls(formId)
            self._applyDeferredFormUpdates(formId)
            self._flushCustomUpdates(formId)

    def onClose(self, data):
        formId = data['AddTouchEventParams']['formId']
        self._closeForm(formId, 'api' if 'closeByInterface' in data else 'user')

    def _closeForm(self, formId, reason):
        form = self.forms.get(formId)
        if form is None:
            return
        try:
            self._removeForm(formId)
        finally:
            try:
                if not self._destroyed:
                    self._afterFormClosed(form)
            finally:
                notifyFormClosed(self._system, formId, reason)

    def _removeForm(self, formId):
        del self.forms[formId]
        self._forgetFormBindings(formId)
        self._gridPlans.pop(formId, None)
        self._gridWatches.pop(formId, None)
        timers = self.__creationTimers.pop(formId, {})
        if timers:
            comp = c.GetEngineCompFactory().CreateGame(c.GetLevelId())
            for timer in timers.values():
                if timer is not None:
                    comp.CancelTimer(timer)
        if formId in self.__loadingForms:
            self.__loadingForms.remove(formId)
        self.__pendingControlMounts.pop(formId, None)
        self.__pendingCustomUpdates.pop(formId, None)
        self.__customControls.pop(formId, None)
        self.__nativeControls.pop(formId, None)
        self.__listViews.pop(formId, None)
        self.__inputRecords.pop(formId, None)
        self.__deferredFormUpdates.pop(formId, None)
        self.__creatingForms.discard(formId)
        self.__flushingCustomUpdates.discard(formId)
        for key in list(self.__geometryTransitions):
            if key[0] == formId:
                del self.__geometryTransitions[key]
        self.__formOrder.remove(formId)
        for updatedData in (self.sliders, self.textfields, self.toggles):
            updatedData[:] = [entry for entry in updatedData if entry['formId'] != formId]
        if not self._destroyed:
            root = self._formControl(formId)
            if root:
                self.RemoveChildControl(root)
            self._refreshFormVisibility()

    def _hostClosed(self):
        self._destroyed = True
        self.__repeatFuncs = []
        for formId in list(self.forms):
            try:
                self._closeForm(formId, 'user')
            except Exception as error:
                print('[FormUI] Error closing form %s with its host: %s' % (formId, error))

    def _refreshFormVisibility(self):
        hiddenByLaterForm = False
        for formId in reversed(self.__formOrder):
            control = self._formControl(formId)
            if not control:
                continue
            style = self.forms[formId]['style']
            visible = bool(style['visible']['value'])
            control.SetVisible(visible and not hiddenByLaterForm)
            if visible and style['hideOtherForms']['value']:
                hiddenByLaterForm = True

    def setLayer(self, formId, controlIndex, value, c=None):
        if formId not in self.forms:
            return
        control = c or (self._formControl(formId) if controlIndex == -1 else self.getControl(formId, controlIndex))
        if control:
            control.SetLayer(value)

    def setSize(self, formId, controlIndex, axis, value, c=None):
        self._setGeometry(formId, controlIndex, axis, value, c, 'Size')

    def setOffset(self, formId, controlIndex, axis, value, c=None):
        self._setGeometry(formId, controlIndex, axis, value, c, 'Position')

    def _setGeometry(self, formId, controlIndex, axis, value, native, kind):
        if formId not in self.forms:
            return
        control = native or (self._formControl(formId)
                             if controlIndex == -1 else self.getControl(formId, controlIndex))
        if not control:
            return
        defaults = self.forms[formId] if controlIndex == -1 else self._getControlData(formId, controlIndex)
        if value is None:
            value = defaults['defaultSize' if kind == 'Size' else 'defaultOffset'][0 if axis == 'x' else 1]
            if value is None and kind == 'Size':
                # Labels may use their native automatic size rather than an explicit dimension.
                return
        target = {'absoluteValue': 0.0, 'relativeValue': 0.0, 'followType': 'parent'}
        target.update(value or {})
        setter = getattr(control, 'SetFull' + kind)
        if controlIndex != -1:
            setter(axis, target)
            return
        key = (formId, controlIndex, kind, axis)
        if formId in self.__creatingForms:
            self.__geometryTransitions.pop(key, None)
            setter(axis, target)
            return
        # Only a live window transition needs its current native geometry as a starting point.
        origin = dict(target)
        origin.update(getattr(control, 'GetFull' + kind)(axis) or {})
        token = object()
        self.__geometryTransitions[key] = token
        if origin['followType'] == target['followType']:
            frame = [0]
            def repeat():
                if self.__geometryTransitions.get(key) is not token or formId not in self.forms:
                    return
                frame[0] += 1
                ratio = frame[0] / 10.0
                current = {name: origin[name] + (target[name] - origin[name]) * ratio
                           for name in ('absoluteValue', 'relativeValue')}
                current['followType'] = target['followType']
                setter(axis, current if frame[0] < 10 else dict(target))
                if frame[0] == 10 and kind == 'Size':
                    self._relayoutForm(formId)
                    self._layoutGroups(formId)
            self.addRepeatFunc(repeat, 10)
        else:
            setter(axis, target)
            if kind == 'Size':
                self._relayoutForm(formId)
                self._layoutGroups(formId)

    def setControlLabel(self, formId, controlIndex, labelPaths, value, c=None):
        if formId not in self.forms:
            return
        control = self.getControl(formId, controlIndex)
        if c:
            control = c
        else:
            cls = self.controlManager.get(self._getControlData(formId, controlIndex)['style']['class']['value'])
            if cls.typeId == ControlType.Button:
                control = control.GetChildByPath(cls.options.get('buttonPath', ''))
        if isinstance(labelPaths, str):
            labelPaths = [labelPaths]
        for path in labelPaths:
            try:
                control.GetChildByPath(path).asLabel().SetText(value)
            except:
                pass

    def setFormTitle(self, formId, titlePath, value):
        control = self._formControl(formId, titlePath)
        if not control:
            return
        control.asLabel().SetText(str(value))
        self.forms[formId]['title']['value'] = value

    def setFormContent(self, formId, contentPath):
        form = self.forms[formId]
        controls = form['controls']
        scrollPanel = self._formControl(formId, contentPath).asScrollView()
        content = getScrollingContent(scrollPanel)
        wasCreating = formId in self.__creatingForms
        self.__creatingForms.add(formId)
        try:
            created = []
            prebuilt = form.pop('_compiledNodes', None)
            for control in controls:
                self._prepareGroup(control)
            self._refreshFormBindings(formId)
            parent = form.get('_compiledParent', content)
            for index, control in enumerate(controls):
                self._createControl(formId, index, control, parent, "c%s" % index, created, prebuilt)
            self._relayoutForm(formId)
            self._layoutGroups(formId)
            self._finishControlCreation(formId, created)
        finally:
            if not wasCreating and self.forms.get(formId) is form:
                self.__creatingForms.discard(formId)
                self._mountAddedControls(formId)
                self._applyDeferredFormUpdates(formId)
                self._flushCustomUpdates(formId)

    def appendFormControl(self, data):
        formId = data['formId']
        form = self.forms.get(formId)
        if form is None:
            return
        if data['index'] < len(form['controls']):
            return
        if data['index'] != len(form['controls']):
            raise ValueError('Out-of-order form control index')
        control = deepcopy(data['control'])
        self._prepareGroup(control)
        candidate = dict(form, controls=form['controls'] + [control])
        gridPlans = self._validateGridData(candidate)
        form['controls'].append(control)
        self._setGridPlans(formId, gridPlans)
        self.__pendingControlMounts.setdefault(formId, set()).add(data['index'])
        self._refreshFormBindings(formId)
        self._mountAddedControls(formId)

    def _mountAddedControls(self, formId):
        if formId in self.__loadingForms or formId in self.__creatingForms:
            return
        while formId in self.forms:
            form = self.forms[formId]
            pending = self.__pendingControlMounts.get(formId, set())
            missing = [(index, form['controls'][index]) for index in sorted(pending)
                       if index not in self.__nativeControls.get(formId, {})]
            if not missing:
                self.__pendingControlMounts.pop(formId, None)
                return
            panel = self._formControl(formId, form['basePath'])
            if not panel:
                return
            content = getScrollingContent(panel)
            if not content:
                return
            self.__creatingForms.add(formId)
            created = []
            try:
                for index, control in missing:
                    if self.forms.get(formId) is not form:
                        return
                    self._createControl(formId, index, control, form.get('_compiledParent', content),
                                        'c%s' % index, created)
                    pending.discard(index)
                self._relayoutForm(formId)
                self._layoutGroups(formId)
                self._finishControlCreation(formId, created)
            finally:
                if self.forms.get(formId) is form:
                    self.__creatingForms.discard(formId)
                    self._applyDeferredFormUpdates(formId)
                    self._flushCustomUpdates(formId)

    def moveNextControls(self, formId, index):
        self._relayoutForm(formId)

    def _relayoutForm(self, formId):
        if formId not in self.forms:
            return
        form = self.forms[formId]
        panel = self._formControl(formId, form['basePath'])
        if not panel:
            return
        content = getScrollingContent(panel)
        if not content:
            return
        if self._layoutFormGrid(formId, panel, content):
            return
        grids = validateGrids([entry['value'] for entry in form['style']['grids']])
        visibleIndex = 0
        rowStart = 0
        rowBottom = 0
        for index, controlData in enumerate(form['controls']):
            control = self.getControl(formId, index)
            if not control:
                continue
            if not controlData['style']['visible']['value']:
                control.SetVisible(False)
                continue
            column = visibleIndex % len(grids)
            if column == 0:
                rowStart = rowBottom
            occupied = self.setControlLayout(formId, controlData, control, form['style'],
                                             index, rowStart, column, grids)
            rowBottom = max(rowBottom, rowStart + occupied)
            visibleIndex += 1
        form['_layoutHeight'] = max(panel.GetSize()[1], rowBottom)
        content.SetFullSize("y", {"absoluteValue": form['_layoutHeight'],
                                  "relativeValue": 0.0, "followType": "parent"})
        self._updateDropdownExtent(formId)

    def setControlLayout(self, formId, controlData, control, formStyle, index, height, column=None, grids=None):
        if grids is None:
            grids = validateGrids([entry['value'] for entry in formStyle['grids']])
        if column is None:
            column = index % len(grids)
        total = float(sum(grids))
        fraction = grids[column] / total
        columnStart = sum(grids[:column]) / total
        style = controlData['style']
        defaultSize = controlData.get('defaultSize')
        if defaultSize is None:
            defaultSize = (control.GetFullSize('x'), control.GetFullSize('y'))
        defaultOffset = controlData.get('defaultOffset')
        if defaultOffset is None:
            defaultOffset = (control.GetFullPosition('x'), control.GetFullPosition('y'))
        sizeX = dict(getSizeDict(style['width']['value']) or defaultSize[0])
        sizeY = dict(getSizeDict(style['height']['value']) or defaultSize[1])
        sizeX['relativeValue'] *= fraction
        self.setSize(formId, index, "x", sizeX, control)
        self.setSize(formId, index, "y", sizeY, control)
        offsetX = dict(getSizeDict(style['offsetX']['value']) or defaultOffset[0] or {})
        offsetY = dict(getSizeDict(style['offsetY']['value']) or defaultOffset[1] or {})
        self.setOffset(formId, index, "x", {
            "relativeValue": columnStart + offsetX.get('relativeValue', 0.0) * fraction,
            "absoluteValue": offsetX.get('absoluteValue', 0.0),
            "followType": "parent"
        }, control)
        self.setOffset(formId, index, "y", {
            "relativeValue": offsetY.get('relativeValue', 0.0),
            "absoluteValue": height + offsetY.get('absoluteValue', 0.0),
            "followType": offsetY.get('followType', 'parent')
        }, control)
        visible = bool(style['visible']['value'])
        control.SetVisible(visible)
        return max(0, control.GetPosition()[1] + control.GetSize()[1] - height) if visible else 0

    def setButtonProperties(self, formId, index, controlCls, c):
        btn = c.GetChildByPath(controlCls.options['buttonPath'])
        if not btn:
            return
        btn = btn.asButton()
        if not btn:
            return
        controlData = self._getControlData(formId, index)
        btn.AddTouchEventParams()
        btn.SetButtonTouchUpCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onClick']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveInCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveIn']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveOutCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveOut']['value']: self.onButtonClick(formId, callbackId))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], btn)

    def setToggleProperties(self, formId, index, controlCls, c):
        toggle = c.asSwitchToggle()
        if not toggle:
            return
        controlData = self._getControlData(formId, index)
        self._trackInput(self.toggles, {"control": toggle, "formId": formId, "index": index, "value": controlData['state']['value'], "path": controlCls.options['togglePath']})
        toggle.SetToggleState(bool(controlData['state']['value']), controlCls.options['togglePath'])
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], toggle)

    def setLabelProperties(self, formId, index, controlCls, c):
        label = c
        if not label:
            return
        controlData = self._getControlData(formId, index)
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], label)
        if 'fontSize' in controlData['style'] and controlData['style']['fontSize']['value'] != 'default':
            self._setLabelFontSize(formId, index, controlCls, controlData['style']['fontSize']['value'])

    def _setLabelFontSize(self, formId, index, cls, value):
        root = self.getControl(formId, index)
        paths = cls.options['labelPaths']
        if isinstance(paths, str):
            paths = [paths]
        scale = getFontScale(value)
        for path in paths:
            root.GetChildByPath(path).asLabel().SetTextFontSize(scale)

    def setSliderProperties(self, formId, index, controlCls, c):
        slider = c.GetChildByPath(controlCls.options['sliderPath'])
        if not slider:
            return
        slider = slider.asSlider()
        if not slider:
            return
        controlData = self._getControlData(formId, index)
        sliderValue = getStepedValue(controlData['value']['value'], controlData['minValue']['value'], controlData['maxValue']['value'], controlData['step']['value'])
        percentage = getSliderPercentage(sliderValue, controlData['minValue']['value'], controlData['maxValue']['value'], controlData['step']['value'])
        self._trackInput(self.sliders, {"control": slider, "formId": formId, "index": index, "value": sliderValue, "minValue": controlData['minValue']['value'], "maxValue": controlData['maxValue']['value'], "step": controlData['step']['value'], "valuePaths": controlCls.options['valuePaths'], "lastPercentage": percentage})
        slider.SetSliderValue(percentage)
        for valuePath in controlCls.options['valuePaths']:
            c.GetChildByPath(valuePath).asLabel().SetText(str(sliderValue))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], c)

    def setTextfieldProperties(self, formId, index, controlCls, c):
        textfield = c.GetChildByPath(controlCls.options['textfieldPath'])
        if not textfield:
            return
        textfield = textfield.asTextEditBox()
        if not textfield:
            return
        controlData = self._getControlData(formId, index)
        self._trackInput(self.textfields, {"control": textfield, "formId": formId, "index": index, "value": controlData['value']['value']})
        textfield.SetEditText(str(controlData['value']['value']))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], c)

    def setDropdownProperties(self, formId, index, controlCls, c, windowKey=None):
        dropdown = c.GetChildByPath(controlCls.options['dropdownPath'])
        if not dropdown:
            return
        dropdown = dropdown.asButton()
        if not dropdown:
            return
        dropdown.AddTouchEventParams()
        dropdown.SetButtonTouchUpCallback(lambda data: self.onDropdownBoxClick(formId, index))
        controlData = self._getControlData(formId, index)
        content = c.GetChildByPath(controlCls.options['contentPath'])
        items = controlData['items']
        rows = None
        if windowKey and items:
            from .template import mountMenuRows
            rows = mountMenuRows(self, content, windowKey, controlCls.options['itemControl'], len(items))
        height = 0
        current = ""
        for itemIndex, item in enumerate(items):
            if item['value']['value'] == controlData['value']['value']:
                current = item['label']['value']
            if rows is None:
                name = 'item_%s' % item['value']['value']
                itemControl = self.CreateChildControl(controlCls.options['itemControl'], name, content)
            else:
                itemControl = rows[itemIndex]
            itemControl.asButton().AddTouchEventParams()
            itemControl.asButton().SetButtonTouchUpCallback(lambda data, itemIndex=item['value']['value'], itemLabel=item['label']['value']: self.onDropdownItemClick(formId, index, itemIndex, itemLabel))
            itemControl.GetChildByPath("/button_label").asLabel().SetText(item['label']['value'])
            height = itemControl.GetFullSize("y")['absoluteValue']
            itemControl.SetFullPosition("y", {"absoluteValue": itemIndex * height})
        content.SetFullSize("y", {"absoluteValue": len(items) * height + 2})
        for labelPath in controlCls.options['boxLabelPaths']:
            dropdown.GetChildByPath(labelPath).asLabel().SetText(str(current))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], c)

    def _trackInput(self, records, record):
        records.append(record)
        self.__inputRecords.setdefault(record['formId'], {})[record['index']] = record

    def _inputIsAlive(self, record):
        return (record['formId'] in self.forms and
                self.__inputRecords.get(record['formId'], {}).get(record['index']) is record)

    def setListviewProperties(self, formId, index, controlCls, c):
        data = self._getControlData(formId, index)
        items = validateListViewItems(unwrapWrappedValue(data['items']))
        height = validateListViewHeight(unwrapWrappedValue(data['style'].get('itemHeight', wrapVariable(32))))
        content = getScrollingContent(c.GetChildByPath(controlCls.options['scrollingPanelPath']))
        if content is None:
            raise ValueError('ListView template requires a native scrolling content panel')
        states = self.__listViews.setdefault(formId, {})
        previous = states.get(index)
        existing = {}
        if '_compiledParent' in self.forms[formId]:
            if previous:
                existing = {i: entry[0] for i, entry in enumerate(previous['rows'])}
            else:
                from ...utils.template import ROWS_MARKER
                if content.GetChildByPath('/' + ROWS_MARKER):
                    for name in self.GetChildrenName(content.GetPath()):
                        if name.startswith('row_') and name[4:].isdigit():
                            existing[int(name[4:])] = content.GetChildByPath('/' + name)
        elif previous:
            for row, key in previous['rows']:
                self.RemoveChildControl(row)
        state = {'root': c, 'rows': [], 'markers': {}, 'selectedMarker': None}
        states[index] = state
        for position, item in enumerate(items):
            # Names use indices, so arbitrary business keys never become native paths.
            row = existing.pop(position, None)
            if row is None:
                row = self.CreateChildControl(controlCls.options['itemControl'], 'row_%s' % position, content)
            state['rows'].append((row, item['value']))
            marker = row.GetChildByPath(controlCls.options['selectedPath'])
            state['markers'][item['value']] = marker
            marker.SetVisible(False)
            row.SetFullSize('y', {'absoluteValue': height, 'relativeValue': 0.0, 'followType': 'parent'})
            row.SetFullPosition('y', {'absoluteValue': position * height, 'relativeValue': 0.0, 'followType': 'parent'})
            for path in controlCls.options['itemLabelPaths']:
                row.GetChildByPath(path).asLabel().SetText(item['label'])
            button = row.GetChildByPath(controlCls.options['itemButtonPath']).asButton()
            button.AddTouchEventParams()
            button.SetButtonTouchUpCallback(
                lambda event, key=item['value'], owner=state: self.onListviewItemClick(formId, index, key, owner))
        for row in existing.values():
            self.RemoveChildControl(row)
        content.SetFullSize('y', {'absoluteValue': len(items) * height,
                                  'relativeValue': 0.0, 'followType': 'parent'})
        empty = c.GetChildByPath(controlCls.options['emptyLabelPath'])
        empty.asLabel().SetText(unwrapWrappedValue(data['style'].get('emptyText', wrapVariable('暂无内容'))))
        empty.SetVisible(not items)
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], data['label']['value'], c)
        self._refreshListviewSelection(formId, index, controlCls)

    def _refreshListviewSelection(self, formId, index, cls):
        state = self.__listViews.get(formId, {}).get(index)
        if not state:
            return
        selected = self._getControlData(formId, index)['value']['value']
        try:
            marker = state['markers'].get(selected)
        except TypeError:
            marker = None  # An unsupported/unhashable selection matches no row.
        previous = state['selectedMarker']
        if marker is previous:
            return
        if previous is not None:
            previous.SetVisible(False)
        if marker is not None:
            marker.SetVisible(True)
        state['selectedMarker'] = marker

    def onListviewItemClick(self, formId, index, value, owner):
        if self.__listViews.get(formId, {}).get(index) is not owner:
            return  # Ignore delayed touches from removed rows or closed forms.
        data = self._getControlData(formId, index)
        if value not in owner['markers'] or data['value']['value'] == value:
            return
        data['value']['value'] = value
        self._writeInputValue(formId, index, 'value', value)
        # A subscriber may have replaced the list or closed the form.
        if formId in self.forms and self.__listViews.get(formId, {}).get(index) is owner:
            cls = self.controlManager.get(data['style']['class']['value'])
            self._refreshListviewSelection(formId, index, cls)

    def setCustomProperties(self, formId, index, controlCls, c):
        self.__customControls.setdefault(formId, {})[index] = {'control': c, 'ready': False}

    def setDividerProperties(self, formId, index, controlCls, c):
        pass

    def onButtonClick(self, formId, callbackId):
        from ...utils.environment import getClientSystem
        form = self.forms.get(formId)
        if form is None:
            return
        data = {"formId": formId, "callbackId": callbackId, "playerId": c.GetLocalPlayerId()}
        if form['fromServer']['value']:
            getClientSystem().NotifyToServer("buttonTriggerCallback", data)
        else:
            getClientSystem().onButtonTrigger(data)

    def _getControlData(self, formId, index):
        if not isinstance(index, tuple):
            return self.forms[formId]['controls'][index]
        data = self.forms[formId]['controls'][index[0]]
        for name in index[1:]:
            data = data['children'][name]
        return data

    def getControl(self, formId, index):
        mounted = self.__nativeControls.get(formId, {}).get(index)
        if mounted is not None:
            return mounted
        form = self.forms[formId]
        content = form.get('_compiledParent') or getScrollingContent(self._formControl(formId, form['basePath']))
        if isinstance(index, tuple):
            control = content.GetChildByPath("/c%s" % index[0])
            for name in index[1:]:
                control = control.GetChildByPath('/' + name)
            return control
        return content.GetChildByPath("/c%s" % index)

    def _prepareGroup(self, data, ancestors=()):
        if '_groupLayout' in data:
            data['style'].update(groupStyle(data['_groupLayout']))
        name = data['style']['class']['value']
        cls = self.controlManager.get(name)
        if cls is None:
            raise ValueError('Unregistered control: %s' % name)
        if getattr(cls, 'typeId', None) != ControlType.Group:
            if data.get('group', {}).get('value'):
                raise ValueError('form.group requires a registered Group')
            return
        if name in ancestors:
            raise ValueError('Circular Group reference: %s' % (ancestors + (name,),))
        instances = data.get('_groupInput', data.get('children', {}))
        definitions = deepcopy(cls.options['controls'])
        unknown = set(instances) - set(definitions)
        if unknown:
            raise ValueError('Unknown Group children: %s' % sorted(unknown))
        data['_groupInput'] = instances
        data['children'] = {}
        for childName, definition in definitions.items():
            child = deepcopy(instances.get(childName, {}))
            if 'style' in child:
                raise ValueError('Group child styles are defined at registration')
            child['_groupDefinition'] = definition
            child['style'] = groupStyle(definition)
            childCls = self.controlManager.get(child['style']['class']['value'])
            if childCls is None:
                raise ValueError('Unregistered Group child: %s' % child['style']['class']['value'])
            self._childDefaults(child, childCls.typeId)
            data['children'][childName] = child
            self._prepareGroup(child, ancestors + (name,))

    def _childDefaults(self, data, typeId):
        data['custom'] = wrapVariable(typeId == ControlType.Custom)
        defaults = {'label': ''}
        if typeId == ControlType.Button:
            data.setdefault('callbacks', {})
            for event in ('onClick', 'onMoveIn', 'onMoveOut'):
                data['callbacks'].setdefault(event, wrapVariable(0))
        elif typeId == ControlType.Toggle:
            defaults['state'] = False
        elif typeId == ControlType.Slider:
            defaults.update(value=0, minValue=0, maxValue=1, step=1)
        elif typeId == ControlType.Textfield:
            defaults['value'] = ''
        elif typeId == ControlType.Dropdown:
            defaults['value'] = None
            data.setdefault('items', [])
            if isinstance(data['items'], dict):
                raise TypeError('dropdown items must be a list of static options')
            validateDropdownItems(unwrapWrappedValue(data['items']))
        elif typeId == ControlType.ListView:
            defaults['value'] = None
            data.setdefault('items', [])
            data['style'].setdefault('itemHeight', wrapVariable(32))
            data['style'].setdefault('emptyText', wrapVariable('暂无内容'))
        elif typeId == ControlType.Custom:
            data.setdefault('params', {})
        for key, value in defaults.items():
            data.setdefault(key, wrapVariable(value))
        if typeId in (ControlType.Custom, ControlType.Group, ControlType.Divider):
            # These types do not expose the standard label property.
            data.pop('label', None)

    def _createControl(self, formId, address, data, parent, name, created, prebuilt=None):
        cls = self.controlManager.get(data['style']['class']['value'])
        if isinstance(address, tuple):
            self._childDefaults(data, cls.typeId)
        native = prebuilt.get(address) if prebuilt else None
        if native is None:
            native = self.CreateChildControl(cls.path, name, parent)
        self.__nativeControls.setdefault(formId, {})[address] = native
        data['_mountedClass'] = cls.name if hasattr(cls, 'name') else data['style']['class']['value']
        data['defaultSize'] = (native.GetFullSize('x'), native.GetFullSize('y'))
        data['defaultOffset'] = (native.GetFullPosition('x'), native.GetFullPosition('y'))
        if cls.typeId == ControlType.Group:
            prefix = address if isinstance(address, tuple) else (address,)
            for childName, child in data['children'].items():
                self._createControl(formId, prefix + (childName,), child, native, childName, created, prebuilt)
        else:
            # Legacy payloads used params presence as the custom marker.
            isCustom = data.get('custom', {}).get('value', 'params' in data)
            typeId = ControlType.Custom if not isinstance(address, tuple) and isCustom else cls.typeId
            if typeId == ControlType.Dropdown and prebuilt and address in prebuilt:
                self.setDropdownProperties(formId, address, cls, native, self.forms[formId]['_compiledKey'])
            else:
                getattr(self, 'set' + typeId[0].upper() + typeId[1:] + 'Properties')(formId, address, cls, native)
        created.append((address, cls, native))
        return native

    def _finishControlCreation(self, formId, created):
        form = self.forms.get(formId)
        for address, cls, native in created:
            if form is None or self.forms.get(formId) is not form:
                return
            callback = cls.options.get('onCreate')
            if callback:
                from ...utils.type import CreateArguments
                data = self._getControlData(formId, address)
                callback(CreateArguments(
                    self, native, unwrapWrappedValue(data.get('params', {})),
                    style=unwrapWrappedValue(data.get('style', {}))))
                if self.forms.get(formId) is not form:
                    return
            state = self.__customControls.get(formId, {}).get(address)
            if state:
                state['ready'] = True

    def _layoutGroups(self, formId):
        planned = {}
        for address, data in iterControls(self.forms[formId]['controls']):
            if '_groupDefinition' not in data:
                continue
            data['style'] = groupStyle(data['_groupDefinition'])
            native = self.getControl(formId, address)
            if self._layoutGroupCell(formId, address, data, native, planned):
                native.SetVisible(bool(data['style']['visible']['value']))
                continue
            for key, axis in (('width', 'x'), ('height', 'y')):
                value = getSizeDict(data['style'][key]['value']) or data['defaultSize'][0 if axis == 'x' else 1]
                self.setSize(formId, address, axis, dict(value), native)
            for key, axis in (('offsetX', 'x'), ('offsetY', 'y')):
                value = getSizeDict(data['style'][key]['value']) or data['defaultOffset'][0 if axis == 'x' else 1]
                self.setOffset(formId, address, axis, dict(value), native)
            native.SetVisible(bool(data['style']['visible']['value']))
        self._updateDropdownExtent(formId)

    def _refreshGroupClasses(self, formId):
        form = self.forms[formId]
        for address, data in list(iterControls(form['controls'])):
            if not isinstance(address, tuple):
                continue
            name = data['style']['class']['value']
            if name == data.get('_mountedClass'):
                continue
            self._rebuildGroupChild(formId, address, data)
            # Ancestor reconstruction replaces descendant records and addresses.
            if self.forms.get(formId) is form:
                self._refreshGroupClasses(formId)
            return

    def _rebuildGroupChild(self, formId, address, data):
        cls = self.controlManager.get(data['style']['class']['value'])
        if cls is None:
            raise ValueError('Unregistered Group child class')
        parentAddress = address[0] if len(address) == 2 else address[:-1]
        parentData = self._getControlData(formId, parentAddress)
        definition = data['_groupDefinition']
        supplied = deepcopy(parentData['_groupInput'].get(address[-1], {}))
        supplied['_groupDefinition'] = definition
        supplied['style'] = groupStyle(definition)
        self._childDefaults(supplied, cls.typeId)
        ancestorNames = []
        for length in range(1, len(address)):
            key = address[0] if length == 1 else address[:length]
            ancestorNames.append(self._getControlData(formId, key)['style']['class']['value'])
        self._prepareGroup(supplied, tuple(ancestorNames))
        matches = lambda key: isinstance(key, tuple) and key[:len(address)] == address
        old = self.getControl(formId, address)
        for entries in (self.sliders, self.toggles, self.textfields):
            entries[:] = [entry for entry in entries if not (entry['formId'] == formId and matches(entry['index']))]
        for mapping in (self.__nativeControls.get(formId, {}), self.__customControls.get(formId, {}),
                        self.__listViews.get(formId, {}), self.__inputRecords.get(formId, {})):
            for key in list(mapping):
                if matches(key):
                    del mapping[key]
        pending = self.__pendingCustomUpdates.get(formId, deque())
        self.__pendingCustomUpdates[formId] = deque(entry for entry in pending if not matches(entry[0]))
        self.RemoveChildControl(old)
        data.clear()
        data.update(supplied)
        self._setGridPlans(formId, self._validateGridData(self.forms[formId]))
        self._refreshFormBindings(formId)
        parentAddress = address[0] if len(address) == 2 else address[:-1]
        created = []
        wasCreating = formId in self.__creatingForms
        self.__creatingForms.add(formId)
        try:
            self._createControl(formId, address, data, self.getControl(formId, parentAddress), address[-1], created)
            self._refreshFormBindings(formId)
            self._layoutGroups(formId)
            self._finishControlCreation(formId, created)
        finally:
            if not wasCreating:
                self.__creatingForms.discard(formId)
                self._applyDeferredFormUpdates(formId)

    def isFormScreen(self):
        return True
    
    def applyObservableUpdate(self, id, value):
        if hasattr(self.controlManager, 'applyObservableUpdate'):
            self.controlManager.applyObservableUpdate(id, value)
        if id in self._observableForms:
            for formId in list(self._observableForms[id]):
                form = self.forms.get(formId)
                if not form:
                    continue
                bindings = self._getFormBindings(formId)
                oldValues = bindings.update(id, value)
                if not oldValues:
                    continue
                self.__pendingCustomUpdates.setdefault(formId, deque()).extend(
                    bindings.customUpdates(id, oldValues))
                if formId in self.__loadingForms or formId in self.__creatingForms:
                    # Creation reads the updated snapshot when the controls become available.
                    if formId in self.__creatingForms:
                        self.__deferredFormUpdates.setdefault(formId, {})[id] = value
                    continue
                try:
                    self._applyFormObservableUpdate(formId, id, value)
                except:
                    pass
                finally:
                    self._flushCustomUpdates(formId)

    def _applyFormObservableUpdate(self, formId, obId, value):
        form = self.forms.get(formId)
        if not form:
            return
        def shouldUpdate(data):
            return data['type'] == 'Observable' and data['obId'] == obId
        if shouldUpdate(form['title']):
            self.setFormTitle(formId, self.controlManager.get(form['style']['class']['value']).options['titlePath'], str(value))
        style = form['style']
        bindings = self._getFormBindings(formId)
        for address, control in bindings.groupStyles.get(obId, ()):
            if '_groupDefinition' in control:
                control['style'] = groupStyle(control['_groupDefinition'])
            elif '_groupLayout' in control:
                control['style'].update(groupStyle(control['_groupLayout']))
        if shouldUpdate(style['layer']):
            self.setLayer(formId, -1, value)
        if any(shouldUpdate(style[key]) for key in ('visible', 'hideOtherForms')):
            self._refreshFormVisibility()
        geometryChanged = any(shouldUpdate(style[key]) for key in ('width', 'height', 'offsetX', 'offsetY'))
        sizeChanged = any(shouldUpdate(style[key]) for key in ('width', 'height'))
        if geometryChanged and self._layoutRootGrid(formId):
            if sizeChanged:
                self._relayoutForm(formId)
        else:
            for key, axis in (('width', 'x'), ('height', 'y')):
                if shouldUpdate(style[key]):
                    self.setSize(formId, -1, axis, getSizeDict(value))
            for key, axis in (('offsetX', 'x'), ('offsetY', 'y')):
                if shouldUpdate(style[key]):
                    self.setOffset(formId, -1, axis, getSizeDict(value))
        if obId in bindings.classIds:
            self._refreshGroupClasses(formId)
            if formId not in self.forms:
                return
            bindings = self._getFormBindings(formId)
        layoutChanged = self.updateControlsProperties(
            obId, formId, form['controls'], value, relayout=False)
        if layoutChanged or obId in bindings.groupGeometryIds:
            self._relayoutForm(formId)
        if sizeChanged or layoutChanged or obId in bindings.groupGeometryIds:
            self._layoutGroups(formId)

    def _applyDeferredFormUpdates(self, formId):
        if formId in self.__loadingForms or formId in self.__creatingForms:
            return
        pending = self.__deferredFormUpdates.pop(formId, {})
        for obId, value in pending.items():
            try:
                self._applyFormObservableUpdate(formId, obId, value)
            except:
                pass
                
    def updateControlsProperties(self, obId, formId, controls, value, oldValues=None, relayout=True):
        if oldValues is None:
            oldValues = {}
        layoutChanged = False
        def shouldUpdate(data, obId):
            return data['type'] == "Observable" and data['obId'] == obId
        bindings = self._getFormBindings(formId)
        for index, control in bindings.controls.get(obId, ()):
            controlCls = self.controlManager.get(control['style']['class']['value'])
            if controlCls.typeId == ControlType.ListView:
                if index in bindings.itemChanges.get(obId, ()):
                    self.setListviewProperties(formId, index, controlCls, self.getControl(formId, index))
                elif shouldUpdate(control['value'], obId):
                    self._refreshListviewSelection(formId, index, controlCls)
                emptyText = control['style'].get('emptyText')
                if emptyText is not None and shouldUpdate(emptyText, obId):
                    self.getControl(formId, index).GetChildByPath(
                        controlCls.options['emptyLabelPath']).asLabel().SetText(emptyText['value'])
            if "label" in control:
                if shouldUpdate(control['label'], obId):
                    self.setControlLabel(formId, index, controlCls.options["labelPaths"], str(value))
                    control['label']['value'] = value
            if controlCls.typeId == ControlType.Slider and any(
                    shouldUpdate(control[key], obId) for key in ('value', 'minValue', 'maxValue', 'step')):
                self._refreshSlider(formId, index, control, controlCls)
            if "value" in control:
                if shouldUpdate(control['value'], obId):
                    c = self.getControl(formId, index)
                    if controlCls.typeId == ControlType.Textfield:
                        c.GetChildByPath(controlCls.options['textfieldPath']).asTextEditBox().SetEditText(str(value))
                        record = self.__inputRecords.get(formId, {}).get(index)
                        if record is not None:
                            record['value'] = value
                    elif controlCls.typeId == ControlType.Dropdown:
                        label = ""
                        for item in control['items']:
                            if item['value']['value'] == value:
                                label = item['label']['value']
                                break
                        for labelPath in controlCls.options['boxLabelPaths']:
                            c.GetChildByPath(controlCls.options['dropdownPath'] + labelPath).asLabel().SetText(str(label))
                    control['value']['value'] = value
            if "state" in control:
                if shouldUpdate(control['state'], obId):
                    c = self.getControl(formId, index)
                    c.asSwitchToggle().SetToggleState(value, controlCls.options['togglePath'])
                    control['state']['value'] = value
                    record = self.__inputRecords.get(formId, {}).get(index)
                    if record is not None:
                        record['value'] = value
            if "style" in control:
                style = control['style']
                if controlCls.typeId == ControlType.Label and 'fontSize' in style and shouldUpdate(style['fontSize'], obId):
                    self._setLabelFontSize(formId, index, controlCls, style['fontSize']['value'])
                    layoutChanged = True
                for key in ('width', 'height', 'offsetX', 'offsetY', 'visible'):
                    if shouldUpdate(style[key], obId):
                        style[key]['value'] = value
                        layoutChanged = True
        if layoutChanged and relayout:
            self._relayoutForm(formId)
        return layoutChanged

    def _refreshSlider(self, formId, index, data, cls):
        value = getStepedValue(data['value']['value'], data['minValue']['value'],
                              data['maxValue']['value'], data['step']['value'])
        root = self.getControl(formId, index)
        percentage = getSliderPercentage(value, data['minValue']['value'], data['maxValue']['value'], data['step']['value'])
        root.GetChildByPath(cls.options['sliderPath']).asSlider().SetSliderValue(percentage)
        for path in cls.options['valuePaths']:
            root.GetChildByPath(path).asLabel().SetText(str(value))
        record = self.__inputRecords.get(formId, {}).get(index)
        if record is not None:
            for key in ('minValue', 'maxValue', 'step'):
                record[key] = data[key]['value']
            record['value'] = value
            record['lastPercentage'] = percentage

    def _notifyCustomUpdate(self, formId, index, key, oldValue, newValue):
        if formId not in self.forms:
            return
        self.__pendingCustomUpdates.setdefault(formId, deque()).append((index, key, oldValue, newValue))
        self._flushCustomUpdates(formId)

    def _flushCustomUpdates(self, formId):
        if (formId in self.__loadingForms or formId in self.__creatingForms
                or formId in self.__flushingCustomUpdates):
            return
        form = self.forms.get(formId)
        if not form:
            return
        pending = self.__pendingCustomUpdates.get(formId)
        if not pending:
            return
        self.__flushingCustomUpdates.add(formId)
        try:
            while pending and self.forms.get(formId) is form:
                index, key, oldValue, newValue = pending[0]
                state = self.__customControls.get(formId, {}).get(index)
                if not state:
                    # Unprepared Group children can queue params updates before
                    # their actual registered type is known. Ordinary controls
                    # have no custom update callback and must not block the queue.
                    pending.popleft()
                    continue
                if not state['ready']:
                    break
                pending.popleft()
                control = self._getControlData(formId, index)
                controlCls = self.controlManager.get(control['style']['class']['value'])
                callback = controlCls.options.get('onObservableUpdate')
                if callback:
                    from ...utils.type import ObservableUpdateArguments
                    params = unwrapWrappedValue(control.get('params', {}))
                    try:
                        callback(ObservableUpdateArguments(oldValue, newValue, key, self, state['control'], params))
                    except Exception as error:
                        print('[ERROR] FormUI custom callback (formId=%s, index=%s, key=%s): %s' %
                              (formId, index, key, error))
        finally:
            self.__flushingCustomUpdates.discard(formId)

    def _writeInputValue(self, formId, index, key, value):
        data = self._getControlData(formId, index)
        binding = data[key]
        obId = binding['obId']
        if obId is None:
            return
        binding['value'] = value
        from ...utils.environment import getClientSystem, getSystem
        serverOwned = obId >= 0 if isinstance(index, tuple) else self.forms[formId]['fromServer']['value']
        if serverOwned:
            getClientSystem().NotifyToServer('applyObservableUpdate', {'obId': obId, 'value': value})
        else:
            getSystem().observableManager.get(obId).setValue(value)

    def onToggleUpdate(self, formId, index, value):
        self._writeInputValue(formId, index, 'state', value)

    def onSliderUpdate(self, formId, index, value):
        self._writeInputValue(formId, index, 'value', value)

    def onTextfieldUpdate(self, formId, index, value):
        self._writeInputValue(formId, index, 'value', value)

    def onDropdownValueUpdate(self, formId, index, value):
        self._writeInputValue(formId, index, 'value', value)

    def onDropdownItemClick(self, formId, index, value, label):
        controlData = self._getControlData(formId, index)
        controlCls = self.controlManager.get(controlData['style']['class']['value'])
        control = self.getControl(formId, index)
        for labelPath in controlCls.options['boxLabelPaths']:
            control.GetChildByPath(controlCls.options['dropdownPath'] + labelPath).asLabel().SetText(str(label))
        if controlData['value']['value'] != value:
            self.onDropdownValueUpdate(formId, index, value)
            controlData['value']['value'] = value
        self._closeDropdown(formId)

    def onDropdownBoxClick(self, formId, index):
        controlData = self._getControlData(formId, index)
        controlCls = self.controlManager.get(controlData['style']['class']['value'])
        self._closeDropdown(formId)
        control = self.getControl(formId, index)
        items = control.GetChildByPath(controlCls.options['contentPath'])
        items.SetVisible(True)
        box = control.GetChildByPath(controlCls.options['dropdownPath'])
        box.SetVisible(False)
        self.forms[formId]['dropdown'] = {'index': index, 'box': box, 'items': items, 'control': control}
        self._relayoutForm(formId)

    def _closeDropdown(self, formId, relayout=True):
        state = self.forms[formId].pop('dropdown', None)
        if state:
            state['items'].SetVisible(False)
            state['box'].SetVisible(True)
            if relayout:
                self._relayoutForm(formId)

    def _updateDropdownExtent(self, formId):
        form = self.forms[formId]
        state = form.get('dropdown')
        if not state:
            return
        index = state['index']
        addresses = ([index[0]] + [index[:length] for length in range(2, len(index) + 1)]
                     if isinstance(index, tuple) else [index])
        if (self.getControl(formId, index) is not state['control'] or
                any(not self._getControlData(formId, address)['style']['visible']['value'] for address in addresses)):
            self._closeDropdown(formId, relayout=False)
            return
        # The menu overlays other cells. Only its actual bottom extends the scroll area.
        top = sum(self.getControl(formId, address).GetPosition()[1] for address in addresses)
        bottom = top + state['items'].GetPosition()[1] + state['items'].GetSize()[1]
        panel = self._formControl(formId, form['basePath'])
        content = getScrollingContent(panel)
        content.SetFullSize('y', {'absoluteValue': max(form['_layoutHeight'], bottom),
                                  'relativeValue': 0.0, 'followType': 'parent'})

    def _hasFrameWork(self):
        return bool(self._gridWatches or self.__repeatFuncs or self.toggles or self.sliders or self.textfields)

    def Update(self):
        self._updateGridLayouts()
        pending, self.__repeatFuncs = self.__repeatFuncs, []
        survivors = []
        for funcData in pending:
            try:
                funcData['function']()
            except:
                pass
            if self._destroyed:
                return
            # Count attempts too: a failing task must not run forever each frame.
            funcData['current'] += 1
            if funcData['current'] < funcData['times']:
                survivors.append(funcData)
        # Work added by a callback starts on the next frame, after existing tasks.
        self.__repeatFuncs = survivors + self.__repeatFuncs
        loading = bool(self.__loadingForms)
        if self._showLoadingIndicator and self.__loadingVisible != loading:
            if self.__loadingControl is None:
                self.__loadingControl = self.GetBaseUIControl('/pre_screen')
            if self.__loadingControl:
                self.__loadingControl.SetVisible(loading)
                self.__loadingVisible = loading
        for data in tuple(self.toggles):
            if not self._inputIsAlive(data):
                continue
            try:
                value = data['control'].GetToggleState(data['path'])
                if value != data['value']:
                    data['value'] = value
                    self._getControlData(data['formId'], data['index'])['state']['value'] = value
                    self.onToggleUpdate(data['formId'], data['index'], value)
            except:
                continue
        for data in tuple(self.sliders):
            if not self._inputIsAlive(data):
                continue
            try:
                percentage = data['control'].GetSliderValue()
                if 'lastPercentage' in data and percentage == data['lastPercentage']:
                    continue
                minV = data['minValue']
                maxV = data['maxValue']
                step = data['step']
                value = getSliderValue(percentage, minV, maxV, step)
                data['lastPercentage'] = percentage
                if value != data['value']:
                    root = self.getControl(data['formId'], data['index'])
                    for valuePath in data['valuePaths']:
                        root.GetChildByPath(valuePath).asLabel().SetText(str(value))
                    data['value'] = value
                    self._getControlData(data['formId'], data['index'])['value']['value'] = value
                    self.onSliderUpdate(data['formId'], data['index'], value)
            except:
                continue
        for data in tuple(self.textfields):
            if not self._inputIsAlive(data):
                continue
            try:
                value = data['control'].GetEditText()
                if value != data['value']:
                    data['value'] = value
                    self.onTextfieldUpdate(data['formId'], data['index'], value)
            except:
                continue

    def addRepeatFunc(self, function, times):
        if not self._destroyed:
            self.__repeatFuncs.append({"function": function, "times": times, "current": 0})


class Screen(_Screen, ScreenNode):
    """The FormUI-owned screen driven by the engine's ScreenNode lifecycle."""

    def __init__(self, namespace, name, params):
        from ...utils.environment import getClientSystem
        ScreenNode.__init__(self, namespace, name, params)
        self._initRenderer(getClientSystem())
        self._popPending = False
        self._popOnUpdate = False
        self._system._registerFormScreen(self)

    def addForm(self, formData, pendingCustomUpdates=()):
        _Screen.addForm(self, formData, pendingCustomUpdates)
        self._popPending = self._popOnUpdate = False

    def _afterFormClosed(self, form):
        if not form.get('options', {}).get('combineUI'):
            self._requestPop()

    def _requestPop(self):
        if self._destroyed or self._popPending or self.forms:
            return
        self._popPending = True
        c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddTimer(0.05, self._popIfCurrent)

    def _popIfCurrent(self):
        if not self._popPending or self._destroyed:
            return
        if self.forms:
            self._popPending = self._popOnUpdate = False
        elif getTopScreenNode() is self:
            self._popPending = self._popOnUpdate = False
            c.PopScreen()
        else:
            self._popOnUpdate = True

    def Update(self):
        if self._popOnUpdate:
            self._popIfCurrent()
        if not self._destroyed:
            _Screen.Update(self)

    def Destroy(self):
        self._hostClosed()
        self._system._formScreenDestroyed(self)
        destroy = getattr(ScreenNode, 'Destroy', None)
        if destroy is not None:
            destroy(self)


class EmbeddedScreen(_Screen):
    """Render on a foreign ScreenNode without taking over its methods or UI stack."""
    _showLoadingIndicator = False

    def __init__(self, system, host, panel, name):
        self._hostNode = host
        self._panel = panel
        self._panelPath = '/' + name
        self.popping = False
        self._initRenderer(system, ready=True)

    def _formParent(self):
        return self._panel

    def __getattr__(self, name):
        # Custom controls can use both host-native methods and FormUI's addRepeatFunc.
        return getattr(self._hostNode, name)

    def panelOn(self, node):
        try:
            return node.GetBaseUIControl(self._panelPath)
        except Exception:
            return None

    def _afterFormClosed(self, form):
        if not self.forms:
            self._system._releaseEmbeddedScreen(self)
