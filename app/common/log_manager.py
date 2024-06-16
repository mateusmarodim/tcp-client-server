import datetime
from app.common.file_manager import FileManager

class LogManager:
    def __init__(self):
        self.base_url = "logs"
        self.start_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    
    def add_log(self, file_manager: FileManager, message: str) -> None:
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{current_time}: {message}"
            log_file = f"{self.base_url}\{self.start_datetime}.log"
            file_manager.write_to_file(content=message, file_name=log_file)
            print(message)
        except OSError as e:
            print(f"error: {e}")
