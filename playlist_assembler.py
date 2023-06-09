UPLOAD_SUCCESSFUL_RESP = b'Upload_Resp/Upload_Successful'
UPLOAD_FAILED_RESP = b'Upload_Resp/Upload_Failed'


def playlist_assembler(input_queue, test_queue, download_queue, send_queue):
    """
    Runs Playlist Assembler thread. Blocks.
    :param input_queue: (Queue(MakeRecordRequest)) of incoming client requests
    :param test_queue: (Queue) for delivering requests to request validators for security tests
    :param download_queue: (Queue) for delivering requests to be downloaded
    :param send_queue: (Queue) for user response sending.
    :return: None
    """
    while True:
        playlist_upload_req, cli_sock = input_queue.get()
        try:
            if len(playlist_upload_req.external_name) > 64:
                send_queue.put((UPLOAD_FAILED_RESP, cli_sock))
                continue
            success = process(playlist_upload_req, test_queue, download_queue)
            if success:
                send_queue.put((UPLOAD_SUCCESSFUL_RESP, cli_sock))
            else:
                send_queue.put((UPLOAD_FAILED_RESP, cli_sock))
        except:
            continue


def process(playlist_upload_req, test_queue, download_queue):
    """
    Process a single playlist upload request, by delivering all files to testers,
    and then to downloaders.
    :param playlist_upload_req: (MakeRecordRequest) request to upload playlist
    :param test_queue: (Queue) for passing requests to request_validators
    :param download_queue: (Queue) for passing requests to downloaders
    :return: None
    """
    playlist_upload_req.data[0].validate_image = True
    execute_for_all(playlist_upload_req.data, test_queue)
    for song_req in playlist_upload_req.data:
        if not song_req.valid:
            return False
    execute_for_all(playlist_upload_req.data, download_queue)
    download_queue.put(playlist_upload_req)
    playlist_upload_req.done.wait()
    return True


def execute_for_all(requests, q):
    """
    Deliver all requests in requests to q and wait for action completion.
    :param requests: (list(MakeRecordRequest)) list of requests.
    :param q: (Queue) to deliver requests to validators or downloaders.
    :return:
    """
    for song_req in requests:
        if song_req.done.isSet():
            song_req.done.clear()
    for song_req in requests:
        q.put(song_req)
    for song_req in requests:
        song_req.done.wait()
