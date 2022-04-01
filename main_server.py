#from kiwoom import Kiwoom_server,logger
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from module.Kiwoom import KiwoomAPI
from collections import defaultdict
from module.win32control import *
from datetime import datetime
from PyQt5 import QtCore
import threading
from configparser import ConfigParser
from tracker_logger import get_logger
from module.server_module import server_Agent
from module.keyboard_agent import recordAgent
import zmq
private_config = ConfigParser()
private_config.read('Private.cfg')

base_config = ConfigParser()
base_config.read('Base_setting.cfg')


def debug_mode(func):
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if args[0]._debug:
            args[0].logger.debug(f"Call {func.__name__} : ret {ret}")
        return ret
    return wrapper

def async_(target, args=(), kwargs={}):
    thread=threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread


class Window_component(object):
    def __init__(self,debug):
        kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kwos = KiwoomAPI(kiwoom)
        self.logger = get_logger()
        self._debug = debug
        self._login_param = 0
        self._ip = base_config['SOCKET']['Producer_Addr']
        self._port = base_config['SOCKET']['Port']
        self._server = server_Agent(self._port,self._ip)
        self._server.reconnect()
        self.keyboardAgent = recordAgent(self)
        async_(target=self.keyboardAgent.run)
        self.LogIn()
        #self.sock = SocketQueuePoller(int(base_config['SOCKET']['Port']))
        self._start_data = False
    # Kiwoom Login process
    def LogIn(self):
        if self._login_param ==0:
            self._login_param = 1
            self.kwos.login()
            timer = threading.Timer(1, self.PassWordInput, args=(
            private_config['LOGIN']['account_pw1'], private_config['LOGIN']['account_pw2'],
            private_config['LOGIN']['account_pw3']))
            timer.start()
        else:
            return
    def LogOut(self):
        self.kwos.KiwoomLogout()
    def PassWordInput(self,password1,password2,password3):
        while True:
            list_windows = getWindowList()
            open_win = [w[1] for w in list_windows if w[0] == 'Open API Login']
            if len(open_win):
                time.sleep(0.1)
                all_child = dumpSpecifiedWindow(open_win[0])
                # 0 : 고객ID 1:pw1, 2:pw2 , 3:login
                try:
                    enter_keys(all_child[1][0], password1)
                    enter_keys(all_child[2][0], password2)
                    click_button(all_child[3][0])
                except:
                    pass
                break
        count = 0
        while count < 100:
            count +=1
            list_windows = getWindowList()
            open_win = [w[1] for w in list_windows if '스마트카드/스마트키 비밀번호(PIN) 입력' in w[0]]
            if len(open_win):
                break
            else:
                time.sleep(3)
        if len(open_win):
            all_child = dumpSpecifiedWindow(open_win[0])
            all_child = all_child[all_child.index([i for i in all_child if '저장매체 비밀번호:' in i[1]][-1]):]
            enter_keys(all_child[1][0], password3)
            click_button(all_child[2][0])
        self._login_param = 0

    # On loop method
    def OnClockTick(self):
        current = datetime.now().strftime('%H:%M:%S')
        if '03:00:00' <= current <='04:00:00' and self.kwos.getLoginState():
            self.LogOut()

        if current >= '07:00:00' and not self.kwos.getLoginState():
            self.LogIn()

        if current == '00:00:00':
            self.logger = get_logger()

        if current >= '08:00:00' and not self._start_data and hasattr(self.kwos,'stock_item'):
            self._start_data = True
            self._server.send_pickle(self._server.sock, ['init',self.kwos.stock_item], flags=0)
            self.kwos.addOnReceiveReal(self.ToLinuxReal)
            self.kwos.addOnReceiveRealExt(self.ToLinuxRealExt)
            if self._debug:
                self.debug_send()
            else:
                self.kwos.addRealData(sorted(self.kwos.stock_item.keys()))

        if current >= '18:00:00' and hasattr(self.kwos,'stock_item'):
            self.kwos.removeRealData(self.kwos.stock_item.keys()) #real data screen quit
            self.LogOut()

    @debug_mode
    def ToLinuxReal(self,sCode, sRealType,realData):
        self.logger.info(f"{sRealType} : {sCode} {realData}")
        self._server.send_pickle(self._server.sock, [sRealType,sCode,realData], flags=0)
    @debug_mode
    def ToLinuxRealExt(self,sCode,sRealType, realData):
        self.logger.info(f"{sRealType} : {sCode} {realData}")
        self._server.send_pickle(self._server.sock, [sRealType, sCode, realData], flags=0)

    def debug_send(self):
        self._server.send_pickle(self._server.sock, ['init', self.kwos.stock_item], flags=0)
        fd = open("LOG/20220401_trunc.txt",'r')
        """
        f = open("LOG/20220401_trunc.txt", 'w')
        
            line = fd.readline()
            if not line:
                break
            if "DEBUG" not in line:
                f.write(line)
        f.close()
        """
        while True:
            d = line = fd.readline()
            if not line:
                break
            if '주식시간외호가' in d:
                sRealType = '주식시간외호가'
                id1 = d.find(sRealType)
                d = d[id1 + len('주식시간외호가') + 3:-1]
                realData = eval(d[d.find('{'):])
                sCode = d[:d.find('{')].strip()
                self._server.send_pickle(self._server.sock, [sRealType, sCode, realData], flags=1)
                print([sRealType, sCode, realData])

            if '주식체결 :' in d and 'ECN주식체결' not in d:
                sRealType = '주식체결'
                id1 = d.find('주식체결 : ')
                d = d[id1 + len('주식체결 : '):]
                realData = eval(d[d.find('{'):])
                sCode = d[:d.find('{')].strip()
                self._server.send_pickle(self._server.sock, [sRealType, sCode, realData], flags=0)


if __name__ == "__main__":
    app = QApplication([])
    window = Window_component(True)
    clock = QtCore.QTimer()
    clock.timeout.connect(window.OnClockTick)
    clock.start(1000)
    app.exec_()

