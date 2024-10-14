from typing import IO


class LineProcessor:
    def __init__(self, file_name : str):
        self.file_name = file_name
    

    def _file_open(self):
        return open(self.file_name, "r")
    

    def delete_newlines(self) -> list:
        lines = []
        with self._file_open() as file:
            for line in file:
                if len(line) == 0: break

                if len(line) == 1 and '({' not in line: continue

                lines.append(line.strip() + '\n')
            
        return lines
    

    def get_file_name(self):
        return self.file_name
    

    def set_file_name(self, file_name : str):
        self.file_name = file_name
            