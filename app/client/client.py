import threading
import socket
import hashlib
from app.common.file_manager import FileManager
from app.common.constants import \
    CHUNK_SIZE, \
    SERVER_IP, \
    SERVER_PORT, \
    CLIENT_IP, \
    CLIENT_PORT

class Client:
    def __init__(self):
        self.file_manager: FileManager | None = FileManager("client")
        self.socket: socket.socket | None = self.create_socket()
        self.running = True
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
            option = input("What do you want to do?\n1 - Fetch file\n2 - Send message\n3 - Exit\n")
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
                _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                data = data.decode("utf-8").split("\r\n")
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
        response = self.socket.recv(1024).decode("utf-8")

    def handle_request(self) -> None:
        pass

    def handle_exit(self) -> None:
        request = "EXIT"
        self.socket.send(request.encode("utf-8"))
        self.socket.close()
        self.running = False
        print("Exiting...")