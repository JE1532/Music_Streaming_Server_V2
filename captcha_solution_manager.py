from threading import Lock


class CaptchaManager:
    """
    Manages captcha information (a mapping of captcha solutions to client and a list
    of clients who have solved a captcha since they were last approved).
    """
    def __init__(self):
        """
        Initialize manager.
        """
        self.sock_to_solution = dict()
        self.sock_to_solution_lock = Lock()
        self.approved_sockets = set()
        self.approval_lock = Lock()


    def register_captcha(self, sock, solution):
        """
        Register captcha solution and associate it to client corresponding to sock.
        :param sock: (ThreadSafeSocket) client socket.
        :param solution: (str) captcha solution.
        :return: None
        """
        with self.sock_to_solution_lock:
            self.sock_to_solution[sock] = solution


    def validate_solution(self, sock, solution):
        """
        returns True if and only if the solution matches solution associated to client.
        If solution is correct, client is marked as approved.
        :param sock: (ThreadSafeSocket) client socket.
        :param solution: (str) a solution to a captcha.
        :return: (bool) True iff solution is valid for client
        """
        with self.sock_to_solution_lock:
            with self.approval_lock:
                valid = (sock in self.sock_to_solution) and self.sock_to_solution[sock] == solution
                if sock in self.sock_to_solution:
                    self.sock_to_solution.pop(sock)
                if valid:
                    self.approved_sockets.add(sock)
        return valid


    def is_approved(self, sock):
        """
        Returns True iff client has solved at lease 1 captcha since they were
        last returned to be approved by this function.
        :param sock: (ThreadSafeSocket) client socket.
        :return: True iff... (specified above)
        """
        with self.approval_lock:
            valid = sock in self.approved_sockets
            if valid:
                self.approved_sockets.remove(sock)
        return valid
