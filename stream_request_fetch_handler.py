from datetime import datetime
import time

SERVER = 'localhost:9010'
PREFIX = 'music/'
PREFIX_LENGTH = 6
ACCESS_DENIED_RESPONSE = f"""HTTP/3 403 Forbidden
Server: {SERVER}
""".encode()

WEEKDAYS = {6: 'Sun', 0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat'}
MONTHS = {0: 'Jan', 1: 'Feb', 2: 'Mar', 3: 'Apr', 4: 'May', 5: 'Jun', 6: 'Jul', 7: 'Aug', 8: 'Sep', 9: 'Oct', 10: 'Nov', 11: 'Dec'}
now = datetime.now
GET_CURRENT_DATE = lambda: str.format('{}, {} {} {} {}:{}:{}', WEEKDAYS[now().weekday()], str(now().day).zfill(2), MONTHS[now().month], str(now().year), str(now().hour - 5).zfill(2), str(now().minute).zfill(2), str(now().second).zfill(2))

OK_RESPONSE2 = f"""HTTP/1.1 200 OK\r
Accept-Ranges: bytes\r
Access-Control-Allow-Origin: *\r
Age: 19\r
Date: {'{}'}\r
Server: {SERVER}\r
Last-Modified: Thu, 13 Oct 2016 00:25:58 GMT\r
Content-Length: {'{}'}\r
Content-Type: audio/x-mpegurl\r
Via: 1.1 127.0.0.1:9010\r 
Connection: Keep-Alive\r
\r
"""
OK_RESPONSE = """HTTP/1.1 200 OK\r
Content-Type: audio/x-mpegurl\r
Content-Length: {}\r
Connection: keep-alive\r
Last-Modified: Thu, 13 Oct 2016 00:25:58 GMT\r
Accept-Ranges: bytes\r
Server: MyServer\r
Date: Tue, 11 Apr 2023 05:34:09 GMT\r
Via: 1.1 localhost:9010 (CloudFront)\r
Age: 11834\r
\r
"""


def fetch(request_queue, output_queue, stop):
    """
    Runs Stream Fetcher thread. Blocks.
    :param request_queue:
    :param output_queue:
    :param stop:
    :return:
    """
    request, sock = request_queue.get()
    while not stop:
        print('starting fetch')
        lines = request.split("\n")
        url = lines[0].split(' ')[1]
        if not url[:max(len(url), 6)] == PREFIX:
            with open(url[1:], 'rb') as f_input:
                data = f_input.read()
                output_queue.put((str.format(OK_RESPONSE, str(len(data))).encode() + data, sock))
        else:
            output_queue.put((ACCESS_DENIED_RESPONSE, sock))
        print("fetched!")
        request, sock = request_queue.get()
