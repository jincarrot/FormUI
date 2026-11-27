# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi

from .attack_form import create_attack_form


ClientSystem = clientApi.GetClientSystemCls()


class AttackFormClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.form = None
        self.target = None
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.onUiReady)

    def onUiReady(self, args):
        if self.form is not None:
            return
        self.form, self.target = create_attack_form()
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'PlayerAttackEntityEvent', self, self.onAttack)

    def onAttack(self, args):
        victimId = args.get('victimId')
        if not victimId or victimId == '-1' or args.get('playerId') != clientApi.GetLocalPlayerId():
            return
        self.target.setValue(victimId)
        if not self.form.isShowing():
            self.form.show()
