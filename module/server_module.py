# from zmq.asyncio import Context
import subprocess, re,time, pickle,zmq


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


class server_Agent(base_Agent):
    def __init__(self, port, binding_ip=None):
        base_Agent.__init__(self, binding_ip, port)
        if (binding_ip == '') or binding_ip is None:
            self.ip = '*'

    def __del__(self):
        self.close()

    def close(self):
        if self.sock:
            self.sock.close()
        self.poller = None

    def reconnect(self):
        self.close()
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.PUB)
        try:
            self.sock.bind(f'tcp://{self.ip}:{self.port}')
        except:
            port_kill(self.port)
            self.sock.bind(f'tcp://{self.ip}:{self.port}')

    def run_server(self, times=0.5, flag=0):
        self.reconnect()
        i = 0
        while True:
            self.send_pickle(self.sock, [i, time.time()], flag)
            # print(f"{i}th data published flag {flag}")
            time.sleep(times)
            i += 1


