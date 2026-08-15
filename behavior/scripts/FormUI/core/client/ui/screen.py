# -*- coding: utf-8 -*-
import math

from ...general.enums.controlType import ControlType
from ...utils.ui import getScrollingContent, getSizeDict, getSliderPercentage, getSliderValue, getStepedValue

import mod.client.extraClientApi as c

ScreenNode = c.GetScreenNodeCls()

class Screen(ScreenNode):
    
    def __init__(self, namespace, name, params):
        from ...utils.environment import getClientSystem
        ScreenNode.__init__(self, namespace, name, params)
        self.observables = []
        self.forms = {}
        self.controlManager = getClientSystem().controlManager
        self.__allready = False
        self.toggles = []
        self.sliders = []
        self.textfields = []

    def isAllReady(self):
        return self.__allready

    def Create(self):
        self.forms = {}
        self.toggles = []
        self.observables = []
        self.__allready = True

    def addForm(self, formData):
        self.observables += formData['observables']
        self.observables = list(set(self.observables))

        title = formData['title']
        style = formData['style']
        formId = formData['formId']['value']
        formData['basePath'] = self.controlManager.get(style['class']['value']).options['scrollingPanelPath']
        if formId in self.forms:
            print("[ERROR] FormUI: Form with id %s already exists." % formId)
            return

        self.forms[formId] = formData
        def create():
            if self.GetBaseUIControl("/panel"):
                c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(timerId)
                base = self.controlManager.get(style['class']['value'])
                baseControl = self.CreateChildControl(base.path, "fm%s" % formId, self.GetBaseUIControl("/panel"))
                self.forms[formId]['defaultSize'] = (baseControl.GetFullSize("x"), baseControl.GetFullSize("y"))
                self.setSize(formId, -1, "x", getSizeDict(style['width']['value']), baseControl)
                self.setSize(formId, -1, "y", getSizeDict(style['height']['value']), baseControl)
                self.forms[formId]['defaultOffset'] = (baseControl.GetFullPosition("x"), baseControl.GetFullPosition("y"))
                self.setOffset(formId, -1, "x", getSizeDict(style['offsetX']['value']), baseControl)
                self.setOffset(formId, -1, "y", getSizeDict(style['offsetY']['value']), baseControl)
                close = baseControl.GetChildByPath(base.options['closeBtnPath']).asButton()
                close.AddTouchEventParams({"formId": formId})
                close.SetButtonTouchUpCallback(self.onClose)
                self.setFormTitle(formId, base.options['titlePath'], title['value'])
                self.setFormContent(formId, base.options['scrollingPanelPath'])
                self.setLayer(formId, -1, formData['options']['layer']['value'], baseControl)
        timerId = c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddRepeatedTimer(0.05, create)

    def onClose(self, data):
        formId = data['AddTouchEventParams']['formId']
        del self.forms[formId]
        for data in (self.sliders, self.textfields, self.toggles):
            for controlData in data:
                if controlData['formId'] == formId:
                    del controlData
        self.RemoveChildControl("/panel/fm%s" % formId)
        if not self.forms:
            c.PopScreen()
        from ...utils.environment import getSystem
        getSystem().NotifyToServer("closeForm%s" % formId, {"closeReason": "api" if "closeByInterface" in data else "user"})

    def setLayer(self, formId, controlIndex, value, c=None):
        if formId not in self.forms:
            return
        if controlIndex == -1:
            control = self.GetBaseUIControl("/panel/fm%s" % formId)
        else:
            control = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % controlIndex)
        if c:
            control = c
        control.SetLayer(value)

    def setSize(self, formId, controlIndex, axis, value, c=None):
        if formId not in self.forms:
            return
        if not value:
            value = self.forms['defaultSize'][0 if axis == 'x' else 1] if controlIndex == -1 else self.forms[formId]['controls'][controlIndex]['defaultSize'][0 if axis == 'x' else 1]
        if controlIndex == -1:
            control = self.GetBaseUIControl("/panel/fm%s" % formId)
        else:
            control = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % controlIndex)
            if self.controlManager.get(self.forms[formId]['controls'][controlIndex]['style']['class']['value']).typeId == "label" and not value:
                return
        if c:
            control = c
        control.SetFullSize(axis, value)

    def setOffset(self, formId, controlIndex, axis, value, c=None):
        if formId not in self.forms:
            return
        if not value:
            value = self.forms['defaultOffset'][0 if axis == 'x' else 1] if controlIndex == -1 else self.forms[formId]['controls'][controlIndex]['defaultOffset'][0 if axis == 'x' else 1]
        if controlIndex == -1:
            control = self.GetBaseUIControl("/panel/fm%s" % formId)
        else:
            control = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % controlIndex)
        if c:
            control = c
        control.SetFullPosition(axis, value)

    def setControlLabel(self, formId, controlIndex, labelPaths, value, c=None):
        if formId not in self.forms:
            return
        control = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % controlIndex)
        if c:
            control = c
        if isinstance(labelPaths, str):
            labelPaths = [labelPaths]
        for path in labelPaths:
            try:
                control.GetChildByPath(path).asLabel().SetText(value)
            except:
                pass

    def setFormTitle(self, formId, titlePath, value):
        control = self.GetBaseUIControl("/panel/fm%s%s" % (formId, titlePath))
        if not control:
            return
        control.asLabel().SetText(str(value))
        self.forms[formId]['title']['value'] = value

    def setFormContent(self, formId, contentPath):
        controls = self.forms[formId]['controls']
        scrollPanel = self.GetBaseUIControl("/panel/fm%s%s" % (formId, contentPath)).asScrollView()
        formStyle = self.forms[formId]['style']
        content = getScrollingContent(scrollPanel)
        index = 0
        height = 0
        temp = []
        for control in controls:
            controlCls = self.controlManager.get(control['style']['class']['value'])
            c = self.CreateChildControl(controlCls.path, "c%s" % index, content)
            self.forms[formId]['controls'][index]['defaultSize'] = (c.GetFullSize("x"), c.GetFullSize("y"))
            self.forms[formId]['controls'][index]['defaultOffset'] = (c.GetFullPosition("x"), c.GetFullPosition("y"))
            # set properties
            typeId = controlCls.typeId
            getattr(self, "set" + typeId[0].upper() + typeId[1:] + "Properties")(formId, index, controlCls, c)
            temp.append(self.setControlLayout(formId, control, c, formStyle, index, height))
            # Add height
            if not (float(index + 1) % len(formStyle['columns'])):
                height += max(temp)
                temp = []
            if index + 1 == len(controls):
                if temp:
                    height += max(temp)
                    temp = []

            onCreate = controlCls.options.get('onCreate')
            if onCreate:
                from ...utils.type import CreateArguments
                onCreate(CreateArguments(self, c))
            index += 1
        formHeight = scrollPanel.GetSize()[1]
        content.SetFullSize("y", {"absoluteValue": max(formHeight, height)})

    def moveNextControls(self, formId, index):
        controls = self.forms[formId]['controls']
        amount = len(controls)
        panel = self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))
        content = getScrollingContent(panel)
        if index >= 0:
            current = content.GetChildByPath("/c%s" % index)
            currentHeight = current.GetPosition()[1] + current.GetSize()[1]
        else:
            currentHeight = 0
        nextIndex = index + 1
        while not controls[nextIndex]['style']['visible']['value']:
            content.GetChildByPath("/c%s" % nextIndex).SetVisible(False)
            nextIndex += 1
            if nextIndex > amount - 1:
                break
        if nextIndex < amount:
            offsetY = getSizeDict(controls[nextIndex]['style']['offsetY']['value'])
            if not offsetY:
                offsetY = {
                    "relativeValue": 1.0,
                    "absoluteValue": 0.0,
                    "followType": "parent"
                }
            target = content.GetChildByPath("/c%s" % nextIndex)
            target.SetVisible(True)
            target.SetFullPosition("y", {
                "relativeValue": offsetY['relativeValue'],
                "absoluteValue": offsetY['absoluteValue'] + currentHeight,
                "followType": "parent"
            })
        if nextIndex < amount - 1:
            self.moveNextControls(formId, nextIndex)
        else:
            content.SetFullSize("y", {"absoluteValue": max(panel.GetSize()[1], target.GetSize()[1] + target.GetPosition()[1])})

    def setControlLayout(self, formId, controlData, control, formStyle, index, height):
        columns = formStyle['columns']
        # Process origin data.
        temp = []
        for i in range(len(columns)):
            temp.append(columns[i]['value'])
        columns = temp

        total = float(sum(columns))
        sizeX = getSizeDict(controlData['style']['width']['value'])
        if not sizeX:
            sizeX = self.forms[formId]['controls'][index]['defaultSize'][0]
        sizeX['relativeValue'] *= columns[index % len(columns)] / total
        self.setSize(formId, index, "x", sizeX, control)
        self.setSize(formId, index, "y", getSizeDict(controlData['style']['height']['value']), control)
        offsetX = getSizeDict(controlData['style']['offsetX']['value'])
        offsetY = getSizeDict(controlData['style']['offsetY']['value'])
        if not offsetX:
            offsetX = {"relativeValue": 1.0, "absoluteValue": 0.0}
        if not offsetY:
            offsetY = {"relativeValue": 1.0, "absoluteValue": 0.0}
        self.setOffset(formId, index, "x", {
            "relativeValue": offsetX['relativeValue'] * sum(columns[0: index % len(columns)]) / total, 
            "absoluteValue": offsetX['absoluteValue'],
            "followType": "parent"
        }, control)
        self.setOffset(formId, index, "y", {
            "relativeValue": offsetY['relativeValue'],
            "absoluteValue": height + offsetY['absoluteValue'],
            "followType": "parent"
        }, control)
        if controlData['style']['visible']['value']:
            return control.GetSize()[1]
        else:
            control.SetVisible(False)
            return 0

    def setButtonProperties(self, formId, index, controlCls, c):
        btn = c.GetChildByPath(controlCls.options['buttonPath'])
        if not btn:
            return
        btn = btn.asButton()
        if not btn:
            return
        controlData = self.forms[formId]['controls'][index]
        btn.AddTouchEventParams()
        btn.SetButtonTouchUpCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onClick']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveInCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveIn']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveOutCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveOut']['value']: self.onButtonClick(formId, callbackId))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], btn)

    def setToggleProperties(self, formId, index, controlCls, c):
        toggle = c.asSwitchToggle()
        if not toggle:
            return
        controlData = self.forms[formId]['controls'][index]
        self.toggles.append({"control": toggle, "formId": formId, "index": index, "value": controlData['state']['value'], "path": controlCls.options['togglePath']})
        toggle.SetToggleState(bool(controlData['state']['value']), controlCls.options['togglePath'])
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], toggle)

    def setLabelProperties(self, formId, index, controlCls, c):
        label = c
        if not label:
            return
        controlData = self.forms[formId]['controls'][index]
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], label)

    def setSliderProperties(self, formId, index, controlCls, c):
        slider = c.GetChildByPath(controlCls.options['sliderPath'])
        if not slider:
            return
        slider = slider.asSlider()
        if not slider:
            return
        controlData = self.forms[formId]['controls'][index]
        sliderValue = getStepedValue(controlData['value']['value'], controlData['minValue']['value'], controlData['maxValue']['value'], controlData['step']['value'])
        self.sliders.append({"control": slider, "formId": formId, "index": index, "value": sliderValue, "minValue": controlData['minValue']['value'], "maxValue": controlData['maxValue']['value'], "step": controlData['step']['value'], "valuePaths": controlCls.options['valuePaths']})
        slider.SetSliderValue(getSliderPercentage(sliderValue, controlData['minValue']['value'], controlData['maxValue']['value'], controlData['step']['value']))
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
        controlData = self.forms[formId]['controls'][index]
        self.textfields.append({"control": textfield, "formId": formId, "index": index, "value": controlData['value']['value']})
        textfield.SetEditText(str(controlData['value']['value']))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], textfield)

    def setDropdownProperties(self, formId, index, controlCls, c):
        dropdown = c.GetChildByPath(controlCls.options['dropdownPath'])
        if not dropdown:
            return
        dropdown = dropdown.asButton()
        if not dropdown:
            return
        dropdown.AddTouchEventParams()
        dropdown.SetButtonTouchUpCallback(lambda data: self.onDropdownBoxClick(formId, index))
        controlData = self.forms[formId]['controls'][index]
        content = c.GetChildByPath(controlCls.options['contentPath'])
        itemIndex = 0
        height = 0
        current = ""
        for item in controlData['items']:
            if item['value']['value'] == controlData['value']['value']:
                current = item['label']['value']
            itemControl = self.CreateChildControl(controlCls.options['itemControl'], "item_%s" % item['value']['value'], content)
            itemControl.asButton().AddTouchEventParams()
            itemControl.asButton().SetButtonTouchUpCallback(lambda data, itemIndex=item['value']['value'], itemLabel=item['label']['value']: self.onDropdownItemClick(formId, index, itemIndex, itemLabel))
            itemControl.GetChildByPath("/button_label").asLabel().SetText(item['label']['value'])
            height = itemControl.GetFullSize("y")['absoluteValue']
            itemControl.SetFullPosition("y", {"absoluteValue": itemIndex * height})
            itemIndex += 1
        content.SetFullSize("y", {"absoluteValue": itemIndex * height + 2})
        for labelPath in controlCls.options['boxLabelPaths']:
            dropdown.GetChildByPath(labelPath).asLabel().SetText(str(current))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], c)

    def setCustomProperties(self, formId, index, controlCls, c):
        pass

    def onButtonClick(self, formId, callbackId):
        from ...utils.environment import getClientSystem
        data = {"formId": formId, "callbackId": callbackId}
        if self.forms[formId]['fromServer']['value']:
            getClientSystem().NotifyToServer("buttonTriggerCallback", data)
        else:
            getClientSystem().onButtonTrigger(data)

    def getControl(self, formId, index):
        content = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath'])))
        return content.GetChildByPath("/c%s" % index)

    def isFormScreen(self):
        return True
    
    def applyObservableUpdate(self, id, value):
        def shouldUpdate(data, obId):
            return data['type'] == "Observable" and data['obId'] == obId
        if id in self.observables:
            for formId in self.forms:
                try:
                    form = self.forms[formId]
                    if form['title']['type'] == "Observable" and form['title']['obId'] == id:
                        self.setFormTitle(formId, self.controlManager.get(form['style']['class']['value']).options['titlePath'], str(value))
                    style = form['style']
                    if shouldUpdate(form['options']['layer'], id):
                        self.setLayer(formId, -1, value)
                        style['layer']['value'] = value
                    if shouldUpdate(style['width'], id):
                        self.setSize(formId, -1, "x", getSizeDict(value))
                        style['width']['value'] = value
                    if shouldUpdate(style['height'], id):
                        self.setSize(formId, -1, "y", getSizeDict(value))
                        style['height']['value'] = value
                    if shouldUpdate(style['offsetX'], id):
                        self.setOffset(formId, -1, "x", getSizeDict(value))
                        style['offsetX']['value'] = value
                    if shouldUpdate(style['offsetY'], id):
                        self.setOffset(formId, -1, "y", getSizeDict(value))
                        style['offsetY']['value'] = value
                    self.updateControlsProperties(id, formId, form['controls'], value)
                except:
                    pass
                
    def updateControlsProperties(self, obId, formId, controls, value):
        index = 0
        def shouldUpdate(data, obId):
            return data['type'] == "Observable" and data['obId'] == obId
        for control in controls:
            controlCls = self.controlManager.get(control['style']['class']['value'])
            if "label" in control:
                if shouldUpdate(control['label'], obId):
                    self.setControlLabel(formId, index, controlCls.options["labelPaths"], str(value))
                    control['label']['value'] = value
            sliderShouldUpdate = False
            if "minValue" in control:
                if shouldUpdate(control['minValue'], obId):
                    control['minValue']['value'] = value
                    for sliderData in self.sliders:
                        if sliderData['index'] == index:
                            sliderData['minValue'] = value
                            break
                    sliderShouldUpdate = True
            if "maxValue" in control:
                if shouldUpdate(control['maxValue'], obId):
                    control['maxValue']['value'] = value
                    for sliderData in self.sliders:
                        if sliderData['index'] == index:
                            sliderData['maxValue'] = value
                            break
                    sliderShouldUpdate = True
            if "step" in control:
                if shouldUpdate(control['step'], obId):
                    control['step']['value'] = value
                    for sliderData in self.sliders:
                        if sliderData['index'] == index:
                            sliderData['step'] = value
                            break
                    sliderShouldUpdate = True
            if sliderShouldUpdate:
                c = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % index)
                c.GetChildByPath(controlCls.options['sliderPath']).asSlider().SetSliderValue(getSliderPercentage(control['value']['value'], control['minValue']['value'], control['maxValue']['value'], control['step']['value']))
            if "value" in control:
                if shouldUpdate(control['value'], obId):
                    c = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % index)
                    if controlCls.typeId == ControlType.Slider:
                        c.GetChildByPath(controlCls.options['sliderPath']).asSlider().SetSliderValue(getSliderPercentage(value, control['minValue']['value'], control['maxValue']['value'], control['step']['value']))
                        stepedValue = getStepedValue(value, control['minValue']['value'], control['maxValue']['value'], control['step']['value'])
                        for valuePath in controlCls.options['valuePaths']:
                            c.GetChildByPath(valuePath).asLabel().SetText(str(stepedValue))
                        for sliderData in self.sliders:
                            if sliderData['index'] == index:
                                sliderData['value'] = stepedValue
                                break
                    elif controlCls.typeId == ControlType.Textfield:
                        c.GetChildByPath(controlCls.options['textfieldPath']).asTextEditBox().SetEditText(str(value))
                        for textFieldData in self.textfields:
                            if textFieldData['index'] == index:
                                textFieldData['value'] = value
                                break
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
                    c = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath']))).GetChildByPath("/c%s" % index)
                    c.asSwitchToggle().SetToggleState(value, controlCls.options['togglePath'])
                    control['state']['value'] = value
                    for toggleData in self.toggles:
                        if toggleData['index'] == index:
                            toggleData['value'] = value
                            break
            if "style" in control:
                style = control['style']
                if shouldUpdate(style['width'], obId):
                    self.setSize(formId, index, "x", getSizeDict(value))
                    style['width']['value'] = value
                if shouldUpdate(style['height'], obId):
                    self.setSize(formId, index, "y", getSizeDict(value))
                    style['height']['value'] = value
                    self.moveNextControls(formId, index)
                if shouldUpdate(style['offsetX'], obId):
                    self.setOffset(formId, index, "x", getSizeDict(value))
                    style['offsetX']['value'] = value
                if shouldUpdate(style['offsetY'], obId):
                    self.setOffset(formId, index, "y", getSizeDict(value))
                    style['offsetY']['value'] = value
                if shouldUpdate(style['visible'], obId):
                    style['visible']['value'] = value
                    self.moveNextControls(formId, index - 1)
            index += 1

    def onToggleUpdate(self, formId, index, value):
        data = self.forms[formId]['controls'][index]
        if data['state']['obId'] != -1:
            self.forms[formId]['controls'][index]['state']['value'] = value
            from ...utils.environment import getClientSystem, getSystem
            if self.forms[formId]['fromServer']['value']:
                getClientSystem().NotifyToServer("applyObservableUpdate", {"obId": data['state']['obId'], "value": value})
            else:
                getSystem().observableManager.get(data['state']['obId']).setValue(value)

    def onSliderUpdate(self, formId, index, value):
        data = self.forms[formId]['controls'][index]
        if data['value']['obId'] != -1:
            self.forms[formId]['controls'][index]['value']['value'] = value
            from ...utils.environment import getClientSystem, getSystem
            if self.forms[formId]['fromServer']['value']:
                getClientSystem().NotifyToServer("applyObservableUpdate", {"obId": data['value']['obId'], "value": value})
            else:
                getSystem().observableManager.get(data['value']['obId']).setValue(value)

    def onTextfieldUpdate(self, formId, index, value):
        data = self.forms[formId]['controls'][index]
        if data['value']['obId'] != -1:
            self.forms[formId]['controls'][index]['value']['value'] = value
            from ...utils.environment import getClientSystem, getSystem
            if self.forms[formId]['fromServer']['value']:
                getClientSystem().NotifyToServer("applyObservableUpdate", {"obId": data['value']['obId'], "value": value})
            else:
                getSystem().observableManager.get(data['value']['obId']).setValue(value)

    def onDropdownValueUpdate(self, formId, index, value):
        data = self.forms[formId]['controls'][index]
        if data['value']['obId'] != -1:
            self.forms[formId]['controls'][index]['value']['value'] = value
            from ...utils.environment import getClientSystem, getSystem
            if self.forms[formId]['fromServer']['value']:
                getClientSystem().NotifyToServer("applyObservableUpdate", {"obId": data['value']['obId'], "value": value})
            else:
                getSystem().observableManager.get(data['value']['obId']).setValue(value)

    def onDropdownItemClick(self, formId, index, value, label):
        controlData = self.forms[formId]['controls'][index]
        controlCls = self.controlManager.get(controlData['style']['class']['value'])
        content = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath'])))
        control = content.GetChildByPath("/c%s" % index)
        for labelPath in controlCls.options['boxLabelPaths']:
            control.GetChildByPath(controlCls.options['dropdownPath'] + labelPath).asLabel().SetText(str(label))
        if controlData['value']['value'] != value:
            self.onDropdownValueUpdate(formId, index, value)
        if "tempHeight" in self.forms[formId]:
            self.moveNextControls(formId, -1)
            # content.SetFullSize("y", {"absoluteValue": self.forms[formId]['tempHeight']})
            del self.forms[formId]['dropdown']
        control.GetChildByPath(controlCls.options['contentPath']).SetVisible(False)

    def onDropdownBoxClick(self, formId, index):
        controlData = self.forms[formId]['controls'][index]
        controlCls = self.controlManager.get(controlData['style']['class']['value'])
        content = getScrollingContent(self.GetBaseUIControl("/panel/fm%s%s" % (formId, self.forms[formId]['basePath'])))
        if self.forms[formId].get("dropdown"):
            self.forms[formId].get("dropdown").SetVisible(False)
            content.SetFullSize("y", {"absoluteValue": self.forms[formId]['tempHeight']})
        control = content.GetChildByPath("/c%s" % index)
        items = control.GetChildByPath(controlCls.options['contentPath'])
        items.SetVisible(True)
        heightRemain = items.GetSize()[1] - control.GetSize()[1] + 15
        i = index + 1
        maxControls = len(self.forms[formId]['controls'])
        self.forms[formId]["dropdown"] = items
        while heightRemain > 0:
            if i + 1 >= maxControls:
                break
            temp = content.GetChildByPath("/c%s" % i)
            if temp.GetVisible():
                heightRemain -= temp.GetSize()[1]
            i += 1
        if heightRemain > 0:
            self.forms[formId]['tempHeight'] = content.GetSize()[1]
            content.SetFullSize("y", {"absoluteValue": content.GetSize()[1] + heightRemain})

    def Update(self):
        try:
            for data in self.toggles:
                value = data['control'].GetToggleState(data['path'])
                if value != data['value']:
                    self.onToggleUpdate(data['formId'], data['index'], value)
                    self.toggles[self.toggles.index(data)]['value'] = value
                    self.forms[data['formId']]['controls'][data['index']]['state']['value'] = value
            for data in self.sliders:
                minV = data['minValue']
                maxV = data['maxValue']
                step = data['step']
                value = getSliderValue(data['control'].GetSliderValue(), minV, maxV, step)
                path = data['control'].GetPath()# type: str
                path = path[:path.rfind("/")]
                for valuePath in data['valuePaths']:
                    self.GetBaseUIControl(path + valuePath).asLabel().SetText(str(value))
                if value != data['value']:
                    self.onSliderUpdate(data['formId'], data['index'], value)
                    self.sliders[self.sliders.index(data)]['value'] = value
                    self.forms[data['formId']]['controls'][data['index']]['value']['value'] = value
            for data in self.textfields:
                value = data['control'].GetEditText()
                if value != data['value']:
                    self.onTextfieldUpdate(data['formId'], data['index'], value)
                    self.textfields[self.textfields.index(data)]['value'] = value
        except:
            pass
            
                
        