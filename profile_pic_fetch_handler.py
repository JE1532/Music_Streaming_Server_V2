from os.path import isfile


GET_PIC_PATH = lambda uname_hash: f'users/profile_pictures/{uname_hash}.jpg'
RESPONSE_PREFIX = b'Gui/Profile_Picture='
DEFAULT_PROFILE_PIC_PATH = 'users/profile_pictures/default.jpg'


def profile_pic_fetch(input_queue, socket_to_uname_hash, output_queue):
    while True:
        request, cli_sock = input_queue.get()
        if not cli_sock in socket_to_uname_hash:
            continue
        uname_hash = socket_to_uname_hash[cli_sock]
        response = bytearray(RESPONSE_PREFIX)
        path = GET_PIC_PATH(uname_hash)
        path = path if isfile(path) else DEFAULT_PROFILE_PIC_PATH
        with open(path, 'rb') as f:
            response.extend(f.read())
        output_queue.put((response, cli_sock))
