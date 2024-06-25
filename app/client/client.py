import threading
import socket
import hashlib
from app.common.file_manager import FileManager
from app.common.log_manager import LogManager
from app.common.constants import \
    CHUNK_SIZE, \
    SERVER_IP, \
    SERVER_PORT, \
    CLIENT_IP, \
    CLIENT_PORT, \
    CRLF

class Client:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("client")
        self.log_manager: LogManager | None = LogManager(self.file_manager)
        self.socket: socket.socket | None = self.create_socket()
        self.lock: threading.Lock | None = threading.Lock()
        self.input_thread: threading.Thread | None = None
        self.chat_mode: bool = False
        self.chat_messages: list[str] = []
        self.running: bool = True
        self.run()

    
    def run(self) -> None:
        try:
            self.socket.connect((SERVER_IP, SERVER_PORT))
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
        except Exception as e:
            print(f"Exception occurred: {e}")
            exit(1)
        # self.socket.set_blocking(False)
        while self.running:
            option = input("What do you want to do?\n1 - Fetch file\n2 - Chat\n3 - Exit\n")
            if option == "1":
                result = self.handle_file()
                while not result:
                    result = self.handle_file()
            elif option == "2":
                self.handle_chat()
            elif option == "3":
                self.handle_exit()
                break
            else:
                print("Invalid option.")
                pass
        
    def create_socket(self) -> socket.socket | None:
        client_port = CLIENT_PORT
        while True:
            try:
                print(f"Binding socket to {CLIENT_IP}:{client_port}...")
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
                _socket.bind((CLIENT_IP, client_port))
                return _socket
            except OSError:
                _input = ""
                while _input not in ["y", "n"]:
                    print(f"Port {client_port} is already in use. Try another port?")
                    _input = input("(y/n): ")
                    if _input == "y":
                        client_port += 1
                        break
                    elif _input == "n":
                        print("Exiting...")
                        exit(0)
                continue

    def handle_file(self) -> bool:
        file_name = input("Enter the file name: ")
        request = f"FILE{file_name}"
        self.socket.send(request.encode("utf-8"))
        data = b""
        file_sha256 = ""
        file_size = 0

        while data != b"EOF":
            data = self.socket.recv(CHUNK_SIZE + 3)
            if data == b"":
                pass
            elif data == b"EOF":
                transferred_file_sha256 = self.file_manager.calculate_sha256(file_name)
                print(f"Transferred file SHA256: {transferred_file_sha256}")
                print(f"Original file SHA256: {file_sha256}")
                if transferred_file_sha256 != file_sha256:
                    print("File transfer failed. SHA256 mismatch.")
                    return False
                if self.file_manager.get_file_size(file_name) != file_size:
                    print("File transfer failed. File size mismatch.")
                    return False
                print("File transfer complete")
                self.socket.send(b"ACK")
            elif data[:3] == b"404":
                print("File not found.")
                break
            elif data[:3] == b"202":
                data = data.decode("utf-8").split(CRLF)
                if data[1] != file_name:
                    self.socket.send(b"NACK")
                    pass
                file_size = int(data[2])
                file_sha256 = data[3]
                self.socket.send(b"ACK")
                self.file_manager.write_to_file("", file_name, True)
            elif data[:3] == b"200":
                print(f"Received chunk of size {len(data[3:])}")
                file_content = data[3:]
                self.file_manager.write_to_file(file_content, file_name, False)
                self.socket.send(b"ACK")

        return True

        
    def handle_chat(self) -> None:
        request = "CHAT"
        self.socket.send(request.encode("utf-8"))
        response = self.socket.recv(60).decode("utf-8").split(CRLF)
        if (response[0] == "200"):
            print(response[1])
            self.chat_mode = True
            self.input_thread = threading.Thread(target=self.input_thread_handler)
            self.input_thread.start()
            self.socket.setblocking(False)
            while self.chat_mode:
                try:
                    if len(self.chat_messages) > 0:
                        message = self.chat_messages.pop(0)
                        self.socket.send(message.encode("utf-8"))
                        if (message == "/exit"):
                            self.lock.acquire()
                            self.chat_mode = False
                            self.socket.setblocking(True)
                            self.lock.release()
                            break
                    data = self.socket.recv(1024)
                    if data == b"":
                        pass
                    else:
                        print(data.decode("utf-8"))
                except BlockingIOError:
                    pass
            
    def handle_request(self) -> None:
        pass

    def handle_exit(self) -> None:
        request = "EXIT"
        self.socket.send(request.encode("utf-8"))
        self.socket.close()
        self.running = False
        print("Exiting...")

    def input_thread_handler(self) -> None:
        while self.chat_mode:
            message = input("")
            self.lock.acquire()
            self.chat_messages.append(message)
            self.lock.release()
            if message == "/exit": 
                break