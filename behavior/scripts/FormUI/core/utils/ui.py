# -*- coding: utf-8 -*-

import math


def isFormScreen(screen):
    return hasattr(screen, "isFormScreen")

def getScrollingContent(control):
    target = control.GetChildByPath("/scroll_mouse/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content")
    if not target:
        target = control.GetChildByPath("/scroll_touch/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content")
    return target

def getSizeDict(info):
    # type: (str | int) -> dict
    if isinstance(info, (int, float)):
        return {"absoluteValue": info, "relativeValue": 0.0, "followType": "parent"}
    elif isinstance(info, str):
        absoluteValue = 0.0
        relativeValue = 0.0
        if info == "fill":
            relativeValue = 1.0
        elif info == 'default':
            return None
        else:
            tempNum = ""
            sgn = 1
            info = info.replace(" ", "")
            for char in info:
                if char.isdigit():
                    tempNum += char
                else:
                    if char == "%":
                        relativeValue += (float(tempNum) / 100.0) * sgn
                        tempNum = ""
                    elif char == "p":
                        absoluteValue += float(tempNum) * sgn
                        tempNum = ""
                    elif char == "+":
                        sgn = 1
                    elif char == "-":
                        sgn = -1
                    elif char == "x":
                        pass
                    else:
                        raise Exception("Invalid value!")
        return {"absoluteValue": absoluteValue, "relativeValue": relativeValue, "followType": "parent"}
    else:
        raise Exception("Invalid value!")

def getStepedValue(v, minV, maxV, step):
    maxBorder = math.floor((maxV - minV) / step) * step + minV
    v = max(minV, min(v, maxBorder))
    v = minV + round((v - minV) / step) * step
    return v

def getSliderPercentage(v, minV, maxV, step):
    if step != 0:
        v = getStepedValue(v, minV, maxV, step)
    return ((v - minV) / (maxV - minV)) if maxV != minV else 0.0

def getSliderValue(percentage, minV, maxV, step):
    v = percentage * (maxV - minV) + minV
    if step != 0:
        v = getStepedValue(v, minV, maxV, step)
    return v