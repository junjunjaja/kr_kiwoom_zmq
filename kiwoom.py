from PyQt5.QAxContainer import QAxWidget
from tracker_logger import logger
REQUEST_LIMIT = 10

logger.debug("=============================================================================")
logger.info("LOG START")

class Kiwoom(object):
    def __init__(self,logger,debug):
        self.KiwoomAPI()
        self.KiwoomConnect()
        self.ScreenNumber = 5000
        self.graphScreenNumber = 9901
        self.KiwoomLogin()
        self.request_limit = 0
        self.debug = debug
    def KiwoomAPI(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")


    def KiwoomConnect(self):
        self.kiwoom.OnEventConnect[int].connect(self.OnEventConnect)
        self.kiwoom.OnReceiveMsg[str, str, str, str].connect(self.OnReceiveMsg)
        self.kiwoom.OnReceiveTrCondition[str, str, str, int, int].connect(self.OnReceiveTrCondition)
        self.kiwoom.OnReceiveTrData[str, str, str, str, str, int, str, str, str].connect(self.OnReceiveTrData)
        self.kiwoom.OnReceiveChejanData[str, int, str].connect(self.OnReceiveChejanData)
        self.kiwoom.OnReceiveConditionVer[int, str].connect(self.OnReceiveConditionVer)
        self.kiwoom.OnReceiveRealCondition[str, str, str, str].connect(self.OnReceiveRealCondition)
        self.kiwoom.OnReceiveRealData[str, str, str].connect(self.OnReceiveRealData)

    def KiwoomDisConnect(self):
        self.kiwoom.OnEventConnect[int].disconnect(self.OnEventConnect)
        self.kiwoom.OnReceiveMsg[str, str, str, str].disconnect(self.OnReceiveMsg)
        self.kiwoom.OnReceiveTrCondition[str, str, str, int, int].disconnect(self.OnReceiveTrCondition)
        self.kiwoom.OnReceiveTrData[str, str, str, str, str, int, str, str, str].disconnect(self.OnReceiveTrData)
        self.kiwoom.OnReceiveChejanData[str, int, str].disconnect(self.OnReceiveChejanData)
        self.kiwoom.OnReceiveConditionVer[int, str].disconnect(self.OnReceiveConditionVer)
        self.kiwoom.OnReceiveRealCondition[str, str, str, str].disconnect(self.OnReceiveRealCondition)
        self.kiwoom.OnReceiveRealData[str, str, str].disconnect(self.OnReceiveRealData)

    def KiwoomLogin(self):
        self.kiwoom.dynamicCall("CommConnect()")
        self._login = True

    def KiwoomLogout(self):
        if self.kiwoom is not None:
            self.kiwoom.dynamicCall("CommTerminate()")

        #self.statusbar.showMessage("해제됨...")

    def KiwoomAccount(self):
        ACCOUNT_CNT = self.kiwoom.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        ACC_NO = self.kiwoom.dynamicCall('GetLoginInfo("ACCNO")')
        self.account = ACC_NO.split(';')[0:-1]

        return (ACCOUNT_CNT, ACC_NO)

    def KiwoomSendOrder(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        if self.request_limit < REQUEST_LIMIT:
            Order = self.kiwoom.dynamicCall('SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                                        [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo])
            self.request_limit += 1
            return (True, Order)
        else:
            return (False, -1)

    def KiwoomSetRealReg(self, sScreenNo, sCode, sRealType='0'):
        ret = self.kiwoom.dynamicCall('SetRealReg(QString, QString, QString, QString)', sScreenNo, sCode, '9001;10', sRealType)
        return ret

    def KiwoomSetRealRemove(self, sScreenNo, sCode):
        ret = self.kiwoom.dynamicCall('SetRealRemove(QString, QString)', sScreenNo, sCode)
        return ret

    def KiwoomScreenNumber(self):
        self.screen_number += 1
        if self.screen_number > 8999:
            self.screen_number = 5000
        return self.screen_number

    def OnEventConnect(self, nErrCode):
        if nErrCode == 0:
            self.kiwoom.dynamicCall("KOA_Functions(QString, QString)", ["ShowAccountWindow", ""])
        else:
            self.statusbar.showMessage("연결실패... %s" % nErrCode)

    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        if self.debug:
            logger.debug('main:OnReceiveMsg [%s] [%s] [%s] [%s]' % (sScrNo, sRQName, sTrCode, sMsg))

    def OnReceiveTrCondition(self, sScrNo, strCodeList, strConditionName, nIndex, nNext):
        if self.debug:
            logger.debug('main:OnReceiveTrCondition [%s] [%s] [%s] [%s] [%s]' % (sScrNo, strCodeList, strConditionName, nIndex, nNext))


    def OnReceiveTrData(self, sScrNo, sRQName, sTRCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSPlmMsg):
        if self.debug:
            logger.debug('main:OnReceiveTrData [%s] [%s] [%s] [%s] [%s] [%s] [%s] [%s] [%s] ' % (sScrNo, sRQName, sTRCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSPlmMsg))
        if self.ScreenNumber != int(sScrNo):
            return
        if sRQName == "계좌정보요청":
            cnt = self.kiwoom.dynamicCall('GetRepeatCnt(QString, QString)', sTRCode, sRQName)
            S = self.kiwoom.dynamicCall('CommGetData(QString, QString, QString, int, QString)', sTRCode, "", sRQName, i,j).strip().lstrip('0')

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFidList):
        if self.debug:
            logger.debug('main:OnReceiveChejanData [%s] [%s] [%s]' % (sGubun, nItemCnt, sFidList))
        pass

    def OnReceiveConditionVer(self, lRet, sMsg):
        if self.debug:
            logger.debug('main:OnReceiveConditionVer : [이벤트] 조건식 저장', lRet, sMsg)

    def OnReceiveRealCondition(self, sTrCode, strType, strConditionName, strConditionIndex):
        if self.debug:
            logger.debug('main:OnReceiveRealCondition [%s] [%s] [%s] [%s]' % (sTrCode, strType, strConditionName, strConditionIndex))

    def OnReceiveRealData(self, sRealKey, sRealType, sRealData):
        if self.debug:
            logger.debug('main:OnReceiveRealData [%s] [%s] [%s]' % (
            sRealKey, sRealType, sRealData))
    def set_input_value(self, id, value):  # TR 요청을 위한 input을 관리하는 함수
        if self.debug:
            logger.debug("SetInputValue([%s], [%s])" % (id, value))
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):  # TR 요청을 위한 리퀘스트 함수
        if self.debug:
            logger.debug("CommRqData([%s], [%s],[%s],[%s])" % (rqname, trcode, next, screen_no))
        ret = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        return ret

    def _set_real_reg(self, screen_no, code_list, fid_list, real_type):  # 종목 실시간 데이터 등록
        if self.debug:
            logger.debug("SetRealReg([%s], [%s], [%s], [%s])" % (screen_no, code_list, fid_list,real_type))
        ret = self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, code_list, fid_list,real_type)
        return ret

    # 해제
    def _set_real_remove(self, screen_no, code_list):  # 종목 실시간 데이터 등록 해제
        if self.debug:
            logger.debug("SetRealRemove([%s], [%s])" % (screen_no, code_list))
        ret = self.kiwoom.dynamicCall("SetRealRemove(Qstring, Qstring))", screen_no, code_list)
        return ret

if __name__ =="__main__":
