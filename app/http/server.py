import threading
import socket
import hashlib
import os
from wsgiref import headers
from app.common.constants import CHUNK_SIZE, SERVER_IP, SERVER_PORT, CRLF
from app.common.file_manager import FileManager
from app.common.log_manager import LogManager

class Server:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("http")
        self.log_manager: LogManager | None = LogManager(self.file_manager)
        self.lock: threading.Lock | None = threading.Lock()
        self.log_manager.add_log("Starting server...")
        self.socket: socket.socket | None = self.create_socket()
        self.client_threads = []
        self.client_sockets = {}
        self.main()

    def create_socket(self) -> socket.socket | None:
        server_port = SERVER_PORT
        while True:
            try:
                self.log_manager.add_log(f"Binding socket to {SERVER_IP}:{server_port}...")
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                data = client_socket.recv(CHUNK_SIZE)
                if not data:
                    break
                request = data.decode("utf-8").split("\r\n")[0]
                method = request.split(" ")[0]
                if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT"]:
                    self.send_400_response(client_socket, client_address)
                    break
                if (method != "GET"):
                    self.send_405_response(client_socket, client_address)
                    break
                self.log_manager.add_log(f"{client_address[0]}:{client_address[1]} - {request}")
                self.handle_GET_request(data.decode("utf-8").split("\r\n")[0].split(" ")[1], client_socket, client_address)
            except Exception as e:
                self.log_manager.add_error(f"Exception occurred: {e}")
                pass

    def handle_GET_request(self, data: str, client_socket: socket.socket, client_address) -> None:
        if data.strip() == "/" or data.strip() == "/index.html":
            self.send_index_html(client_socket, client_address)
        elif not data.strip().startswith("/assets") and not data.strip().startswith("/public"):
            self.send_403_response(client_socket, client_address)
        else:
            file_path = f"{self.file_manager.base_directory}{data}"
            if not os.path.exists(file_path):
                self.send_404_response(client_socket, client_address)
            else:
                self.send_file(file_path, client_socket, client_address)

    def send_index_html(self, client_socket: socket.socket, client_address) -> None:
        try:
            with open(f"{self.file_manager.base_directory}/index.html", "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 200 OK\r\n".encode("utf-8")
                headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_log(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket, client_address)
    
    def send_file(self, file_path: str, client_socket: socket.socket, client_address) -> None:
        if file_path.endswith(".html"):
            content_type = "text/html; charset=UTF-8"
        elif file_path.endswith(".css"):
            content_type = "text/css; charset=UTF-8"
        elif file_path.endswith(".js"):
            content_type = "application/javascript; charset=UTF-8"
        elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        elif file_path.endswith(".gif"):
            content_type = "image/gif"
        elif file_path.endswith(".svg"):
            content_type = "image/svg+xml"
        elif file_path.endswith(".ico"):
            content_type = "image/x-icon"
        elif file_path.endswith(".json"):
            content_type = "application/json; charset=UTF-8"
        elif file_path.endswith(".xml"):
            content_type = "application/xml; charset=UTF-8"
        elif file_path.endswith(".txt"):
            content_type = "text/plain; charset=UTF-8"
        else:
            content_type = "application/octet-stream"
        try:
            with open(file_path, "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 200 OK\r\n".encode("utf-8")
                headers = f"Content-Type: {content_type}\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_log(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket)
    
    def send_400_response(self, client_socket: socket.socket, client_address) -> None:
        try:
            with open(f"{self.file_manager.base_directory}/error/400.html", "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 400 Bad Request\r\n".encode("utf-8")
                headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_error(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket)

    def send_403_response(self, client_socket: socket.socket, client_address) -> None:
        try:
            with open(f"{self.file_manager.base_directory}/error/403.html", "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 403 Forbidden\r\n".encode("utf-8")
                headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_error(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket, client_address)

    def send_404_response(self, client_socket: socket.socket, client_address) -> None:
        try:
            with open(f"{self.file_manager.base_directory}/error/404.html", "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 404 Not Found\r\n".encode("utf-8")
                headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_error(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket, client_address)
    
    def send_405_response(self, client_socket: socket.socket, client_address) -> None:
        try:
            with open(f"{self.file_manager.base_directory}/error/405.html", "rb") as file:
                content = file.read()
                length = len(content)
                status_line = "HTTP/1.1 405 Method Not Allowed\r\n".encode("utf-8")
                headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
                response = status_line + headers + content
                client_socket.send(response)
                self.log_manager.add_error(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.send_500_response(client_socket, client_address)
    
    def send_500_response(self, client_socket: socket.socket, client_address) -> None:
        content = b"<!DOCTYPE html><html lang=\"en-us\"><head><meta charset=\"UTF-8\"><title>500 Internal Server Error</title></head><body><h1>500 Internal Server Error</h1><p>Sorry, something went wrong on the server.</p></body></html>"
        length = len(content)
        status_line = "HTTP/1.1 500 Internal Server Error\r\n".encode("utf-8")
        headers = f"Content-Type: text/html; charset=UTF-8\r\nConnection: keep-alive\r\nContent-Length: {length}\r\n\r\n".encode("utf-8")
        response = status_line + headers + content
        try:
            client_socket.send(response)
            self.log_manager.add_error(f"{client_address[0]}:{client_address[1]} - {status_line.decode("utf-8")}")
        except Exception as e:
            self.log_manager.add_error(f"Exception occurred: {e}")
            pass

    def main(self) -> None:
        self.socket.listen()
        self.log_manager.add_log(f"Listening on {SERVER_IP}:{self.socket.getsockname()[1]}...")
        while True:
            client_socket, client_address = self.socket.accept()
            self.log_manager.add_log(f"Connection established with {client_address[0]}:{client_address[1]}")
            
            self.lock.acquire()
            client_thread = threading.Thread(
                target=self.client_thread_handler,
                args=(client_socket, client_address)
            )
            client_thread.start()
            self.lock.release()
            print('started thread')
            self.client_threads.append(client_thread)
            self.client_sockets[client_address] = client_socket
