import ssl


CHUNK_SIZE = 256
HTTP_REQ = b'GET'
UPLOAD_REQ = b'Gui/Upload_Playlist/LEN '
LENGTH_FIELD_END = b'*'
SEARCH_PREFIX = b'Search'
GET_TRACKS_PREFIX = b'Fetch/^tracks'


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
    raise Exception('Invalid request received.')


class RequestIterable:
    def __init__(self, socket, unlimited_length_prefix_list=[SEARCH_PREFIX, GET_TRACKS_PREFIX, HTTP_REQ, UPLOAD_REQ],delimiter=b'@'):
        self.socket = socket
        self.delimiter = delimiter
        self.unlimited_length_prefix = unlimited_length_prefix_list


    def __iter__(self):
        return RequestIterable.RequestIterator(recvall(self.socket), self.delimiter, self.unlimited_length_prefix)


    class RequestIterator:
        def __init__(self, data, delimiter, unlimited_length_prefix):
            self.data = data
            self.delimiter = delimiter
            self.unlimited_length_prefix = unlimited_length_prefix
            self.cursor = 0


        def __iter__(self):
            return self


        def __next__(self):
            if self.cursor == len(self.data):
                raise StopIteration
            request = None
            if self.data[self.cursor:self.cursor + len(HTTP_REQ)] == HTTP_REQ:
                request = self.process_request(b'\r\n\r\n')
            elif self.data[self.cursor: self.cursor + len(UPLOAD_REQ)] == UPLOAD_REQ:
                request = self.process_upload_request()
            else:
                request = self.process_request(self.delimiter)
            if (not (True in [request[:len(prefix)] == prefix for prefix in self.unlimited_length_prefix])) and len(request) > 200:
                raise Exception('Request too long.')
            return request


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
