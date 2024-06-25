import os
import hashlib
from typing import Generator
from app.common.constants import CHUNK_SIZE

class FileManager:
    """Abstraction for file manipulations.

    Provides methods to read and write to files and directories present on a given
    base directory.

    Attributes:
        base_directory (str): String containing the path of the base directory.
    """
    def __init__(self, base_suffix: str) -> None:
        _base_directory = f"{os.getcwd()}/app/{base_suffix}"
        if not os.path.exists(_base_directory):
            raise FileNotFoundError()
        
        self.base_directory = _base_directory
    
    def write_to_file(self, content: str, file_name: str, overwrite: bool = False) -> None:
        try:
            if not os.path.exists(f"{self.base_directory}/{file_name}"):
                with open(f"{self.base_directory}/{file_name}", "wb") as file:
                    if type(content) == bytes:
                        file.write(content)
                    elif type(content) == str:
                        file.write(content.encode())
            else:
                if overwrite:
                    with open(f"{self.base_directory}/{file_name}", "wb") as file:
                        if type(content) == bytes:
                            file.write(content)
                        elif type(content) == str:
                            file.write(content.encode())
                else:
                    with open(f"{self.base_directory}/{file_name}", "ab") as file:
                        if type(content) == bytes:
                            file.write(content)
                        elif type(content) == str:
                            file.write(content.encode())
        except OSError as e:
            raise e
    
    def read_from_file(self, file_name: str):
        try:
            file_path = f"{self.base_directory}/{file_name}"
            with open(file_path, "rb") as file:
                yield os.path.getsize(file_path)
                while True:
                    data = file.read(CHUNK_SIZE)
                    if not data:
                        break
                    yield data
        except OSError:
            return False
        
    def check_file_exists(self, file_name: str) -> bool:
        return os.path.exists(f"{self.base_directory}/{file_name}")

    def check_or_create_directory(self, directory_name: str) -> bool:
        try:
            if not os.path.exists(f"{self.base_directory}/{directory_name}"):
                os.mkdir(f"{self.base_directory}/{directory_name}")
            return True
        except Exception:
            return False
        
    def calculate_sha256(self, file_name: str) -> str | bool:
        try:
            sha256_hash = hashlib.sha256()
            file_path = f"{self.base_directory}/{file_name}"
            with open(file_path, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except OSError:
            return False
    
    def get_file_size(self, file_name: str) -> int:
        try:
            return os.path.getsize(f"{self.base_directory}/{file_name}")
        except OSError:
            return 0