import ssl

LENGTH_PREFIX = lambda length: f'LEN {length}@'.encode()


def sender(queue, stop, length_prefix=False):
    """
    Runs Send Handler thread. Blocks.
    :param queue: (Queue) of responses to send to clients.
    :param stop: (bool) indicates termination.
    :param length_prefix: add a length prefix to every message or not.
    :return:
    """
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
