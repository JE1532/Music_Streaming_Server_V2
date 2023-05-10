LENGTH_PREFIX = lambda length: f'LEN {length}@'.encode()


def sender(queue, stop, length_prefix=False):
    while not stop:
        data, sock = queue.get()
        if length_prefix:
            data = LENGTH_PREFIX(len(data)) + data
        try:
            sock.send(data)
        except:
            continue
