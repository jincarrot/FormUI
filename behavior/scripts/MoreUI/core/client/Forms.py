# -*- coding: utf-8 -*-
import random
import mod.client.extraClientApi as clientApi
from ..config_client import *

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()

def getSystem():
    system = clientApi.GetSystem(NamespaceClient, SystemNameClient)
    if system:
        return system
    raise Exception("MoreUI运行时错误！请检查您是否在客户端导入了MoreUI.register？")

class CustomFormUI(ScreenNode):
    """Custom form."""
    
    def __init__(self, namespace, name, params):
        ScreenNode.__init__(self, namespace, name, params)
        self.options = params['options']
        self.grid_pos = self.options.get("pos", None)
        self.grid_size = self.options.get("size", None)
        self.grid_offset = self.options.get("offset", None)
        self.grid_margin = self.options.get("margin", None)
        self.sn = self
        self.basePath = ""
        self.titleLabel = params['title']
        self.formId = params['formId']
        self.data = params['data']
        self.TOUCH_PATH = "/panel/scroll_touch/scroll_view/panel/background_and_viewport/background"
        self.MOUSE_PATH = "/panel/scroll_mouse/scroll_view/stack_panel/background_and_viewport/background"
        self.content = None
        self.title = None
        self.close_btn = None
        self.panel = None
        self.move_btn = None
        self.resize_btn = None
        self.movable = self.options['movable']
        self.resizable = self.options['resizable']
        self.style = self.options['style']
        self.textFields = []
        self.toggles = []
        self.sliders = []
        self.dropdowns = {}
        self.height = 0
        self.pos = None
        self.size = None

    @property
    def formType(self):
        return "custom"
    
    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#custom_form_close')
    def Close(self, args):
        clientApi.PopScreen()

    def close(self, data):
        if self.basePath and not self.options.get("mayCloseAll", False):
            self.sn.GetBaseUIControl(self.basePath).SetVisible(False)
        else:
            clientApi.PopScreen()

    def Create(self):
        self.panel = self.sn.GetBaseUIControl(self.basePath + "/panel")
        self.content = self.sn.GetBaseUIControl(self.basePath + "/panel").asScrollView().GetScrollViewContentControl()
        self.title = self.sn.GetBaseUIControl(self.basePath + self.TOUCH_PATH + "/title")
        self.close_btn = self.sn.GetBaseUIControl(self.basePath + self.TOUCH_PATH + "/close")
        if not self.title:
            self.title = self.sn.GetBaseUIControl(self.basePath + self.MOUSE_PATH + "/title")
            self.close_btn = self.sn.GetBaseUIControl(self.basePath + self.MOUSE_PATH + "/close")
        if not self.title:
            raise Exception("Create form error!")
        self.close_btn = self.close_btn.asButton()
        self.close_btn.AddTouchEventParams({"isSwallow": True})
        self.close_btn.SetButtonTouchUpCallback(self.close)
        self.title = self.title.asLabel()
        self.title.SetText(self.titleLabel)
        self.move_btn = self.sn.GetBaseUIControl(self.basePath + "/move").asButton()
        self.move_btn.AddTouchEventParams({"isSwallow": True})
        # self.move_btn.SetButtonTouchMoveCallback(self.move)
        self.resize_btn = self.sn.GetBaseUIControl(self.basePath + "/resize").asButton()
        self.resize_btn.AddTouchEventParams({"isSwallow": True})
        # self.resize_btn.SetButtonTouchMoveCallback(self.resize)
        self.update({"data": self.data, "title": self.titleLabel, "formId": self.formId, "options": self.options})

    def Update(self):
        self.move({})
        self.resize({})
        index = 0
        for (textField, obId, value) in self.textFields:
            index += 1
            text = textField.GetEditText()
            if text != value:
                self.textFields[index - 1] = (textField, obId, text)
                getSystem().NotifyToServer(
                    "updateObservable%s" % obId, 
                    {"value": text}
                )
        index = 0
        for (toggle, obId, value) in self.toggles:
            toggled = toggle.GetToggleState()
            index += 1
            if toggled != value:
                self.toggles[index - 1] = (toggle, obId, toggled)
                getSystem().NotifyToServer(
                    "updateObservable%s" % obId, 
                    {"value": toggled}
                )
        index = 0
        for (slider, obId, value, minValue, maxValue) in self.sliders:
            steps = maxValue - minValue
            cur = int(round(slider.GetSliderValue() * steps) + minValue)
            index += 1
            if cur != value:
                self.sliders[index - 1] = (slider, obId, cur, minValue, maxValue)
                getSystem().NotifyToServer(
                    "updateObservable%s" % obId, 
                    {"value": cur}
                )

    def onClickDropdownItem(self, data):
        obId = data['AddTouchEventParams']['obId']
        control = self.sn.GetBaseUIControl(data['ButtonPath'].split("/content_panel")[0])
        button = control.GetChildByPath("/dropdown_box")
        content = control.GetChildByPath("/content_panel")
        item = self.sn.GetBaseUIControl(data['ButtonPath']).asButton()
        label = item.GetChildByPath("/button_label").asLabel().GetText()
        value = data['AddTouchEventParams']['value']
        button.GetChildByPath("/default/button_label").asLabel().SetText(label)
        button.GetChildByPath("/hover/button_label").asLabel().SetText(label)
        button.GetChildByPath("/pressed/button_label").asLabel().SetText(label)
        button.SetVisible(True)
        content.SetVisible(False)
        self.content.SetFullSize("y", {"absoluteValue": self.height})
        if self.dropdowns[obId] != value:
            getSystem().NotifyToServer(
                "updateObservable%s" % obId, 
                {"value": value}
            )

    def onClickDropdownBox(self, data):
        control = self.sn.GetBaseUIControl(data['ButtonPath'].split("/dropdown_box")[0])
        button = control.GetChildByPath("/dropdown_box")
        content = control.GetChildByPath("/content_panel")
        content.SetVisible(True)
        button.SetVisible(False)
        height = control.GetFullPosition("y")['absoluteValue']
        sizeY = content.GetSize()[1]
        self.content.SetFullSize("y", {"absoluteValue": max(height + sizeY + 20, self.height)})

    def update(self, data):
        if data['formId'] != self.formId:
            return
        self.grid_pos = data['options'].get("pos", None)
        self.grid_size = data['options'].get("size", None)
        self.grid_offset = data['options'].get("offset", None)
        self.grid_margin = data['options'].get("margin", None)
        self.data = data['data']
        self.titleLabel = data['title']
        self.textFields = []
        self.toggles = []
        self.sliders = []
        self.dropdowns = {}
        index = 0
        height = 0
        self.title.SetText(data['title'])
        self.move_btn.SetVisible(data['options']['movable'])
        self.resize_btn.SetVisible(data['options']['resizable'])
        self.close_btn.SetVisible(data['options']['closable'])
        for controlData in data['data']:
            control = self.content.GetChildByPath("/c%s" % index)
            if not controlData['visible']:
                if control:
                    control.SetVisible(False)
                index += 1
                continue
            if controlData['type'] == 'button':
                if control:
                    if control.asButton():
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height + 5})
                        height += 35
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.normal_btn", "c%s" % index, self.content).asButton()
                        control.SetFullPosition("y", {"absoluteValue": height + 5})
                        height += 35
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.normal_btn", "c%s" % index, self.content).asButton()
                    control.SetFullPosition("y", {"absoluteValue": height + 5})
                    height += 35
                # Add callbacks.
                control = control.asButton()
                control.AddTouchEventParams({"isSwallow": True})
                control.SetButtonTouchUpCallback(self.onButtonClick)
                # Update labels.
                control.GetChildByPath("/default/button_label").asLabel().SetText(controlData['label'])
                control.GetChildByPath("/hover/button_label").asLabel().SetText(controlData['label'])
                control.GetChildByPath("/pressed/button_label").asLabel().SetText(controlData['label'])
            elif controlData['type'] == 'label':
                if control:
                    if control.asLabel():
                        # Control created and is the same type, only cauculate this height.
                        pass
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.label", "c%s" % index, self.content).asLabel()
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.label", "c%s" % index, self.content).asLabel()
                control.asLabel().SetText(controlData['text'])
                control.SetFullPosition("y", {"absoluteValue": height + 5})
                height += int(control.GetSize()[1])
            elif controlData['type'] == 'divider':
                if control:
                    if control.GetChildByPath("/bg2"):
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height + 10})
                        height += 20
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.divider", "c%s" % index, self.content)
                        control.SetFullPosition("y", {"absoluteValue": height + 10})
                        height += 20
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.divider", "c%s" % index, self.content)
                    control.SetFullPosition("y", {"absoluteValue": height + 10})
                    height += 20
            elif controlData['type'] == 'textField':
                if control:
                    if control.asTextEditBox():
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height + 20})
                        height += 50
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.textfield", "c%s" % index, self.content)
                        control.SetFullPosition("y", {"absoluteValue": height + 20})
                        height += 50
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.textfield", "c%s" % index, self.content)
                    control.SetFullPosition("y", {"absoluteValue": height + 20})
                    height += 50
                control = control.asTextEditBox()
                # Set title and the value.
                control.GetChildByPath("/default/title").asLabel().SetText(controlData['label'])
                control.GetChildByPath("/hover/title").asLabel().SetText(controlData['label'])
                control.GetChildByPath("/pressed/title").asLabel().SetText(controlData['label'])
                control.SetEditText(controlData['text'])
                if controlData['clientWritable']:
                    self.textFields.append((control, controlData['textId'], controlData['text']))
            elif controlData['type'] == 'toggle':
                if control:
                    if control.GetChildByPath("/toggle"):
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 25
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.toggle", "c%s" % index, self.content)
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 25
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.toggle", "c%s" % index, self.content)
                    control.SetFullPosition("y", {"absoluteValue": height})
                    height += 25
                # Set label and the value.
                control.GetChildByPath("/title").asLabel().SetText(controlData['label'])
                toggle = control.GetChildByPath("/toggle").asSwitchToggle()
                toggle.SetToggleState(controlData['toggled'])
                if controlData['clientWritable']:
                    self.toggles.append((toggle, controlData['toggledId'], controlData['toggled']))
            elif controlData['type'] == 'slider':
                if control:
                    if control.GetChildByPath("/slider"):
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 35
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.slider", "c%s" % index, self.content)
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 35
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.slider", "c%s" % index, self.content)
                    control.SetFullPosition("y", {"absoluteValue": height})
                    height += 35
                # Set label and the current value.
                control.GetChildByPath("/label").asLabel().SetText(controlData['label'])
                slider = control.GetChildByPath("/slider").asSlider()
                steps = float(controlData['maxValue'] - controlData['minValue'])
                slider.SetSliderValue(((controlData['value'] - controlData['minValue']) / steps) if steps else 0)
                control.GetChildByPath("/value").asLabel().SetText("%s" % controlData['value'])
                if controlData['clientWritable']:
                    self.sliders.append((slider, controlData['valueId'], controlData['value'], controlData['minValue'], controlData['maxValue']))
            elif controlData['type'] == 'dropdown':
                if control:
                    if control.GetChildByPath("/dropdown_box"):
                        # Control created and is the same type, only cauculate this height.
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 50
                    else:
                        # Control created but is not the same type, delete and create it again.
                        self.sn.RemoveChildControl(control)
                        control = self.sn.CreateChildControl("oreui_controls.dropdown", "c%s" % index, self.content)
                        # initial items
                        button = control.GetChildByPath("/dropdown_box").asButton()
                        button.AddTouchEventParams({"isSwallow": True})
                        button.SetButtonTouchUpCallback(self.onClickDropdownBox)
                        content = control.GetChildByPath("/content_panel")
                        items = controlData['items']
                        if not items:
                            items = [{"label": "", "value": 0}]
                        i = 0
                        for item in items:
                            label = item['label']
                            value = item['value']
                            temp = self.sn.CreateChildControl("oreui_controls.dropdown_items", "item%s" % i, content).asButton()
                            temp.AddTouchEventParams({"isSwallow": True, "obId": controlData['valueId']})
                            temp.SetButtonTouchUpCallback(self.onClickDropdownItem)
                            temp.GetChildByPath("/button_label").asLabel().SetText(label)
                            temp.GetChildByPath("/value").asLabel().SetText("%s" % value)
                            temp.SetPosition((2, i * 30))
                            i += 1
                        content.SetFullSize("y", {"absoluteValue": index * 30})
                        content.SetVisible(False)
                        control.SetFullPosition("y", {"absoluteValue": height})
                        height += 50
                else:
                    # Control not created, create now.
                    control = self.sn.CreateChildControl("oreui_controls.dropdown", "c%s" % index, self.content)
                    # initial items
                    button = control.GetChildByPath("/dropdown_box").asButton()
                    button.AddTouchEventParams({"isSwallow": True})
                    button.SetButtonTouchUpCallback(self.onClickDropdownBox)
                    content = control.GetChildByPath("/content_panel")
                    items = controlData['items']
                    if not items:
                        items = [{"label": "", "value": 0}]
                    i = 0
                    for item in items:
                        label = item['label']
                        value = item['value']
                        temp = self.sn.CreateChildControl("oreui_controls.dropdown_items", "item%s" % i, content).asButton()
                        temp.AddTouchEventParams({"isSwallow": True, "obId": controlData['valueId'], "value": value})
                        temp.SetButtonTouchUpCallback(self.onClickDropdownItem)
                        temp.GetChildByPath("/button_label").asLabel().SetText(label)
                        temp.GetChildByPath("/value").asLabel().SetText("%s" % value)
                        temp.SetPosition((2, i * 25 + 2))
                        i += 1
                    content.SetFullSize("y", {"absoluteValue": i * 25 + 4})
                    content.SetFullPosition("y", {"absoluteValue": (i - 1) * 26 - 5})
                    content.SetVisible(False)
                    control.SetFullPosition("y", {"absoluteValue": height})
                    height += 50
                # Set label and the current value.
                control.GetChildByPath("/label").asLabel().SetText(controlData['label'])
                itemLabel = ""
                for item in controlData['items']:
                    if item['value'] == controlData['value']:
                        itemLabel = item['label']
                        break
                control.GetChildByPath("/dropdown_box/default/button_label").asLabel().SetText(itemLabel)
                control.GetChildByPath("/dropdown_box/hover/button_label").asLabel().SetText(itemLabel)
                control.GetChildByPath("/dropdown_box/pressed/button_label").asLabel().SetText(itemLabel)
                if controlData['clientWritable']:
                    self.dropdowns[controlData['valueId']] = controlData['value']

            control.SetVisible(True)
            index += 1
        self.content.SetFullSize("y", {"absoluteValue": height + 20})
        self.height = height + 20
        # Clear visible controls.
        while self.content.GetChildByPath("/c%s" % index):
            self.content.GetChildByPath("/c%s" % index).SetVisible(False)
            index += 1

    def onButtonClick(self, data):
        getSystem().NotifyToServer(
            "updateForm%s" % self.formId, 
            {
                "selection": int(data['ButtonPath'][-1]),
                "operation": "buttonClick"
            }
        )

    def move(self, data):
        if not self.move_btn or not self.move_btn.GetVisible():
            return
        size = self.panel.GetSize()
        pos = self.move_btn.GetPosition()
        posX = pos[0]
        posY = pos[1]
        if (posX - size[0] / 2 + 8, posY) == self.pos:
            return
        # scrollValue = self.panel.asScrollView().GetScrollViewPercentValue()
        self.panel.SetPosition((posX - size[0] / 2 + 8, posY))
        self.resize_btn.SetPosition((posX + size[0] / 2 - 8, posY + size[1] - 25))
        # self.panel.asScrollView().SetScrollViewPercentValue(scrollValue)
        self.pos = (posX - size[0] / 2 + 8, posY)

    def resize(self, data):
        if not self.resize_btn or not self.resize_btn.GetVisible():
            return
        pos = self.resize_btn.GetPosition()
        posX = pos[0]
        posY = pos[1]
        ori = self.panel.GetPosition()
        ori_size = self.panel.GetSize()
        size = [posX - ori[0] + 16, posY - ori[1] + 25]
        if size[0] < 60:
            size[0] = 60
        if size[1] < 60:
            size[1] = 60
        if size[0] == 60 or size[1] == 60:
            self.resize_btn.SetPosition((ori[0] + size[0] - 16, ori[1] + size[1] - 25))
        if self.size == size:
            return
        # scrollValue = self.panel.asScrollView().GetScrollViewPercentValue()
        move_ori_pos = self.move_btn.GetPosition()
        self.panel.SetSize((size[0], size[1]), True)
        self.panel.SetPosition(ori)
        self.move_btn.SetPosition((move_ori_pos[0] + size[0] / 2 - ori_size[0] / 2, move_ori_pos[1]))
        # self.panel.asScrollView().SetScrollViewPercentValue(scrollValue)
        self.size = [size[0], size[1]]

class BarFormUI(CustomFormUI):

    def __init__(self, namespace, name, params):
        ScreenNode.__init__(self, namespace, name, params)
        self.options = params['options']
        self.direction = self.options.get("direction", "vertical")
        self.grid_pos = self.options.get("pos", None)
        self.grid_size = self.options.get("size", None)
        self.grid_offset = self.options.get("offset", None)
        self.grid_margin = self.options.get("margin", None)
        self.sn = self
        self.basePath = ""
        self.titleLabel = params['title']
        self.formId = params['formId']
        self.data = params['data']
        self.TOUCH_PATH = "/panel/scroll_touch/scroll_view/panel/background_and_viewport/background"
        self.MOUSE_PATH = "/panel/scroll_mouse/scroll_view/stack_panel/background_and_viewport/background"
        self.content = None
        self.title = None
        self.close_btn = None
        self.panel = None
        self.move_btn = None
        self.resize_btn = None
        self.movable = self.options['movable']
        self.resizable = self.options['resizable']
        self.style = self.options['style']
        self.tabs = []
        self.height = 0
        self.pos = None
        self.size = None

    @property
    def formType(self):
        return "bar"
    
    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#custom_form_close')
    def Close(self, args):
        clientApi.PopScreen()

    def Update(self):
        index = 0
        for (tab, value) in self.tabs:
            if not tab:
                return
            cur = tab.GetChildByPath("/toggle").asSwitchToggle().GetToggleState()
            if cur != value:
                getSystem().NotifyToServer(
                    "updateBarForm%s" % self.formId, 
                    {
                        "selection": int(tab.GetPath()[-1]),
                        "operation": "tabButtonClick"
                    }
                )
                i = 0
                for (c, value) in self.tabs:
                    if index != i:
                        c.GetChildByPath("/toggle").asSwitchToggle().SetToggleState(False)
                    self.tabs[i] = (c, False)
                    i += 1
                self.tabs[index] = (tab, cur)
            index += 1
        
    def Create(self):
        self.panel = self.sn.GetBaseUIControl(self.basePath + "/panel")
        self.content = self.sn.GetBaseUIControl(self.basePath + "/panel")
        self.title = self.panel.GetChildByPath("/title")
        self.close_btn = self.panel.GetChildByPath("/close")
        if not self.title:
            raise Exception("Create form error!")
        self.close_btn = self.close_btn.asButton()
        self.close_btn.AddTouchEventParams({"isSwallow": True})
        self.close_btn.SetButtonTouchUpCallback(self.close)
        self.title = self.title.asLabel()
        self.title.SetText(self.titleLabel)
        self.move_btn = self.sn.GetBaseUIControl(self.basePath + "/move").asButton()
        self.move_btn.AddTouchEventParams({"isSwallow": True})
        # self.move_btn.SetButtonTouchMoveCallback(self.move)
        self.resize_btn = self.sn.GetBaseUIControl(self.basePath + "/resize").asButton()
        self.resize_btn.AddTouchEventParams({"isSwallow": True})
        # self.resize_btn.SetButtonTouchMoveCallback(self.resize)
        self.update({"data": self.data, "title": self.titleLabel, "formId": self.formId, "options": self.options})

    def update(self, data):
        if data['formId'] != self.formId:
            return
        self.grid_pos = data['options'].get("pos", None)
        self.grid_size = data['options'].get("size", None)
        self.grid_offset = data['options'].get("offset", None)
        self.grid_margin = data['options'].get("margin", None)
        self.data = data['data']
        self.titleLabel = data['title']
        self.tabs = []
        index = 0
        height = 20
        self.title.SetText(data['title'])
        self.move_btn.SetVisible(data['options']['movable'])
        self.resize_btn.SetVisible(data['options']['resizable'])
        self.close_btn.SetVisible(data['options']['closable'])
        for controlData in data['data']:
            control = self.content.GetChildByPath("/c%s" % index)
            if not controlData['visible']:
                if control:
                    control.SetVisible(False)
                index += 1
                continue
            if control:
                # Control created and is the same type, only cauculate this height.
                if self.direction == 'vertical':
                    control.SetFullPosition("y", {"absoluteValue": height + 5})
                    height += 35
                else:
                    control.SetSize((40, 20))
                    control.SetFullPosition("x", {"absoluteValue": height + 40})
                    height += 45
            else:
                # Control not created, create now.
                control = self.sn.CreateChildControl("oreui_controls.tab_btn", "c%s" % index, self.content)
                if self.direction == 'vertical':
                    control.SetFullPosition("y", {"absoluteValue": height + 5})
                    height += 35
                else:
                    control.SetSize((40, 20))
                    control.SetFullPosition("x", {"absoluteValue": height + 40})
                    height += 45
            # Update labels.
            states = [
                "unchecked",
                "checked",
                "unchecked_hover",
                "checked_hover"
            ]
            for state in states:
                control.GetChildByPath("/toggle/this_toggle/" + state + "/button_label").asLabel().SetText(controlData['label'])
            control.SetVisible(True)
            index += 1
            self.tabs.append((control, control.GetChildByPath("/toggle").asSwitchToggle().GetToggleState()))
        # Clear visible controls.
        while self.content.GetChildByPath("/c%s" % index):
            self.content.GetChildByPath("/c%s" % index).SetVisible(False)
            index += 1

class More(ScreenNode):
    
    def __init__(self, namespace, name, params):
        ScreenNode.__init__(self, namespace, name, params)
        self.forms = [] # type: list[CustomFormUI]
        self.currentLayer = 0
        self.column = params['column'] or [1]
        self.row = params['row'] or [1]

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#custom_ui_close')
    def Close(self, args):
        clientApi.PopScreen()

    def Create(self):
        pass

    def Update(self):
        for form in self.forms:
            form.Update()

    @property
    def isMoreUI(self):
        return True
    
    def updateGrid(self, fm):
        form = self.GetBaseUIControl(fm.basePath)
        screenSize = self.GetBaseUIControl("/screen").GetSize()
        posX = 0
        for i in range(0, fm.grid_pos[0]):
            posX += self.column[i]
        posY = 0
        for i in range(0, fm.grid_pos[1]):
            posY += self.row[i]
        sizeX = 0
        for i in range(0, fm.grid_size[0]):
            sizeX += self.column[i + fm.grid_pos[0]]
        sizeY = 0
        for i in range(0, fm.grid_size[1]):
            sizeY += self.row[i + fm.grid_pos[1]]
        gridX = 0
        for c in self.column:
            gridX += c
        if not gridX:
            gridX = 1
        gridY = 0
        for c in self.row:
            gridY += c
        if not gridY:
            gridY = 1
        form.SetPosition((
            screenSize[0] * posX / gridX + fm.grid_offset[0] + fm.grid_margin[3], 
            screenSize[1] * posY / gridY + fm.grid_offset[1] + fm.grid_margin[0]
            ))
        form.SetSize((
            screenSize[0] * sizeX / gridX - fm.grid_margin[1] - fm.grid_margin[3], 
            screenSize[1] * sizeY / gridY - fm.grid_margin[0] - fm.grid_margin[2]), 
            True)

    def combine(self, fm):
        # type: (CustomFormUI) -> None
        baseControl = ""
        if fm.formType == 'custom':
            baseControl = "server_forms.custom_form_panel"
        elif fm.formType == 'bar':
            baseControl = "server_forms.bar_form_panel"
        self.forms.append(fm)
        fm.sn = self
        index = random.randint(0, 32767)
        fm.basePath = "/screen/panel%s" % index
        form = self.CreateChildControl(baseControl, "panel%s" % index, self.GetBaseUIControl("/screen"))
        form.SetLayer(fm.options['layer'] * 50)
        self.currentLayer += 50
        self.updateGrid(fm)
        fm.Create()

    def update(self, data):
        for form in self.forms:
            form.update(data)
            self.updateGrid(form)

class SidebarFormUI(More):
    """
    A single-panel form with a vertical strip of square icon tabs on the left and a content
    area on the right. Each tab's CustomForm is rendered into the content area through the
    inherited ``More`` combine pipeline; switching tabs just shows/hides the matching form,
    driven from the server exactly like ConfigMenu's pages.
    """
    FRAME = "/screen/frame"

    def __init__(self, namespace, name, params):
        ScreenNode.__init__(self, namespace, name, params)
        self.forms = [] # type: list[CustomFormUI]
        self.formId = params['formId']
        self.tabs = params['tabs']           # icon texture paths, aligned with content forms
        self.tabFormIds = params['formIds']  # content form ids, aligned with tabs
        self.options = params['options']
        self.tabButtons = []

    @property
    def isMoreUI(self):
        return True

    @property
    def isSidebar(self):
        return True

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#custom_ui_close')
    def Close(self, args):
        clientApi.PopScreen()

    def Create(self):
        close_btn = self.GetBaseUIControl(self.FRAME + "/close")
        if close_btn:
            close_btn = close_btn.asButton()
            close_btn.AddTouchEventParams({"isSwallow": True})
            close_btn.SetButtonTouchUpCallback(self.onClose)
            close_btn.SetVisible(self.options.get("closable", True))
        # Build the square icon tab strip from the top-left down.
        strip = self.GetBaseUIControl(self.FRAME + "/sidebar")
        for i in range(len(self.tabs)):
            btn = self.CreateChildControl("oreui_controls.sidebar_tab_btn", "tab%s" % i, strip).asButton()
            btn.AddTouchEventParams({"isSwallow": True, "selection": i})
            btn.SetButtonTouchUpCallback(self.onTabClick)
            btn.SetPosition((4, 4 + i * 40))
            icon = btn.GetChildByPath("/icon")
            if icon and self.tabs[i]:
                icon.asImage().SetSprite(self.tabs[i])
            self.tabButtons.append(btn)
        self.setSelected(0)

    def onClose(self, data):
        clientApi.PopScreen()

    def onTabClick(self, data):
        sel = data['AddTouchEventParams']['selection']
        self.setSelected(sel)
        getSystem().NotifyToServer("updateSidebarForm%s" % self.formId, {"selection": sel})

    def setSelected(self, index):
        i = 0
        for btn in self.tabButtons:
            mark = btn.GetChildByPath("/selected")
            if mark:
                mark.SetVisible(i == index)
            i += 1

    def combine(self, fm):
        # type: (CustomFormUI) -> None
        baseControl = "server_forms.custom_form_panel"
        if fm.formType == 'bar':
            baseControl = "server_forms.bar_form_panel"
        self.forms.append(fm)
        fm.sn = self
        index = random.randint(0, 32767)
        fm.basePath = self.FRAME + "/content/panel%s" % index
        self.CreateChildControl(baseControl, "panel%s" % index, self.GetBaseUIControl(self.FRAME + "/content"))
        fm.Create()
        # Tab content is chrome-less: the sidebar frame owns the window decorations.
        if fm.move_btn:
            fm.move_btn.SetVisible(False)
        if fm.resize_btn:
            fm.resize_btn.SetVisible(False)
        if fm.close_btn:
            fm.close_btn.SetVisible(False)
        # Fill the content area.
        content = self.GetBaseUIControl(self.FRAME + "/content")
        panel = self.GetBaseUIControl(fm.basePath)
        if content and panel:
            size = content.GetSize()
            panel.SetLayer(2)
            panel.SetPosition((-2, -2))
            # The body's visible fill is inset 2px from the panel (border_linear 100%+2px /
            # bg 100%-2px), so grow the panel by 2px to make the form fill the content area.
            panel.SetSize((size[0] + 4, size[1] + 4), True)
        # Combine is deferred, so the server cannot reliably hide forms before they exist:
        # only the active tab (the first by default) starts visible; the rest are hidden
        # until their tab is clicked.
        active = self.tabFormIds[0] if self.tabFormIds else None
        if panel:
            panel.SetVisible(fm.formId == active)

    def update(self, data):
        for form in self.forms:
            form.update(data)
