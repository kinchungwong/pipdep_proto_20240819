import os
from pathlib import Path


class CatchUpReader:
    _data: bytearray
    _pos: int
    _faulted: bool
    _encoding: str

    def __init__(self) -> None:
        self._data = bytearray()
        self._pos = 0
        self._faulted = False
        self._encoding = "utf-8"

    def catch_up(self, file_path: Path, raise_if_deleted: bool = False) -> None:
        """ Copy new content from the file and append the data to the buffer.

        Arguments:
            file_path: Path
                The file to read from.

        Raises:
            Exception:
                If the file is truncated.
                If the instance is faulted.
        """
        if self._faulted:
            raise Exception("CatchUpReader: faulted.")
        if not file_path.is_file():
            if raise_if_deleted:
                raise Exception(f"CatchUpReader: file {file_path} was deleted.")
            return
        with file_path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            if file_size < self._pos:
                self._faulted = True
                raise Exception(f"CatchUpReader: file {file_path} was truncated from {self._pos} to {file_size}.")
            elif file_size == self._pos:
                return
            f.seek(self._pos)
            new_data = f.read(file_size - self._pos)
            if not new_data:
                return
            self._data.extend(new_data)
            self._pos += len(new_data)

    def produce_lines(self, take_all: bool = False, keep_ends: bool = False) -> list[str]:
        """Take as many delimited lines from the byte array buffer as possible.
        The buffer is updated to remove the taken content.
        
        Arguments:
            take_all: bool = False
                If false (default), content that is not yet delimited is left in the buffer.
                if true, all content is taken, and the byte array buffer is emptied.
            keep_ends: bool = False
                If false (default), the delimiter is not included in the output.
                If true, the delimiter is included in the output.
        """
        if self._faulted:
            raise Exception("CatchUpReader: faulted.")
        cut_idx: int
        if take_all:
            cut_idx = len(self._data)
        else:
            last_n = self._data.rfind(b"\n")
            last_r = self._data.rfind(b"\r")
            last_newline = max(last_n, last_r) ### -1 if neither is found
            cut_idx = last_newline + 1
        if cut_idx == 0:
            return []
        removed_data = self._data[:cut_idx]
        self._data = self._data[cut_idx:]
        raw_lines = removed_data.splitlines(keepends=keep_ends)
        text = [raw_line.decode(self._encoding) for raw_line in raw_lines]
        return text
