import sqlite3
from upload_request_download_distributor import RecordType


ADD_TO_DB = f"INSERT INTO records VALUES(?, ?, ?, ?, ?);"


def database_updater(input_queue):
    """
    gets upload_playlist_download_distributor.MakeRecordRequest(s) from input_queue and
    adds each request to the database. afterwards, it marks the requests as 'done'.

    :param input_queue: queue of incoming requests.
    :return:
    """
    conn = sqlite3.connect('songs.db')
    crsr = conn.cursor()
    while True:
        curr_req = input_queue.get()
        try:
            process(curr_req ,crsr, conn)
        except Exception as e:
            continue


def process(curr_req, crsr, conn):
    """
    Add a single request to database.
    :param curr_req: (MakeRecordRequest) request
    :param crsr: (sqlite3.Cursor) for songs.db
    :param conn: (qlite3.Connection) for songs.db
    :return: None
    """
    crsr.execute(ADD_TO_DB, (curr_req.internal_name, curr_req.external_name, 0, 0, 0 if curr_req.type == RecordType.SONG else 1))
    conn.commit()
    curr_req.done.set()
