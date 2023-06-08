import os
import subprocess
import upload_request_download_distributor as dist


FFMPEG_COMMAND = lambda m3u8_path, segment_name_format, segment_time: ['ffmpeg', '-y', '-f', 'wav', '-i', 'pipe:0', '-c:a', 'aac', '-b:a', '128k', '-muxdelay', '0', '-f', 'segment', '-sc_threshold', '0', '-segment_time', str(segment_time), '-segment_list', m3u8_path, '-segment_format', 'mpegts', segment_name_format]
M3U8_PATH = lambda internal_name: f'music/{internal_name}/{internal_name}.m3u8'
SEGMENT_NAME_FORMAT = lambda internal_name: f'music/{internal_name}/segment%d.m4a'
PIC_PATH = lambda internal_name: f'music/{internal_name}/picture.jpg'
TRACKLIST_PATH = lambda internal_name: f'music/{internal_name}/tracklist.txt'
DIR_PATH = lambda internal_name: f'music/{internal_name}'
SEGMENT_TIME = 5

TRACKLIST_TRACK_PREFIX = lambda i: f'#{i}\n'
TRACKLIST_TRACK_SUFFIX = lambda i: f'\n'


def downloader(input_queue, output_queue):
    """
    downloads requests received from input queue as upload_request_download_distributor.MakeRecordRequest
    and passes them forward for database refactoring to output_queue

    :param input_queue:
    :param output_queue:
    :return:
    """
    while True:
        curr_req = input_queue.get()
        try:
            process(curr_req)
            output_queue.put(curr_req)
        except Exception as e:
            raise e
            continue

def process(curr_req):
    os.mkdir(DIR_PATH(curr_req.internal_name))
    if curr_req.type == dist.RecordType.SONG:
        p = subprocess.Popen(FFMPEG_COMMAND(M3U8_PATH(curr_req.internal_name), SEGMENT_NAME_FORMAT(curr_req.internal_name), SEGMENT_TIME), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_out, p_err = p.communicate(input=curr_req.data)
    else:
        data = construct_tracklist(curr_req)
        with open(TRACKLIST_PATH(curr_req.internal_name), 'w') as tracklist_file:
            tracklist_file.write(data)

    with open(PIC_PATH(curr_req.internal_name), 'wb') as pic_file:
        pic_file.write(curr_req.picture)


def construct_tracklist(playlist_req):
    tracklist = []
    for i in range(len(playlist_req.data)):
        tracklist.append(TRACKLIST_TRACK_PREFIX(i))
        tracklist.append(playlist_req.data[i].internal_name)
        tracklist.append(TRACKLIST_TRACK_SUFFIX(i))
    return ''.join(tracklist)
