import os

class FileManager:
    """Abstraction for file manipulations.

    Provides methods to read and write to files and directories present on a given
    base directory.

    Attributes:
        base_directory (str): String containing the path of the base directory.
    """
    def __init__(self, base_suffix: str) -> None:
        _base_directory = f"{os.getcwd()}\\app\{base_suffix}"
        print(f"base_directory: {_base_directory}")
        if not os.path.exists(_base_directory):
            raise FileNotFoundError()
        
        self.base_directory = _base_directory
    
    def write_to_file(self, content: str, file_name: str, overwrite: bool = False) -> None:
        try:
            if overwrite:
                with open(f"{self.base_directory}\{file_name}", "wb") as file:
                    file.write(content.encode())
            else:
                with open(f"{self.base_directory}\{file_name}", "ab") as file:
                    file.write(content.encode())
        except OSError as e:
            raise e
    
    def read_from_file(self, file_name: str) -> bytes:
        try:
            with open(f"{self.base_directory}\{file_name}", "rb") as file:
                return file.read()
        except OSError as e:
            raise e