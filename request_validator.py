from PIL import Image
from io import BytesIO
import subprocess
from upload_request_download_distributor import RecordType


FFPROBE_AUDIO_VALIDATION_COMMAND = ['ffprobe', '-v', 'quiet', '-show_streams', '-show_format', 'pipe:0']
CODEC_TYPE = b'codec_type='
AUDIO = b'audio'


def request_validator(input_queue, output_queue, test):
    """
    Receives upload_playlist_download_distributor.MakeRecordRequest(s) from input_queue,
    checks each request for threats using test (a function). afterwards if there is an output queue and request
    is valid it delivers it onwards, and if there isn't it marks the request as valid and done.
    invalid requests are instantly marked as invalid and done and not passed forward through output_queue.

    :param input_queue: incoming request queue.
    :param output_queue: queue to pass requests on.
    :param test: testing function for threats.
    :return:
    """
    while True:
        curr_req = input_queue.get()
        if curr_req.done.isSet():
            continue
        try:
            res = test(curr_req)
            if not res:
                curr_req.valid = False
                curr_req.done.set()
            if not output_queue and res:
                curr_req.valid = True
                curr_req.done.set()
            elif res:
                output_queue.put(curr_req)
        except:
            curr_req.valid = False
            curr_req.done.set()
            continue


def validate_audio_filetype(make_song_req):
    img = Image.open(BytesIO(make_song_req.picture))
    try:
        img.load()
    except:
        return False
    if make_song_req.type == RecordType.SONG:
        p = subprocess.Popen(FFPROBE_AUDIO_VALIDATION_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_out, p_err = p.communicate(input=make_song_req.data)
        if p_out == b'':
            return False
        tags = p_out.split(b'\r\n')
        seen_codec_type_tag = False
        for tag in tags:
            if tag[:len(CODEC_TYPE)] == CODEC_TYPE:
                seen_codec_type_tag = True
                if tag.split(b'=')[1] != AUDIO:
                    return False
        if not seen_codec_type_tag:
            return False
    return True
