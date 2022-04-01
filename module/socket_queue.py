import socket,threading,multiprocessing
from queue import Queue
import time,select,collections
import lz4.frame as lz
import _pickle as pickle

sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_msg(sock):
    while True:
        data = sys.stdin.readline()
        sock.sendto(data, target)

def recv_msg(sock):
    while True:
        data, addr = sock.recvfrom(1024)
        sys.stdout.write(data)

Thread(target=send_msg, args=(sock_send,)).start()
Thread(target=recv_msg, args=(sockfd,)).start()

class SerializationError(Exception):
    pass

LZ_HEADER_BYTES = 10

def lz_segmented_compress(buf):
    stride = 2 **30
    bufs = []
    offset = 0
    while offset < len(buf):
        segment = buf[offset : offset + stride]
        segment = lz.compress(segment,compression_level=0)
        header = str(len(segment))
        header = "0" * (LZ_HEADER_BYTES - len(header)) + header
        bufs.append(header)
        bufs.append(segment)

        offset += stride
    return "".join(bufs)

def lz_segmented_decompress(buf):
    bufs = []
    offset = 0
    while offset < len(buf):
        header = buf[offset : offset + LZ_HEADER_BYTES]
        stride = int(header)
        offset += LZ_HEADER_BYTES
        segment = lz.decompress(buf[offset : offset + stride])
        bufs.append(segment)
        offset += stride
    return "".join(bufs)

def serialize(obj,compress = True):
    """
    Compress above a has little benefits.
    """
    buf = pickle.dumps(obj,protocol = 2)
    if compress and len(buf) > 1000:
        buf = '1' + lz_segmented_compress(buf)
    else:
        buf = '0' + buf

    return buf

def deserialize(buf):
    if not buf:
        raise SerializationError('Empty buffer')

    code = buf[0]
    buf = buf[1 : ]

    if code == '0':
        return pickle.loads(buf)

    elif code == '1':
        buf=lz_segmented_decompress(buf)
        return pickle.loads(buf)

    else:
        raise SerializationError('Invalid serialization code: %s' % code)

def async_(target, args=(), kwargs={}):
    thread=threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

class NoConnectionError(Exception):
    pass

class Timeout(Exception):
    pass



class SocketQueuePoller:
    """
    Polls for read requests from connecting queue.
    """
    def __init__(self,port):
        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.settimeout(0.)
        server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(('',port))
        server.listen(1000)
        self.sever = server
        self.fd_to_socket = {server.fileno():server}
        self.fd_to_queue = {}
        select.select()
        self.poller = select.poll()
        self.poller.register(server.fileno(),select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)
        self.queus = collections.deque()

    def poll(self,timeout = None):
        """
        :param timeout: in SECOND
        :return:
        """
        if self.queus:
            return self.queus.popleft()
        if timeout is not None:
            timeout = 1000
        events = self.poller.poll(timeout)

        for fd,flag in events:
            sock = self.fd_to_socket[fd]
            if flag & (select.POLLIN | select.POLLPRI):
                if sock is self.sever:
                    client_socket,_ = sock.accept()
                    queue = SocketQueue(client_socket)

                    self.fd_to_socket[client_socket.fileno()] = client_socket
                    self.fd_to_queue[client_socket.fileno()] = queue
                    self.poller.register(client_socket.fileno(),select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)
                else:
                    queue = self.fd_to_queue[fd]
                    if queue.is_alive():
                        self.queus.append(queue)
                    else:
                        queue.close()
                        self.poller.unregister(fd)
                        del self.fd_to_socket[fd]
                        del self.fd_to_queue[fd]
            elif flag & (select.POLLERR | select.POLLHUP):
                if sock is self.sever:
                    raise NoConnectionError('Poller : server socket closed unexpectedly')
                else:
                    self.poller.unregister(fd)
                    del self.fd_to_socket[fd]
                    del self.fd_to_queue[fd]
            else:
                raise ValueError('Poller : unexpected flag : %s' % flag)
        if self.queus:
            return self.queus.popleft()
        return None

    def close(self):
        for _,sock in self.fd_to_socket.items():
            sock.close()
        for _,queue in self.fd_to_queue.items():
            queue.close()
        self.poller = None

    def __del__(self):
        self.close()
class SocketQueue:
    """
    Single- consumer, single-producer socket queue.
    Important, THis must not be blocking, Declare timeout whenever put()/get().
    """
    #Todo : Opposite side crash cannont be handled - need some timeout

    def __init__(self,sock):
        self.sock = sock
        self.sock.settimout(0)
        self.sock.setsockopt(sock.IPROTO_TCP,socket.TCP_NODELAY,1)
        self.closed = False
        self.header_buf = ''
        self.body_bufs = []

        self.peername = self.sock.getpeername()
        self.sockname = self.sock.getsockname()

    @staticmethod
    def make(host,port):
        if host == socket.gethostname():
            host = 'localhost'
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            sock.connect((host,port))
        except socket.error as e:
            raise NoConnectionError(f'connect() failed {e.args}')
        return SocketQueue(sock)

    def getpeername(self):
        return self.peername
    def getsockname(self):
        return self.sockname
    def reconnect(self):
        self.close()
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.sock.connect(self.getpeername())
        except socket.error:
            self.sock.close()
            raise NoConnectionError(f'cannot reconnect: {self.getpeername}')
        self.sock.settimeout(0)
        self.sockname = self.sock.getsockname()
        self.closed = False

    def is_alive(self):
        if self.closed:
            return False
        self.sock.settimeout(1e-8)

        try:
            buf = self.sock.recv(1)
            self.sock.settimeout(0.)
        except socket.timeout:
            self.sock.settimeout(0.)
            return True
        except socket.error:
            self.close()
            return False

        if not buf:
            self.close()
            return False
        if len(self.header_buf) >= 30:
            self.body_bufs.append(buf)
        else:
            self.header_buf += buf
        return True
    def put(self,obj,reconnect = True):
        if not self.is_alive():
            if reconnect:
                self.reconnect()
            else:
                raise NoConnectionError(f'queue closed by peer {str(self.getpeername())}')
        # Todo : Need on extra logic to check if already serialized
        if not isinstance(obj,str):
            buf = serialize(obj)
        else:
            buf = obj
        bodylen = str(len(buf))
        header = '0' * (30 - len(bodylen))  + bodylen

        try:
            self.sock.settimeout(None)
            self.sock.sendall(header + buf)
            self.sock.settimeout(0.)
        except socket.error as e:
            self.close()
            raise NoConnectionError(f'put () failed at {e.args}')

    def get(self,timeout=None,reconnect = False):
        """
        get() is passive, so shouldn't reconnect by default.
        """
        if not self.is_alive():
            if reconnect:
                self.reconnect()
            else:
                raise NoConnectionError(f'queue closed by peer : {str(self.getpeername())}')
        self.sock.settimeout(timeout)

        while len(self.header_buf) <30:
            try:
                self.header_buf += self.sock.recv(30 - len(self.header_buf))
            except socket.timeout:
                self.sock.settimeout(0.)
                raise Timeout
            except socket.error:
                self.close()
                raise NoConnectionError(f'queue closed by peer : {str(self.getpeername)}')
            if not self.header_buf:
                self.close()
                raise NoConnectionError(f'queue closed by peer : {str(self.getpeername)}')
        bodylen = int(self.header_buf)
        n_bytes = sum(len(buf) for buf in self.body_bufs)

        while n_bytes < bodylen:
            try:
                bytes_recv = self.sock.recv(min(2**20,bodylen - n_bytes))
            except socket.timeout:
                self.sock.settimeout(0.)
                raise Timeout
            except socket.error:
                self.close()
                raise NoConnectionError(f'queue closed by peer : {str(self.getpeername)}')
            if not bytes_recv:
                self.close()
                raise NoConnectionError(f'queue closed by peer : {str(self.getpeername)}')
            self.body_bufs.append(bytes_recv)
            n_bytes += len(bytes_recv)
        message = ''.join(self.body_bufs)
        try:
            message = deseialize(message)
        except SerializationError:
            pass
        self.header_buf = ''
        self.body_bufs = []
        self.sock.settimeout(0.)
        return message

    def close(self):
        self.sock.close()
        self.closed = True
        self.header_buf = ''
        self.body_bufs = []

    def __del__(self):
        self.close()

class DuckQueue:
    """
    Mock queue for testing
    """
    def __init__(self):
        self.queue = Queue()
        self.last_put_ident = None
    def get(self,timeout=None):
        while True:
            obj = self.queue.get(timeout)
            if self.last_put_ident == threading.current_thread().ident:
                self.queue.put(obj)
            else:
                return obj
        time.sleep(0.5)

    def put(self,obj):
        self.queue.put(obj)
        self.last_put_ident = threading.current_thread().ident

    @staticmethod
    def is_alive():
        return True

    def close(self):
        pass
