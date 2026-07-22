# -*- coding: utf-8 -*-

def isFormScreen(screen):
    return hasattr(screen, "isFormScreen")

def getSizeDict(info):
    # type: (str | int) -> dict
    if isinstance(info, int):
        return {"absoluteValue": info, "relativeValue": 0.0, "followType": "parent"}
    elif isinstance(info, str):
        absoluteValue = 0.0
        relativeValue = 0.0
        if info == "fill":
            relativeValue = 1.0
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