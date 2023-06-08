import selectors
import threading
import concurrent.futures
from queue import Queue
import socket
import ssl

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
from request_validator import request_validator, validate_audio_filetype


STREAM = 'GET'
USER_REQ = 'UserProcessor'
RECORD_FETCH = 'Fetch'
SEARCH_FETCH = 'Search'
PROFILE_PIC_FECH = 'Gui/Get_Profile_Picture'
UPLOAD_REQ = b'Gui/Upload_Playlist/LEN '

MAX_WORKERS = 1

SERVER = ('0.0.0.0', 9010)
KEYFILE = 'server.key'
CERTFILE = 'server.crt'

SUFFIX = b'@'


class ThreadSafeSocket:
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



def main():
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
    sock_to_uname_hash_map = dict()
    stop = False
    #stream_fetcher_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    #for i in range(MAX_WORKERS):
    #    stream_fetcher_pool.submit(stream_fetch, stream_queue, stream_fetch_to_send_queue, stop)
    stream_fetcher_thread = threading.Thread(target=stream_fetch, args=(stream_queue, stream_fetch_to_send_queue, stop))
    stream_fetcher_thread.start()

    stream_sender_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    for i in range(MAX_WORKERS):
        stream_sender_pool.submit(sender, stream_fetch_to_send_queue, stop, False)
    #stream_sender_thread = threading.Thread(target=sender, args=(stream_fetch_to_send_queue, stop))
    #stream_sender_thread.start()

    profile_pic_fetch_queue = Queue()
    profile_pic_send_queue = Queue()
    profile_pic_fetch_thread = threading.Thread(target=profile_pic_fetch, args=(profile_pic_fetch_queue,sock_to_uname_hash_map, profile_pic_send_queue))
    profile_pic_fetch_thread.start()

    profile_pic_send_thread = threading.Thread(target=sender, args=(profile_pic_send_queue, stop, True))
    profile_pic_send_thread.start()

    #user_proc_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    #for i in range(MAX_WORKERS):
    #    user_proc_pool.submit(login_fetch, user_req_queue, user_req_fetch_to_send_queue, stop, sock_to_uname_hash_map)
    user_proc_thread = threading.Thread(target=login_fetch, args=(user_req_queue, user_req_fetch_to_send_queue, stop, sock_to_uname_hash_map))
    user_proc_thread.start()

    #user_proc_sender_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    #for i in range(MAX_WORKERS):
    #    user_proc_sender_pool.submit(sender, user_req_fetch_to_send_queue, stop)
    user_proc_sender_thread = threading.Thread(target=sender, args=(user_req_fetch_to_send_queue, stop, True))
    user_proc_sender_thread.start()

    search_fetch_queue = Queue()
    search_send_queue = Queue()
    record_fetch_queue = Queue()
    record_fetch_send_queue = Queue()

    search_fetch_thread = threading.Thread(target=search_fetch, args=(search_fetch_queue, search_send_queue))
    search_fetch_thread.start()

    record_fetch_thread = threading.Thread(target=record_fetch_handler, args=(record_fetch_queue, record_fetch_send_queue))
    record_fetch_thread.start()

    search_sender_thead = threading.Thread(target=sender, args=(search_send_queue, stop, True))
    search_sender_thead.start()

    record_sender_thread = threading.Thread(target=sender, args=(record_fetch_send_queue, stop, True))
    record_sender_thread.start()

    upload_queue = Queue()
    playlist_assembler_queue = Queue()
    test_queue = Queue()
    download_queue = Queue()
    db_update_queue = Queue()
    upload_success_send_queue = Queue()

    record_download_dist_thread = threading.Thread(target=upload_request_download_distributor, args=(upload_queue, playlist_assembler_queue))
    record_download_dist_thread.start()

    playlist_assembly_thread = threading.Thread(target=playlist_assembler, args=(playlist_assembler_queue, test_queue, download_queue, upload_success_send_queue))
    playlist_assembly_thread.start()

    offline_test_thread = threading.Thread(target=request_validator, args=(test_queue, None, validate_audio_filetype))
    offline_test_thread.start()

    downloader_thread = threading.Thread(target=downloader, args=(download_queue, db_update_queue))
    downloader_thread.start()

    db_updater_thread = threading.Thread(target=database_updater, args=(db_update_queue,))
    db_updater_thread.start()

    upload_approval_sender_thread = threading.Thread(target=sender, args=(upload_success_send_queue, stop, True))
    upload_approval_sender_thread.start()


    socks_receive = dict()
    socks_send = dict()

    def process(cli_sock, mask):
        try:
            send_sock = socks_send[cli_sock]
            for encoded_data in socks_receive[cli_sock]:
                if encoded_data[:len(UPLOAD_REQ)] == UPLOAD_REQ:
                    start = encoded_data.find(b'*') + 1
                    upload_queue.put((encoded_data[start:], send_sock))
                    continue
                data = encoded_data.decode()
                if data[:len(STREAM)] == STREAM:
                    stream_queue.put((data, send_sock))
                    return
                elif data[:len(USER_REQ)] == USER_REQ:
                    user_req_queue.put((data, send_sock))
                    return
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



    def accept(sock, mask):
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
