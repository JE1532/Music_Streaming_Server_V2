import random
import string
import enum
from queue import Queue
from threading import Event


DELIMITER = b'&'
LENGTH_PREFIX = b' LEN '
LENGTH_END = b'*'
PLAYLIST = 'playlist'
INTERNAL_NAME_LENGTH = 64
SONG_NAMES = b'song_name'
PICTURE = b'pic'
EXTERNAL_NAME = b'external_name'
SONG_AUDIO = b'song_audio'


class RecordType(enum.Enum):
    PLAYLIST: int = 0
    SONG: int = 1


class MakeRecordRequest:
    def __init__(self, type, internal_name, external_name, picture, data):
        self.type = type
        self.internal_name = internal_name
        self.external_name = external_name
        self.picture = picture
        self.data = data
        self.done = Event()
        self.valid = None



def upload_request_download_distributor(input_queue, assembly_queue):
    """
    This is the distributor for upload requests.
    It receives upload requests through the input queue, splits each into individual songs and a playlist, and
    passes those to the downloaders for saving via the output queue.
    :param input_queue: input queue for incoming requests.
    :param output_queue: output queue for individual savable records.
    :return:
    """
    while True:
        curr_req, cli_sock = input_queue.get()
        try:
            playlist_req, song_count = process(curr_req)
            assembly_queue.put((playlist_req, cli_sock))
        except:
            continue


def process(curr_req):
    cursor = 0
    fields = {EXTERNAL_NAME: [], PICTURE: [], SONG_NAMES: [], SONG_AUDIO: []}
    while cursor < len(curr_req):
        prefix, data, cursor = process_field(curr_req, cursor)
        fields[prefix].append(data)

    external_song_names = [name.decode() for name in fields[SONG_NAMES]]
    internal_song_names = [generate_internal_name() for song in external_song_names]
    internal_playlist_name = generate_internal_name()
    song_audio = fields[SONG_AUDIO]
    pic = fields[PICTURE][0]
    external_playlist_name = fields[EXTERNAL_NAME][0].decode()
    song_req_lst = []
    for i in range(len(external_song_names)):
        curr_req = MakeRecordRequest(RecordType.SONG, internal_song_names[i], external_song_names[i], pic, song_audio[i])
        song_req_lst.append(curr_req)
    playlist_req = MakeRecordRequest(RecordType.PLAYLIST, internal_playlist_name, external_playlist_name, pic, song_req_lst)
    return playlist_req, len(external_song_names)


def process_field(curr_req, cursor):
    eq_index = curr_req.find(b'=', cursor, len(curr_req))
    prefix = curr_req[cursor:eq_index]
    length_start = eq_index + len(LENGTH_PREFIX) + 1
    length_end = curr_req.find(LENGTH_END, length_start, len(curr_req))
    length = int(curr_req[length_start:length_end])
    data = curr_req[length_end + 1: length_end + 1 + length]
    new_cursor = length_end + 1 + length + len(DELIMITER)
    return prefix, data, new_cursor


def generate_internal_name():
    return ''.join(random.choices(string.ascii_lowercase, k=INTERNAL_NAME_LENGTH))
