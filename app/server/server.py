import threading
import socket
import hashlib
from app.common.constants import CHUNK_SIZE, SERVER_IP, SERVER_PORT, CRLF
from app.common.file_manager import FileManager
from app.common.log_manager import LogManager

class Server:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("server")
        self.log_manager: LogManager | None = LogManager(self.file_manager)
        self.lock: threading.Lock | None = threading.Lock()
        self.log_manager.add_log("Starting server...")
        self.socket: socket.socket | None = self.create_socket()
        self.client_threads = []
        self.client_sockets = {}
        self.chat_sockets = []
        self.main()

    def create_socket(self) -> socket.socket | None:
        server_port = SERVER_PORT
        while True:
            try:
                self.log_manager.add_log(f"Binding socket to {SERVER_IP}:{server_port}...")
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                _socket.bind((SERVER_IP, server_port))
                self.log_manager.add_log(f"Socket bound.")
                return _socket
            except OSError:
                _input = ""
                while _input not in ["y", "n"]:
                    self.log_manager.add_warn(f"Port {server_port} is already in use. Try another port?")
                    _input = input("(y/n): ")
                    if _input == "y":
                        server_port += 1
                        break
                    elif _input == "n":
                        self.log_manager.add_log("Exiting...")
                        exit(0)
                continue
    
    def client_thread_handler(self, client_socket: socket.socket, client_address) -> None:
        while True:
            try:
                data = client_socket.recv(1024)
                if (data == b""): pass

                if (data[:4] == b"EXIT"):
                    self.log_manager.add_log(f"[EXIT request from {client_address[0]}:{client_address[1]}]")
                    self.handle_exit_request(client_socket, client_address)
                    break
                elif (data[:4] == b"FILE"):
                    self.log_manager.add_log(f"[FILE request from {client_address[0]}:{client_address[1]}]: {data.decode()[4:]}")
                    data = data[4:]
                    self.handle_file_request(data.decode(), client_socket)
                elif (data[:4] == b"CHAT"):
                    self.log_manager.add_log(f"[CHAT request fom {client_address[0]}:{client_address[1]}]")
                    self.handle_chat_request(client_socket)
                    pass
                else:
                    response = b"400Invalid request"
                    client_socket.send(response)
                    break
            except Exception as e:
                self.log_manager.add_error(f"Exception occurred: {e}")
                pass

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
                address, port = client_socket.getpeername()
                self.log_manager.add_log(f"[FILE sent to {address}:{port}]: {file_name}")
        except BlockingIOError:
            pass
        except Exception as e:
            status_code = "500"
            message = "Internal server error."
            response = f"{status_code}{message}\r\n"
            client_socket.send(response.encode("utf-8"))

    def handle_chat_request(self, client_socket: socket.socket) -> None:
        response = "200\r\nYou are now in the chat room. Type /exit to leave."
        self.chat_sockets.append(client_socket)
        client_socket.send(response.encode("utf-8"))
        client_socket.setblocking(False)
        message = f"[CHAT {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]} joined the chat]"
        self.log_manager.add_log(message)
        self.lock.acquire()
        for socket in self.chat_sockets:
            if socket != client_socket:
                socket.send(message.encode("utf-8"))
        self.lock.release()
        while True:
            try:
                data = client_socket.recv(1024)
                if data == b"": 
                    pass
                if data[:5] == b"/exit":
                    self.log_manager.add_log(f"[CHAT {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]} left the chat]")
                    self.lock.acquire()
                    for socket in self.chat_sockets:
                        if socket != client_socket:
                            socket.send(f"[CHAT {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]} left the chat]".encode("utf-8"))
                    self.lock.release()
                    client_socket.setblocking(True)
                    break
                message = f"[{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}]: {data.decode()}"
                self.log_manager.add_log(message)
                self.lock.acquire()
                for socket in self.chat_sockets:
                    if socket != client_socket:
                        socket.send(message.encode("utf-8"))
                self.lock.release()
            except BlockingIOError as e:
                pass
            except Exception as e:
                self.log_manager.add_error(f"Exception ocurred: {e}")
        self.chat_sockets.remove(client_socket)
        
    def handle_exit_request(self, client_socket, client_address) -> None:
        client_socket.close()
        self.log_manager.add_log(f"Connection with {client_address[0]}:{client_address[1]} closed.")
        if (client_address in self.client_sockets.keys()):
            del self.client_sockets[client_address]
        current_thread = threading.current_thread()
        self.client_threads.remove(current_thread)
        pass

    def main(self) -> None:
        self.socket.listen(10)
        self.log_manager.add_log(f"Listening on {SERVER_IP}:{self.socket.getsockname()[1]}...")
        while True:
            client_socket, client_address = self.socket.accept()
            self.log_manager.add_log(f"Connection established with {client_address[0]}:{client_address[1]}")
            client_thread = threading.Thread(
                target=self.client_thread_handler,
                args=(client_socket, client_address)
            )
            client_thread.start()
            self.client_threads.append(client_thread)
            self.client_sockets[client_address] = client_socket