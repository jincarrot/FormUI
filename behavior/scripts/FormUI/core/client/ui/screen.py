# -*- coding: utf-8 -*-
import math
from ...utils.ui import getSizeDict

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

    def isAllReady(self):
        return self.__allready

    def Create(self):
        self.forms = {}
        self.observables = []
        self.__allready = True

    def addForm(self, formData):
        self.observables += formData['observables']
        self.observables = list(set(self.observables))

        title = formData['title']
        style = formData['style']
        controls = formData['controls']
        formId = formData['formId']['value']
        if formId in self.forms:
            return
        
        self.forms[formId] = formData

        def create():
            if self.GetBaseUIControl("/panel"):
                c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(timerId)
                base = self.controlManager.get(style['class']['value'])
                baseControl = self.CreateChildControl(base.path, "fm%s" % formId, self.GetBaseUIControl("/panel"))
                self.setSize(formId, -1, "x", getSizeDict(style['width']['value']), baseControl)
                self.setSize(formId, -1, "y", getSizeDict(style['height']['value']), baseControl)
                self.setOffset(formId, -1, "x", getSizeDict(style['offsetX']['value']), baseControl)
                self.setOffset(formId, -1, "y", getSizeDict(style['offsetY']['value']), baseControl)
                close = baseControl.GetChildByPath(base.options['closeBtnPath']).asButton()
                close.AddTouchEventParams()
                close.SetButtonTouchUpCallback(lambda x: c.PopScreen())
                self.setFormTitle(formId, base.options['titlePath'], title['value'])
                self.setFormContent(formId, base.options['scrollingPanelPath'])
        timerId = c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddRepeatedTimer(0.05, create)

    def setSize(self, formId, controlIndex, axis, value, c=None):
        if formId not in self.forms:
            return
        if controlIndex == -1:
            control = self.GetBaseUIControl("/panel/fm%s" % formId)
        else:
            control = self.GetBaseUIControl("/panel/fm%s/c%s" % (formId, controlIndex))
        if c:
            control = c
        control.SetFullSize(axis, value)

    def setOffset(self, formId, controlIndex, axis, value, c=None):
        if formId not in self.forms:
            return
        if controlIndex == -1:
            control = self.GetBaseUIControl("/panel/fm%s" % formId)
        else:
            control = self.GetBaseUIControl("/panel/fm%s/c%s" % (formId, controlIndex))
        if c:
            control = c
        control.SetFullPosition(axis, value)

    def setControlLabel(self, formId, controlIndex, labelPaths, value, c=None):
        if formId not in self.forms:
            return
        control = self.GetBaseUIControl("/panel/fm%s/c%s" % (formId, controlIndex))
        if c:
            control = c
        for path in labelPaths:
            control.GetChildByPath(path).asLabel().SetText(value)

    def setFormTitle(self, formId, titlePath, value):
        control = self.GetBaseUIControl("/panel/fm%s%s" % (formId, titlePath))
        control.asLabel().SetText(value)
        self.forms[formId]['title']['value'] = value

    def setFormContent(self, formId, contentPath):
        controls = self.forms[formId]['controls']
        scrollPanel = self.GetBaseUIControl("/panel/fm%s%s" % (formId, contentPath)).asScrollView()
        formStyle = self.forms[formId]['style']
        # content = scrollPanel.GetChildByPath("/scroll_touch/scroll_view/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content")
        # content = scrollPanel.GetChildByPath("/scroll_touch/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content")
        content = scrollPanel.GetScrollViewContentControl()
        index = 0
        height = 2
        temp = []
        for control in controls:
            controlCls = self.controlManager.get(control['style']['class']['value'])
            c = self.CreateChildControl(controlCls.path, "c%s" % index, content)
            temp.append(self.setControlLayout(formId, control, c, formStyle, index, height))
            # Add height
            if not (float(index + 1) % len(formStyle['columns'])):
                height += max(temp) + 2
                temp = []
            if index + 1 == len(controls):
                if temp:
                    height += max(temp) + 2
                    temp = []
            # set properties
            if controlCls.typeId == "button":
                self.setButtonProperties(formId, index, controlCls, c)
            elif controlCls.typeId == "toggle":
                pass
            index += 1
        formHeight = scrollPanel.GetSize()[1]
        content.SetFullSize("y", {"absoluteValue": max(formHeight, height)})

    def setControlLayout(self, formId, controlData, control, formStyle, index, height):
        columns = formStyle['columns']
        temp = []
        for i in range(len(columns)):
            temp.append(columns[i]['value'])
        columns = temp
        total = float(sum(columns))
        sizeX = getSizeDict(controlData['style']['width']['value'])
        sizeX['relativeValue'] *= columns[index % len(columns)] / total
        self.setSize(formId, index, "x", sizeX, control)
        self.setSize(formId, index, "y", getSizeDict(controlData['style']['height']['value']), control)
        self.setOffset(formId, index, "x", {"relativeValue": sum(columns[0: index % len(columns)]) / total, "followType": "parent"}, control)
        self.setOffset(formId, index, "y", {"absoluteValue": height}, control)
        return control.GetSize()[1]

    def setButtonProperties(self, formId, index, controlCls, c=None):
        btn = self.GetBaseUIControl("/panel/fm%s/c%s" % (formId, index))
        if c:
            btn = c
        btn = btn.asButton()
        controlData = self.forms[formId]['controls'][index]
        btn.AddTouchEventParams()
        btn.SetButtonTouchUpCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onClick']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveInCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveIn']['value']: self.onButtonClick(formId, callbackId))
        btn.SetButtonTouchMoveOutCallback(lambda x, formId=formId, callbackId=controlData['callbacks']['onMoveOut']['value']: self.onButtonClick(formId, callbackId))
        self.setControlLabel(formId, index, controlCls.options['labelPaths'], controlData['label']['value'], btn)

    def onButtonClick(self, formId, callbackId):
        if self.forms[formId]['fromServer']:
            from ...utils.environment import getClientSystem
            getClientSystem().NotifyToServer("buttonTriggerCallback", {"formId": formId, "callbackId": callbackId})

    def isFormScreen(self):
        return True
    
    def applyObservableUpdate(self, id, value):
        def shouldUpdate(data, obId):
            return data['type'] == "Observable" and data['obId'] == obId
        if id in self.observables:
            for formId in self.forms:
                form = self.forms[formId]
                if form['title']['type'] == "Observable" and form['title']['obId'] == id:
                    self.setFormTitle(formId, self.controlManager.get(form['style']['class']['value']).options['titlePath'], str(value))
                style = form['style']
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
                
    def updateControlsProperties(self, obId, formId, controls, value):
        index = 0
        def shouldUpdate(data, obId):
            return data['type'] == "Observable" and data['obId'] == obId
        for control in controls:
            controlCls = self.controlManager.get(control['style']['class']['value'])
            if "label" in control:
                if shouldUpdate(control['label'], obId):
                    self.setControlLabel(formId, index, controlCls.get("labelPaths"), str(value))
                    control['label']['value'] = value
            elif "style" in control:
                style = control['style']
                if shouldUpdate(style['width'], obId):
                    self.setSize(formId, index, "x", getSizeDict(value))
                    style['width']['value'] = value
                if shouldUpdate(style['height'], obId):
                    self.setSize(formId, index, "y", getSizeDict(value))
                    style['height']['value'] = value
                if shouldUpdate(style['offsetX'], obId):
                    self.setOffset(formId, index, "x", getSizeDict(value))
                    style['offsetX']['value'] = value
                if shouldUpdate(style['offsetY'], obId):
                    self.setOffset(formId, index, "y", getSizeDict(value))
                    style['offsetY']['value'] = value
            index += 1

                

        