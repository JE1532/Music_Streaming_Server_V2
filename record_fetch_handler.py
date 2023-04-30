import sqlite3


#'Fetch_Record/[record_name]'
GET_PIC_PATH = lambda record_name: f'music/{record_name}/picture.jpg'
GET_RECORD_PATH = lambda record_name: f'music/{record_name}/record.txt'
RESPONSE_PREFIX = b'Gui/Fetched/'
FORMAT_LIKES_AND_LISTENNINGS = lambda name, likes, listennings: f'name={name}&likes={likes}&listennings={listennings}&picture='.encode()
SONG_DATABASE = 'songs.db'
FETCH_RECORD_LIKES_AND_LISTENNINGS = lambda name: f'SELECT likes, listennings FROM records WHERE name="{name}"'


def record_fetch_handler(fetch_queue, send_queue):
    conn = sqlite3.connect(SONG_DATABASE)
    crsr = conn.cursor()
    crsr.execute('DROP TABLE records;')
    crsr.execute('CREATE TABLE records(name VARCHAR(64), likes INT, listennings INT, PRIMARY KEY(name));')
    crsr.execute('INSERT INTO records VALUES("longSoundExample", 50, 79);')
    crsr.execute('INSERT INTO records VALUES("song2", 57, 64);')
    crsr.execute('INSERT INTO records VALUES("song3", 47, 34);')
    while True:
        fetch_request, cli_sock = fetch_queue.get()
        try:
            prefix, record_name = fetch_request.split('/')
        except:
            raise Exception('Invalid Fetch Request:', fetch_request)
        try:
            likes, listennings = crsr.execute(FETCH_RECORD_LIKES_AND_LISTENNINGS(record_name)).fetchall()[0]
        except:
            raise Exception(f'invalid record name: {record_name}\n request was {fetch_request}')
        response = bytearray(RESPONSE_PREFIX + FORMAT_LIKES_AND_LISTENNINGS(record_name, likes, listennings))
        with open(GET_PIC_PATH(record_name), 'rb') as pic_file:
            pic_data = pic_file.read()
            response.extend(pic_data)
        send_queue.put((bytes(response), cli_sock))
