import ssl


CHUNK_SIZE = 256
HTTP_REQ = b'GET'


def recvall(socket):
    data = bytearray()
    while True:
        try:
            data.extend(socket.recv(CHUNK_SIZE))
        except ssl.SSLWantReadError:
            break
    return bytes(data)


def find(string, sub, start, end):
    i = start
    while i < end - len(sub) + 1:
        valid = True
        for cursor in range(len(sub)):
            if string[i + cursor] != sub[cursor]:
                valid = False
                break
        if valid == True:
            return i
        i += 1
    return -1


class RequestIterable:
    def __init__(self, socket, delimiter=b'@'):
        self.socket = socket
        self.delimiter = delimiter


    def __iter__(self):
        return RequestIterable.RequestIterator(recvall(self.socket), self.delimiter)


    class RequestIterator:
        def __init__(self, data, delimiter):
            self.data = data
            self.delimiter = delimiter
            self.cursor = 0


        def __iter__(self):
            return self


        def __next__(self):
            if self.cursor == len(self.data):
                raise StopIteration
            if self.data[self.cursor:self.cursor + len(HTTP_REQ)] == HTTP_REQ:
                return self.process_request(b'\r\n\r\n')
            else:
                return self.process_request(self.delimiter)


        def process_request(self, delimiter):
            prev_cursor = self.cursor
            self.cursor = find(self.data, delimiter, self.cursor, len(self.data)) + len(delimiter)
            return self.data[prev_cursor:self.cursor - len(delimiter)]




