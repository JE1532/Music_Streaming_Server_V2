import ssl


CHUNK_SIZE = 256
HTTP_REQ = b'GET'
UPLOAD_REQ = b'Gui/Upload_Playlist/LEN '
LENGTH_FIELD_END = b'*'


def recvall(socket):
    data = bytearray()
    while True:
        try:
            curr_chunk = socket.recv(CHUNK_SIZE)
            data.extend(curr_chunk)
            if curr_chunk == b'':
                break
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
            elif self.data[self.cursor: self.cursor + len(UPLOAD_REQ)] == UPLOAD_REQ:
                return self.process_upload_request()
            else:
                return self.process_request(self.delimiter)


        def process_request(self, delimiter):
            prev_cursor = self.cursor
            self.cursor = find(self.data, delimiter, self.cursor, len(self.data)) + len(delimiter)
            return self.data[prev_cursor:self.cursor - len(delimiter)]


        def process_upload_request(self):
            prev_cursor = self.cursor
            self.cursor += len(UPLOAD_REQ)
            msg_length_string_end = find(self.data, LENGTH_FIELD_END, self.cursor, len(self.data))
            length_field_string = self.data[self.cursor:msg_length_string_end].decode()
            length = int(length_field_string)
            self.cursor += len(length_field_string) + len(LENGTH_FIELD_END) + length
            upload_request = self.data[prev_cursor:self.cursor]
            return upload_request
