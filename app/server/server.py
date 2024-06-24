import threading
import socket
import hashlib
from app.common.constants import CHUNK_SIZE, SERVER_IP, SERVER_PORT
from app.common.file_manager import FileManager
from app.common.log_manager import LogManager

CRLF = "\r\n"

class Server:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("server")
        self.log_manager: LogManager | None = LogManager(self.file_manager)
        self.lock: threading.Lock | None = threading.Lock()
        self.log_manager.add_log(self.file_manager, "Starting server...")
        self.socket: socket.socket | None = self.create_socket()
        self.client_threads = []
        self.client_sockets = {}
        self.main_thread = threading.Thread(target=self.main_thread)
        self.main_thread.start()

    def create_socket(self) -> socket.socket | None:
        server_port = SERVER_PORT
        while True:
            try:
                self.log_manager.add_log(self.file_manager, f"Binding socket to {SERVER_IP}:{server_port}...")
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                _socket.bind((SERVER_IP, server_port))
                self.log_manager.add_log(self.file_manager, f"Socket bound.")
                return _socket
            except OSError:
                _input = ""
                while _input not in ["y", "n"]:
                    self.log_manager.add_warn(self.file_manager, f"Port {server_port} is already in use. Try another port?")
                    _input = input("(y/n): ")
                    if _input == "y":
                        server_port += 1
                        break
                    elif _input == "n":
                        self.log_manager.add_log(self.file_manager, "Exiting...")
                        exit(0)
                continue
    
    def main_thread(self) -> None:
        self.socket.listen(10)
        self.log_manager.add_log(self.file_manager, f"Listening on {SERVER_IP}:{self.socket.getsockname()[1]}...")
        while True:
            client_socket, client_address = self.socket.accept()
            self.log_manager.add_log(self.file_manager, f"Connection established with {client_address[0]}:{client_address[1]}")
            client_thread = threading.Thread(
                target=self.client_thread_handler,
                args=(client_socket, client_address)
            )
            client_thread.start()
            self.client_threads.append(client_thread)
            self.client_sockets[client_address] = client_socket

    def client_thread_handler(self, client_socket: socket.socket, client_address) -> None:
        # client_socket.setblocking(False)
        while True:
            try:
                data = client_socket.recv(1024)
                if (data == b""): pass
                self.log_manager.add_log(self.file_manager, f"Received request from {client_address[0]}:{client_address[1]}: {data.decode()}")

                if (data[:4] == b"EXIT"):
                    ## TODO: implement exit
                    break
                elif (data[:4] == b"FILE"):
                    data = data[4:]
                    self.handle_file_request(data.decode(), client_socket)
                elif (data[:4] == b"CHAT"):
                    ## TODO: implement chat
                    pass
                else:
                    response = b"400Invalid request"
                    client_socket.send(response)
                    break
            except Exception as e:
                self.log_manager.add_error(self.file_manager, f"Exception occurred: {e}")
                pass
        client_socket.close()
        self.log_manager.add_log(self.file_manager, f"Connection with {client_address[0]}:{client_address[1]} closed.")
        if (client_address in self.client_sockets.keys()):
            del self.client_sockets[client_address]
        current_thread = threading.current_thread()
        self.client_threads.remove(current_thread)

    def handle_file_request(self, file_name: str, client_socket: socket.socket) -> None:
        try:
            file_generator = self.file_manager.read_from_file(file_name)
            file_size = next(file_generator)
            if not file_size:
                status_code = "404"
                message = "File not found."
                response = status_code + CRLF + \
                           message
                client_socket.send(response.encode("utf-8"))
            else:
                status_code = "202"
                file_hash = self.file_manager.calculate_sha256(file_name)
                response = status_code + CRLF + \
                           file_name + CRLF + \
                           str(file_size) + CRLF + \
                           str(file_hash)
                client_response = b""
                client_socket.send(response.encode("utf-8"))
                while client_response != b"ACK":
                    client_response = client_socket.recv(1024)
                client_response = b""

                for chunk in file_generator:
                    status_code = "200"
                    response = status_code.encode("utf-8") + chunk
                    client_response = b""
                    while client_response != b"ACK":
                        client_socket.send(response)
                        client_response = client_socket.recv(1024)
                client_response = b""
                while client_response != b"ACK":
                    client_socket.send(b"EOF")
                    client_response = client_socket.recv(1024)
        except Exception as e:
            status_code = "500"
            message = "Internal server error."
            response = f"{status_code}{message}\r\n"
            client_socket.send(response.encode("utf-8"))

    def handle_chat_request(self, data: str, client_socket: socket.socket) -> None:
        message = f"{str(client_socket.getpeername())}: {data}"
        self.log_manager.add_log(self.file_manager, message)
        pass

    def handle_exit_request(self, client_socket: socket.socket) -> None:
        pass