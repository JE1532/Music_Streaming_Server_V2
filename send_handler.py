def sender(queue, stop):
    while not stop:
        data, sock = queue.get()
        try:
            sock.send(data)
        except:
            continue
