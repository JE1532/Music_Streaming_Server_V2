def listener(server_sock, output_set, stop):
    while not stop:
        server_sock.listen(100)
        curr_sock, curr_addr = server_sock.accept()
        curr_sock.setblocking(False)
        output_set.add(curr_sock)
