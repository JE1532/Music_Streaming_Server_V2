GET_SONG_RECOMMENATIONS = 'Search?prompt=^Song_Recommendations'
GET_ALBUM_RECOMMENDATIONS = 'Search?prompt=^Playlist_Recommendations'
SONG_RECOMMENDATION_PATH = 'music/song_recommendations.txt'
ALBUM_RECOMMENDATIONS_PATH = 'music/playlist_recommendations.txt'
RESPONSE_PREFIX = 'Gui/Searched/'

def search_fetch(search_queue, send_queue):
    while True:
        to_search, cli_sock = search_queue.get()
        print(f'searched for: {to_search}')
        if to_search == GET_SONG_RECOMMENATIONS:
            with open(SONG_RECOMMENDATION_PATH, 'rb') as f:
                send_queue.put((RESPONSE_PREFIX.encode() + f.read(), cli_sock))
        elif to_search == GET_ALBUM_RECOMMENDATIONS:
            with open(ALBUM_RECOMMENDATIONS_PATH, 'rb') as f:
                send_queue.put((RESPONSE_PREFIX.encode() + f.read(), cli_sock))
