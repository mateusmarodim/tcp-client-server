import threading
import socket
import time
from app.common.constants import SERVER_IP, SERVER_PORT
from app.common.file_manager import FileManager
from app.common.log_manager import LogManager

class Server:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("server")
        self.log_manager: LogManager | None = LogManager()
        self.mutex: threading.Lock | None = threading.Lock()
        self.socket: socket.socket | None = self.create_socket()
        print(f"socket: {self.socket}")

    def create_socket(self) -> socket.socket | None:
        while True:
            try:
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                _socket.bind((SERVER_IP, SERVER_PORT))
                raise OSError
                return _socket
            except OSError as e:
                self.log_manager.add_log(self.file_manager, f"Error creating socket: {e}")
                break


