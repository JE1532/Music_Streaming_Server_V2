import sqlite3


#'Fetch_Record/[record_name]'
GET_PIC_PATH = lambda record_name: f'music/{record_name}/picture.jpg'
GET_RECORD_PATH = lambda record_name: f'music/{record_name}/record.txt'
RESPONSE_PREFIX = b'Gui/Fetched/'
FORMAT_LIKES_AND_LISTENNINGS = lambda name, likes, listennings: f'name={name}&likes={likes}&listennings={listennings}&picture='.encode()
SONG_DATABASE = 'songs.db'
FETCH_RECORD_LIKES_AND_LISTENNINGS = lambda name: f'SELECT likes, listennings FROM records WHERE name="{name}"'
IS_PLAYLIST_TRACKLIST = '^tracks:'
PLAYLIST_RESPONSE_PREFIX = 'Gui/Fetched/'.encode()
GET_TRACKLIST_PATH = lambda playlist: f'music/{playlist}/tracklist.txt'


def record_fetch_handler(fetch_queue, send_queue):
    conn = sqlite3.connect(SONG_DATABASE)
    crsr = conn.cursor()
    #crsr.execute('DROP TABLE records;')
    #crsr.execute('CREATE TABLE records(name VARCHAR(64), likes INT, listennings INT, PRIMARY KEY(name));')
    #crsr.execute('INSERT INTO records VALUES("longSoundExample", 50, 79);')
    #crsr.execute('INSERT INTO records VALUES("song2", 57, 64);')
    #crsr.execute('INSERT INTO records VALUES("song3", 47, 34);')
    #conn.commit()
    while True:
        fetch_request, cli_sock = fetch_queue.get()
        try:
            prefix, record_name = fetch_request.split('/')
        except:
            raise Exception('Invalid Fetch Request:', fetch_request)
        if len(record_name) >= len(IS_PLAYLIST_TRACKLIST) and record_name[:len(IS_PLAYLIST_TRACKLIST)] == IS_PLAYLIST_TRACKLIST:
            send_queue.put((fetch_tracklist(record_name), cli_sock))
            continue
        try:
            likes, listennings = crsr.execute(FETCH_RECORD_LIKES_AND_LISTENNINGS(record_name)).fetchall()[0]
        except:
            raise Exception(f'invalid record name: {record_name}\n request was {fetch_request}')
        response = bytearray(RESPONSE_PREFIX + FORMAT_LIKES_AND_LISTENNINGS(record_name, likes, listennings))
        with open(GET_PIC_PATH(record_name), 'rb') as pic_file:
            pic_data = pic_file.read()
            response.extend(pic_data)
        send_queue.put((bytes(response), cli_sock))


def fetch_tracklist(record_name):
    playlist = record_name[len(IS_PLAYLIST_TRACKLIST):]
    with open(GET_TRACKLIST_PATH(playlist), 'rb') as f:
        response = PLAYLIST_RESPONSE_PREFIX + f.read()
    return response