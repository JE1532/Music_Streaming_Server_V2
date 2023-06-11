from threading import Lock


class CaptchaManager:
    def __init__(self):
        self.sock_to_solution = dict()
        self.sock_to_solution_lock = Lock()
        self.approved_sockets = set()
        self.approval_lock = Lock()


    def register_captcha(self, sock, solution):
        with self.sock_to_solution_lock:
            self.sock_to_solution[sock] = solution


    def validate_solution(self, sock, solution):
        with self.sock_to_solution_lock:
            with self.approval_lock:
                valid = (sock in self.sock_to_solution) and self.sock_to_solution[sock] == solution
                if sock in self.sock_to_solution:
                    self.sock_to_solution.pop(sock)
                if valid:
                    self.approved_sockets.add(sock)
        return valid


    def is_approved(self, sock):
        with self.approval_lock:
            valid = sock in self.approved_sockets
            if valid:
                self.approved_sockets.remove(sock)
        return valid
