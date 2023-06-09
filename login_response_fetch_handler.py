import sqlite3
from hashlib import sha3_256 as hash_func
import time


DATABASE_FILE = 'users.db'
CREATE_USER_TABLE = """CREATE TABLE users(
             username_hash VARCHAR(64),
             password_hash VARCHAR(64),
             email VARCHAR(30),
             PRIMARY KEY(username_hash));"""
CLEAR_TABLE = """DELETE FROM users WHERE true;"""
DROP_USER_TABLE ="DROP TABLE users"
SELECT = lambda table, fields : str.format("SELECT {} FROM {} WHERE username_hash=?;", fields, table)
INSERT = lambda table, values : str.format('INSERT INTO {} VALUES({});', table, values)

LOG_NEW_USER = "UserProcessor/SignUp"
LOG_RETURNING_USER = "UserProcessor/SignIn"
LOG_OUT_REQUEST = 'UserProcessor/LogOut'

MAX_CREDENTIAL_LENGTH = 64

USER_ALREADY_EXISTS = 'UserProcessor/user_already_exists'.encode()
NO_SUCH_USER = 'UserProcessor/no_such_user'.encode()
WRONG_PASSWORD = 'UserProcessor/wrong_password'.encode()
AUTH_OKAY = 'UserProcessor/200'.encode()
CREDENTIAL_TOO_LONG = 'UserProcessor/credential_too_long'

PREFIX = 'UserProcessor/'

CAPTCHA_REQ_PREFIX = 'UserProcessor/Submit_Captcha/solution='
CAPTCHA_SOL_RESPONSE = lambda valid: b'Gui/Captcha_Response/200' if valid else  b'Gui/Captcha_Response/400'
CAPTCHA_NOT_SOLVED = b'UserProcessor/captcha_has_not_been_solved._please_request_one.'


def log_new_user(arguments, crsr):
    """
        Logs a new user.
        :param arguments: [{username}, {password}, {email}]
        :return: (str) to send to client, (str) username hash, (bool) login successful or not
    """
    for arg in arguments:
        if len(arg) > MAX_CREDENTIAL_LENGTH:
            return
    uname_hash = hash_func(arguments[0].encode()).hexdigest()
    if list(crsr.execute(SELECT('users', '*',), (uname_hash,))):
        return USER_ALREADY_EXISTS, uname_hash, False
    password_hash = hash_func(arguments[1].encode()).hexdigest()
    crsr.execute(INSERT('users', str.format('"{}","{}","{}"', uname_hash, password_hash, arguments[2])))
    return AUTH_OKAY, uname_hash, True


def log_returning_user(arguments, crsr):
    """
            Logs a returning user.
            :param arguments: [{username}, {password}]
            :return: (str) to send to client, (str) username hash, (bool) login successful or not
    """
    uname_hash = hash_func(arguments[0].encode()).hexdigest()
    password_hash = hash_func(arguments[1].encode()).hexdigest()
    user = crsr.execute(SELECT('users', 'password_hash'), (uname_hash,)).fetchall()
    if not user:
        return NO_SUCH_USER, uname_hash, False
    if not user[0][0] == password_hash:
        return WRONG_PASSWORD, uname_hash, False
    return AUTH_OKAY, uname_hash, True


def process_captcha_solution(captcha_solution_manager, cli_sock, request):
    """
    Process a captcha solution using solution manager, update solution manager accordingly and return whether solution was
    correct.
    :param captcha_solution_manager: (CaptchaSolutionManager) manager
    :param cli_sock: (ThreadSafeSocket) client socket
    :param request: (str) request sent by the client for solution submition
    :return:
    """
    solution = request[len(CAPTCHA_REQ_PREFIX):]
    return captcha_solution_manager.validate_solution(cli_sock, solution)


PROCESS_REQUEST = {'SignUp' : log_new_user, 'SignIn' : log_returning_user}


def fetch(request_queue, output_queue, stop, sock_to_uname_hash_map, captcha_solution_manager):
    """
    Runs UserProcessor thread. Blocks.
    :param request_queue: (Queue) of incoming requests.
    :param output_queue: (Queue) of replies to send via sender
    :param stop: boolean to indicate termination
    :param sock_to_uname_hash_map: (dict(ThreadSafeSocket, str)) mapping between client socket and hashes of their usernames
    :param captcha_solution_manager: (CaptchaSolutionManager) captha solution manager
    :return: None
    """
    connection = sqlite3.connect(DATABASE_FILE)
    crsr = connection.cursor()
    #crsr.execute(CREATE_USER_TABLE)
    #crsr.execute(CLEAR_TABLE)
    while not stop:
        request, sock = request_queue.get()
        if request == LOG_OUT_REQUEST:
            sock_to_uname_hash_map.pop(sock)
            print('User logged out.')
            continue
        response, uname_hash, auth_successful = process_request(request, crsr, captcha_solution_manager, sock)
        connection.commit()
        if auth_successful:
            sock_to_uname_hash_map[sock] = uname_hash
        output_queue.put((response, sock))


def process_request(request, crsr, captcha_solution_manager, cli_sock):
    """
    Process a single authentication / captcha solution validation request.
    :param request: (bytes) request as a bytestring
    :param crsr: (sqlite3.Cursor) for users.db
    :param captcha_solution_manager: (CaptchaSolutionManager) captcha solution manager.
    :param cli_sock: (ThreadSafeSoskcet) client socket.
    :return:
    """
    if request[:len(CAPTCHA_REQ_PREFIX)] == CAPTCHA_REQ_PREFIX:
        return CAPTCHA_SOL_RESPONSE(process_captcha_solution(captcha_solution_manager, cli_sock, request)), None, False
    if not captcha_solution_manager.is_approved(cli_sock):
        return CAPTCHA_NOT_SOLVED, None, False
    url = request.split('\n')[0][len(PREFIX):]
    request_type, request_args_bulk = url.split('?')
    request_args = [arg.split('=')[1] for arg in request_args_bulk.split('&')]
    return PROCESS_REQUEST[request_type](request_args, crsr)


if __name__ == "__main__":
    fetch(None, None, None, None)