UPLOAD_SUCCESSFUL_RESP = b'Gui/Upload_Successful'
UPLOAD_FAILED_RESP = b'Gui/Upload_Failed'


def playlist_assembler(input_queue, test_queue, download_queue, send_queue):
    while True:
        playlist_upload_req, cli_sock = input_queue.get()
        try:
            success = process(playlist_upload_req, test_queue, download_queue)
            if success:
                send_queue.put((UPLOAD_SUCCESSFUL_RESP, cli_sock))
            else:
                send_queue.put((UPLOAD_FAILED_RESP, cli_sock))
        except:
            continue


def process(playlist_upload_req, test_queue, download_queue):
    execute_for_all(playlist_upload_req.data, test_queue)
    for song_req in playlist_upload_req.data:
        if not song_req.valid:
            return False
    execute_for_all(playlist_upload_req.data, download_queue)
    download_queue.put(playlist_upload_req)
    playlist_upload_req.done.wait()
    return True


def execute_for_all(requests, q):
    for song_req in requests:
        if song_req.done.isSet():
            song_req.done.clear()
    for song_req in requests:
        q.put(song_req)
    for song_req in requests:
        song_req.done.wait()
