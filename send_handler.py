import ssl

LENGTH_PREFIX = lambda length: f'LEN {length}@'.encode()


def sender(queue, stop, length_prefix=False):
    while not stop:
        data, sock = queue.get()
        if length_prefix:
            data = LENGTH_PREFIX(len(data)) + data
        success = False
        while not success:
            try:
                sock.send(data)
            except ssl.SSLWantWriteError as e:
                print(e)
                continue
            success = True
