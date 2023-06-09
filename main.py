import selectors
import threading
import concurrent.futures
from queue import Queue
import socket
import ssl
import vt

from send_handler import sender
from login_response_fetch_handler import fetch as login_fetch
from stream_request_fetch_handler import fetch as stream_fetch
from record_fetch_handler import record_fetch_handler
from search_fetch_handler import search_fetch
from socket_wrapper_iterator import RequestIterable
from profile_pic_fetch_handler import profile_pic_fetch
from upload_request_download_distributor import upload_request_download_distributor
from playlist_assembler import playlist_assembler
from downloader import downloader
from database_updater import database_updater
from request_validator import request_validator, validate_audio_filetype, validate_with_virustotal
from captcha_server import captcha_server
from captcha_solution_manager import CaptchaManager


STREAM = 'GET'
USER_REQ = b'UserProcessor'
RECORD_FETCH = 'Fetch'
SEARCH_FETCH = 'Search'
PROFILE_PIC_FECH = 'Gui/Get_Profile_Picture'
UPLOAD_REQ = b'Gui/Upload_Playlist/LEN '
CAPTCHA_REQ_PREFIX = b'Gui/Request_Captcha'

VT_API_KEY = "b26e17c04992b6609a83cdc2b97cd36f77e1eeff14d02f26eabde900d89d2bb4"

MAX_WORKERS = 20

SERVER = ('0.0.0.0', 9010)
KEYFILE = 'server.key'
CERTFILE = 'server.crt'

SUFFIX = b'@'


class ThreadSafeSocket:
    """
    Threadsafe wrapper for ssl.sslsocket.
    """
    def __init__(self, sock):
        self.sock = sock
        self.lock = threading.Lock()


    #override
    def recv(self, bufsize=1024, flags=0):
        self.lock.acquire()
        try:
            data = self.sock.recv(bufsize, flags)
        except ssl.SSLWantReadError as e:
            raise e
        finally:
            self.lock.release()
        return data

    #override
    def send(self, data, flags=0):
        self.lock.acquire()
        try:
            self.sock.send(data, flags)
        except ssl.SSLWantWriteError as e:
            raise e
        finally:
            self.lock.release()


class ThreadSafeDict(dict):
    """
    Threadsafe wrapper for python's built in dict type.
    """
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()


    def __getitem__(self, item):
        with self.lock:
            val = super().__getitem__(item)
        return val


    def __setitem__(self, key, value):
        with self.lock:
            super().__setitem__(key, value)


    def pop(self, key):
        with self.lock:
            super().pop(key)


def main():
    """
    Initializes all threads and functions as receiving thread. Blocks.
    :return: None
    """
    client_sel = selectors.DefaultSelector()
    ser_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ser_sock = ssl.wrap_socket(
        ser_sock,
        server_side=True,
        keyfile=KEYFILE,
        certfile=CERTFILE,
        ssl_version=ssl.PROTOCOL_TLSv1_2,
    )
    ser_sock.bind(SERVER)
    ser_sock.listen(100)
    stream_queue = Queue()
    stream_fetch_to_send_queue = Queue()
    user_req_queue = Queue()
    user_req_fetch_to_send_queue = Queue()
    captcha_manager = CaptchaManager()
    captcha_req_queue = Queue()
    captcha_send_queue = Queue()
    sock_to_uname_hash_map = ThreadSafeDict()
    stop = False
    #stream_fetcher_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    #for i in range(MAX_WORKERS):
    #    stream_fetcher_pool.submit(stream_fetch, stream_queue, stream_fetch_to_send_queue, stop)
    stream_fetcher_thread = threading.Thread(target=stream_fetch, args=(stream_queue, stream_fetch_to_send_queue, stop))
    stream_fetcher_thread.start()

    stream_senders = []
    for i in range(MAX_WORKERS):
        stream_sender_thread = threading.Thread(target=sender, args=(stream_fetch_to_send_queue, stop))
        stream_sender_thread.start()
        stream_senders.append(stream_sender_thread)

    profile_pic_fetch_queue = Queue()
    profile_pic_send_queue = Queue()
    profile_pic_fetch_threads = []
    for i in range(MAX_WORKERS):
        profile_pic_fetch_threads.append(threading.Thread(target=profile_pic_fetch, args=(profile_pic_fetch_queue,sock_to_uname_hash_map, profile_pic_send_queue)))
    for profile_pic_fetch_thread in profile_pic_fetch_threads:
        profile_pic_fetch_thread.start()
    pro_pic_send_threads = []
    for i in range(MAX_WORKERS):
        profile_pic_send_thread = threading.Thread(target=sender, args=(profile_pic_send_queue, stop, True))
        pro_pic_send_threads.append(profile_pic_send_thread)
        profile_pic_send_thread.start()

    user_proc_threads = []
    for i in range(MAX_WORKERS):
        user_proc_thread = threading.Thread(target=login_fetch, args=(user_req_queue, user_req_fetch_to_send_queue, stop, sock_to_uname_hash_map, captcha_manager))
        user_proc_thread.start()
        user_proc_threads.append(user_proc_thread)

    user_proc_senders = []
    for i in range(MAX_WORKERS):
        user_proc_sender_thread = threading.Thread(target=sender, args=(user_req_fetch_to_send_queue, stop, True))
        user_proc_sender_thread.start()
        user_proc_senders.append(user_proc_sender_thread)

    captcha_server_threads = []
    for i in range(MAX_WORKERS):
        captcha_server_thread = threading.Thread(target=captcha_server, args=(captcha_req_queue, captcha_send_queue, captcha_manager))
        captcha_server_thread.start()
        captcha_server_threads.append(captcha_server_thread)

    captcha_sender_threads = []
    for i in range(MAX_WORKERS):
        captcha_sender_thread = threading.Thread(target=sender, args=(captcha_send_queue, stop, True))
        captcha_sender_thread.start()
        captcha_sender_threads.append(captcha_sender_thread)

    search_fetch_queue = Queue()
    search_send_queue = Queue()
    record_fetch_queue = Queue()
    record_fetch_send_queue = Queue()

    search_fetch_threads = []
    for i in range(MAX_WORKERS):
        search_fetch_thread = threading.Thread(target=search_fetch, args=(search_fetch_queue, search_send_queue))
        search_fetch_thread.start()
        search_fetch_threads.append(search_fetch_thread)

    record_fetch_threads = []
    for i in range(MAX_WORKERS):
        record_fetch_thread = threading.Thread(target=record_fetch_handler, args=(record_fetch_queue, record_fetch_send_queue))
        record_fetch_thread.start()
        record_fetch_threads.append(record_fetch_thread)

    search_sender_threads = []
    for i in range(MAX_WORKERS):
        search_sender_thread = threading.Thread(target=sender, args=(search_send_queue, stop, True))
        search_sender_thread.start()
        search_sender_threads.append(search_sender_thread)

    record_sender_threads = []
    for i in range(MAX_WORKERS):
        record_sender_thread = threading.Thread(target=sender, args=(record_fetch_send_queue, stop, True))
        record_sender_thread.start()
        record_sender_threads.append(record_sender_thread)

    upload_queue = Queue()
    playlist_assembler_queue = Queue()
    offline_test_queue = Queue()
    online_test_queue = Queue()
    online_test_client = [vt.Client(VT_API_KEY, timeout=1800) for i in range(20)]
    download_queue = Queue()
    db_update_queue = Queue()
    upload_success_send_queue = Queue()

    record_download_dist_threads = []
    for i in range(MAX_WORKERS):
        record_download_dist_thread = threading.Thread(target=upload_request_download_distributor, args=(upload_queue, playlist_assembler_queue))
        record_download_dist_thread.start()
        record_download_dist_threads.append(record_download_dist_thread)

    playlist_assembly_threads = []
    for i in range(MAX_WORKERS):
        playlist_assembly_thread = threading.Thread(target=playlist_assembler, args=(playlist_assembler_queue, offline_test_queue, download_queue, upload_success_send_queue))
        playlist_assembly_thread.start()
        playlist_assembly_threads.append(playlist_assembly_thread)

    offline_test_threads = []
    for i in range(MAX_WORKERS):
        offline_test_thread = threading.Thread(target=request_validator, args=(offline_test_queue, online_test_queue, validate_audio_filetype))
        offline_test_thread.start()
        offline_test_threads.append(offline_test_thread)

    online_test_threads = [threading.Thread(target=request_validator, args=(online_test_queue, None, validate_with_virustotal, (online_test_client[i],))) for i in range(20)]
    for online_test_thread in online_test_threads:
        online_test_thread.start()

    downloader_threads = []
    for i in range(MAX_WORKERS):
        downloader_thread = threading.Thread(target=downloader, args=(download_queue, db_update_queue))
        downloader_thread.start()
        downloader_threads.append(downloader_thread)

    db_updater_threads = []
    for i in range(MAX_WORKERS):
        db_updater_thread = threading.Thread(target=database_updater, args=(db_update_queue,))
        db_updater_thread.start()
        db_updater_threads.append(db_updater_thread)

    upload_approval_sender_threads = []
    for i in range(MAX_WORKERS):
        upload_approval_sender_thread = threading.Thread(target=sender, args=(upload_success_send_queue, stop, True))
        upload_approval_sender_thread.start()
        upload_approval_sender_threads.append(upload_approval_sender_thread)


    socks_receive = dict()
    socks_send = dict()

    def process(cli_sock, mask):
        """
        Invoked by selector. Process readable socket. deliver messages from socket to appropriate threads (resolvers).
        :param cli_sock: (ssl.sslsocket) client socket
        :param mask:
        :return: None
        """
        try:
            send_sock = socks_send[cli_sock]
            for encoded_data in socks_receive[cli_sock]:
                if encoded_data[:len(USER_REQ)] == USER_REQ:
                    user_req_queue.put((encoded_data.decode(), send_sock))
                    continue
                elif encoded_data[:len(CAPTCHA_REQ_PREFIX)] == CAPTCHA_REQ_PREFIX:
                    captcha_req_queue.put((encoded_data.decode(), send_sock))
                    continue
                elif not send_sock in sock_to_uname_hash_map:
                    continue
                elif encoded_data[:len(UPLOAD_REQ)] == UPLOAD_REQ:
                    start = encoded_data.find(b'*') + 1
                    upload_queue.put((encoded_data[start:], send_sock))
                    continue
                data = encoded_data.decode()
                if data[:len(STREAM)] == STREAM:
                    stream_queue.put((data, send_sock))
                    continue
                elif data[:len(RECORD_FETCH)] == RECORD_FETCH:
                    record_fetch_queue.put((data, send_sock))
                elif data[:len(SEARCH_FETCH)] == SEARCH_FETCH:
                    search_fetch_queue.put((data, send_sock))
                elif data == PROFILE_PIC_FECH:
                    profile_pic_fetch_queue.put((data, send_sock))
        except ConnectionError:
            client_sel.unregister(cli_sock)
            socks_receive.pop(cli_sock)
            socks_send.pop(cli_sock)
            if cli_sock in sock_to_uname_hash_map:
                sock_to_uname_hash_map.pop(cli_sock)
            return
        except Exception:
            client_sel.unregister(cli_sock)
            socks_receive.pop(cli_sock)
            socks_send.pop(cli_sock)
            if cli_sock in sock_to_uname_hash_map:
                sock_to_uname_hash_map.pop(cli_sock)
            return



    def accept(sock, mask):
        """
        Invoked by selector. Logs new readable sockets.
        :param sock:
        :param mask:
        :return:
        """
        cli_sock, addr = sock.accept()
        cli_sock.setblocking(False)
        client_sel.register(cli_sock, selectors.EVENT_READ, process)
        safe_cli_sock = ThreadSafeSocket(cli_sock)
        socks_receive[cli_sock] = RequestIterable(safe_cli_sock)
        socks_send[cli_sock] = safe_cli_sock
        print('New user connected!')


    client_sel.register(ser_sock, selectors.EVENT_READ, accept)
    print('Server ready...')
    while not stop:
        events = client_sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)


if __name__ == '__main__':
    main()
