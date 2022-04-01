import subprocess, re,time,traceback,pickle,zmq,sys
from sig_generator import ind_stock,Base_AM
from tele_bot import Tel_Bot
import heapq
import threading

def async_(target, args=(), kwargs={}):
    thread=threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

def port_kill(port):
    find_result = subprocess.run(f"netstat -ano | findstr {port}", shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    target_process = set(
        [re.split("\s+", i)[-1] for i in find_result.stdout.split("\n") if len(re.split("\s+", i)) > 1])

    for tp in target_process:
        kill_process = subprocess.run(f"taskkill /f /pid {tp}", shell=True, stdout=subprocess.PIPE, encoding='utf-8')
        print("return code :  %s" % (kill_process.returncode))
        print(kill_process.stdout)
        print(kill_process.stderr)


class base_Agent(object):
    def __init__(self, binding_ip, port):
        self.ip = binding_ip
        self.port = port
        self.poller = None
        self.sock = None

    def send_pickle(self, socket, obj, flags=0):
        """
        pickle an object >> zip >> sending
        """
        p = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return socket.send(p, flags=flags)

    def recv_pickle(self, socket, flags=0):
        p = socket.recv(flags)
        return pickle.loads(p)
class Agent(base_Agent):
    def __init__(self, binding_ip, port,teleport,token,channel_id):
        base_Agent.__init__(self, binding_ip, port)
        self.sock_sub = None
        self.tele_bot = Tel_Bot(token=token,channel_id=channel_id,port=teleport)
        self.tele_bot.run()
        self.teleport = teleport
        self.market_timing = 0
        self.target_rank = []
        async_(self.impact_ranking)
    def __del__(self):
        self.close()

    def close(self):
        if self.sock:
            self.sock.close()
        if self.sock_sub:
            self.sock_sub.close()
        self.poller = None

    def reconnect(self):
        self.close()
        ctx = zmq.Context.instance()
        self.sock = ctx.socket(zmq.REQ)
        try:
            self.sock.connect(f'tcp://localhost:{self.teleport}')
        except:
            port_kill(self.port)
            self.sock.connect(f'tcp://localhost:{self.teleport}')
        self.sock_sub = ctx.socket(zmq.SUB)
        try:
            self.sock_sub.connect(f'tcp://{self.ip}:{self.port}')
        except:
            port_kill(self.port)
            self.sock_sub.connect(f'tcp://{self.ip}:{self.port}')
        self.sock_sub.setsockopt(zmq.SUBSCRIBE, str("").encode())
        self.sock_sub.setsockopt(zmq.RCVTIMEO, 1000)
        self.poller = zmq.Poller()
        self.poller.register(self.sock,zmq.POLLIN)
        self.poller.register(self.sock_sub, zmq.POLLIN)



    def impact_ranking(self):
        print("impact_ranking start!!")
        if hasattr(self,'AM') and len(self.AM.Sig_Target)>100:
            dat = sorted(self.AM.Sig_Target.items(),key= lambda x: x[1].balance_impact_adj)
            self.send_pickle(self.sock,dat[:10])
        threading.Timer(60,self.impact_ranking).start()

    def run_client(self,flag=0):
        self.reconnect()
        while True:
            socks = dict(self.poller.poll())
            if socks.get(self.sock_sub, None) == zmq.POLLIN:
                try:
                    data = self.recv_pickle(self.sock_sub, flag)
                    if data[0] == 'init':
                        self.stock_item = data[1]
                        self.AM = Base_AM(self.stock_item)
                    elif (data[0] == '주식시간외호가'):
                        if data[1] in self.stock_item:
                            if not (data[1] in self.AM.Sig_Target):
                                stock_num = int(self.stock_item[data[1]]['상장주식수'])
                                price_d1 = float(self.stock_item[data[1]]['전일가'])
                                self.AM.Sig_Target[data[1]] = ind_stock(price_d1, stock_num)
                            try:
                                self.AM.Sig_Target[data[1]].ask_total_remain = int(data[-1]['시간외매도호가총잔량'])
                                self.AM.Sig_Target[data[1]].bid_total_remain = int(data[-1]['시간외매수호가총잔량'])
                                self.AM.Sig_Target[data[1]].ask_cancel_total += abs(data[-1]['시간외매도호가총잔량직전대비']) if data[-1]['시간외매도호가총잔량직전대비'] <0  else 0
                                self.AM.Sig_Target[data[1]].bid_cancel_total += abs(data[-1]['시간외매수호가총잔량직전대비']) if data[-1]['시간외매수호가총잔량직전대비'] <0  else 0
                            except:
                                pass
                    elif (data[0] == '주식체결')  and False:
                        if data[1] in self.stock_item:
                            if not (data[1] in self.AM.Sig_Target):
                                price_d1 = abs(int(data[-1]['현재가'])) - int(data[-1]['전일대비'])
                                stock_num =int(abs(int(data[-1]['시가총액']))*1e8//abs(int(data[-1]['현재가'])))
                                self.AM.Sig_Target[data[1]] = ind_stock(price_d1, stock_num)
                            if not int(data[-1]['최우선매도호가']) and not int(data[-1]['최우선매수호가']):
                                self.AM.Sig_Target[data[1]].ask_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].ask_traded_volume += abs(data[-1]['거래량'])//2
                                self.AM.Sig_Target[data[1]].bid_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].bid_traded_volume += abs(data[-1]['거래량'])//2
                            elif not int(data[-1]['최우선매도호가']):
                                self.AM.Sig_Target[data[1]].ask_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].ask_traded_volume += abs(data[-1]['거래량'])
                            elif not int(data[-1]['최우선매수호가']):
                                self.AM.Sig_Target[data[1]].bid_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].bid_traded_volume += abs(data[-1]['거래량'])
                            if int(data[-1]['현재가']) == int(data[-1]['최우선매도호가']):
                                self.AM.Sig_Target[data[1]].ask_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].v_ask_price = (self.AM.Sig_Target[data[1]].ask_traded_volume*self.AM.Sig_Target[data[1]].v_ask_price + \
                                                                            abs(data[-1]['거래량'])*data[-1]['현재가']) \
                                                                           /(self.AM.Sig_Target[data[1]].ask_traded_volume + abs(data[-1]['거래량']))
                                self.AM.Sig_Target[data[1]].ask_traded_volume += abs(data[-1]['거래량'])
                            elif int(data[-1]['현재가']) == int(data[-1]['최우선매수호가']):
                                self.AM.Sig_Target[data[1]].bid_price = data[-1]['현재가']
                                self.AM.Sig_Target[data[1]].v_bid_price = (self.AM.Sig_Target[data[1]].bid_traded_volume * \
                                self.AM.Sig_Target[data[1]].bid_traded_volume)/self.AM.Sig_Target[data[1]].total_a
                                self.AM.Sig_Target[data[1]].bid_traded_volume += abs(data[-1]['거래량'])
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:
                        pass  # no message was ready (yet!)
                    else:
                        print(traceback.print_exc())

            if socks.get(self.sock, None) == zmq.POLLIN:
                rep =  self.recv_pickle(self.sock,flag)
                print(rep)
