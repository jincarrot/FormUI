# -*- coding: utf-8 -*-
from FormData import CustomForm, MoreUI, Observable
import mod.server.extraServerApi as serverApi

class ConfigMenu:

    def __init__(self, playerId, title):
        self.__whitePageLayer = Observable.create(1)
        self.__titleBarLayer = Observable.create(2)
        self.__ui = MoreUI.create(playerId, {"column": [1, 4], "row": [1, 1, 16]})
        self.__sidebar = self.__ui.addBarForm("", {}, {"position": [0, 1], "size": [1, 2]})
        self.__whitePage = self.__ui.addCustomForm("", {"closable": False}, {"position": [1, 1], "size": [1, 2], "layer": self.__whitePageLayer})
        self.__titleBar = self.__ui.addBarForm(title, {"closable": True}, {"position": [0, 0], "size": [2, 2], "layer": self.__titleBarLayer})
        self.__titleBar.mayCloseAll.setData(True)
        self.__currentPage = self.__whitePage.form
        self.__pages = [self.__whitePage.form]

    @staticmethod
    def create(playerId, title):
        return ConfigMenu(playerId, title)
    
    def addPage(self, form, tabName=None):
        # type: (CustomForm, str) -> None
        fmd = self.__ui.addForm(form, {"position": [1, 1], "size": [1, 2]})
        self.__pages.append(form)
        self.__whitePageLayer.setData(fmd.layout.layer + 1)
        self.__titleBarLayer.setData(fmd.layout.layer + 2)
        if not tabName:
            tabName = form._title
        def onClick():
            for fm in self.__pages:
                fm.close()
            form.show()
            self.__currentPage = form
        self.__sidebar.form.button(tabName, onClick)

    def show(self):
        self.__ui.show()

    def close(self):
        self.__ui.close()
    
    