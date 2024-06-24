import datetime
from app.common.file_manager import FileManager

class LogManager:
    def __init__(self, file_manager: FileManager):
        self.base_dir = "logs"
        self.check_or_create_base_directory(file_manager)

    def check_or_create_base_directory(self, file_manager: FileManager) -> None:
        file_manager.check_or_create_directory(self.base_dir)
    
    def add_log(self, file_manager: FileManager, message: str) -> None:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[I {current_time}]: {message}"
            log_file = f"{self.base_dir}/log.log"
            file_manager.write_to_file(content=f"{message}\n", file_name=log_file, overwrite=False)
            print(message)
        except OSError as e:
            print(f"error: {e}")

    def add_warn(self, file_manager: FileManager, message: str) -> None:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[W {current_time}]: {message}"
            log_file = f"{self.base_dir}/log.log"
            file_manager.write_to_file(content=f"{message}\n", file_name=log_file, overwrite=False)
            print(message)
        except OSError as e:
            print(f"error: {e}")
    
    def add_error(self, file_manager: FileManager, message: str) -> None:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[E {current_time}]: {message}"
            log_file = f"{self.base_dir}/log.log"
            file_manager.write_to_file(content=f"{message}\n", file_name=log_file, overwrite=False)
            print(message)
        except OSError as e:
            print(f"error: {e}")