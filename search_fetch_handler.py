import sqlite3


GET_SONG_RECOMMENATIONS = 'Search?prompt=^Song_Recommendations'
GET_ALBUM_RECOMMENDATIONS = 'Search?prompt=^Playlist_Recommendations'
SONG_RECOMMENDATION_PATH = 'music/song_recommendations.txt'
ALBUM_RECOMMENDATIONS_PATH = 'music/playlist_recommendations.txt'
RESPONSE_PREFIX = 'Gui/Searched/'
DATABASE_PATH = 'songs.db'
SEARCH = "SELECT name FROM records WHERE name LIKE ? ORDER BY listennings LIMIT 10"
PREPARE_PROMPT = lambda prompt: '%' + prompt + '%'
RECORD_RESPONSE_FORMAT = lambda name, serial: f'#{serial}\r\n{name}\r\n'


def search_fetch(search_queue, send_queue):
    conn = sqlite3.connect(DATABASE_PATH)
    crsr = conn.cursor()
    while True:
        to_search, cli_sock = search_queue.get()
        print(f'searched for: {to_search}')
        if to_search == GET_SONG_RECOMMENATIONS:
            with open(SONG_RECOMMENDATION_PATH, 'rb') as f:
                send_queue.put((RESPONSE_PREFIX.encode() + f.read(), cli_sock))
        elif to_search == GET_ALBUM_RECOMMENDATIONS:
            with open(ALBUM_RECOMMENDATIONS_PATH, 'rb') as f:
                send_queue.put((RESPONSE_PREFIX.encode() + f.read(), cli_sock))
        else:
            prompt = to_search.split('=')[1]
            crsr.execute(SEARCH, (PREPARE_PROMPT(prompt),))
            relevant_records = crsr.fetchall()
            send_queue.put(((RESPONSE_PREFIX + construct_response_file(relevant_records)).encode(), cli_sock))


def construct_response_file(records):
    response = []
    for i in range(len(records)):
        response.append(RECORD_RESPONSE_FORMAT(records[i][0], i))
    return ''.join(response)
