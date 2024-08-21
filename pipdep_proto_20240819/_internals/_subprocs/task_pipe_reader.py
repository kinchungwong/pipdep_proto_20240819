from collections import deque
from collections.abc import Iterable
import multiprocessing
import multiprocessing.pool
import os
from pathlib import Path
import tempfile
import time


from pipdep_proto_20240819._internals._subprocs.task_protocol import TaskProtocol
from pipdep_proto_20240819._internals._subprocs.pool_protocol import PoolProtocol
from pipdep_proto_20240819._internals._subprocs.catch_up_reader import CatchUpReader


class TaskPipeReader:
    _fio_folder: Path
    _keep_ends: bool
    _is_closed: bool
    _out_path: Path
    _err_path: Path
    _out_reader: CatchUpReader
    _err_reader: CatchUpReader
    _out_text_deque: deque[str]
    _err_text_deque: deque[str]

    def __init__(self, folder: Path, keep_ends: bool = False) -> None:
        self._fio_folder = folder if folder is not None else Path(tempfile.mkdtemp())
        self._keep_ends = keep_ends
        self._is_closed = False
        self._out_path = self._mkstemp_internal()
        self._err_path = self._mkstemp_internal()
        self._out_reader = CatchUpReader()
        self._err_reader = CatchUpReader()
        self._out_text_deque = deque()
        self._err_text_deque = deque()

    def mark_closed(self):
        self._is_closed = True

    def catch_up(self):
        self._catch_up_internal(self._out_path, self._out_reader, self._out_text_deque)
        self._catch_up_internal(self._err_path, self._err_reader, self._err_text_deque)

    def _catch_up_internal(self, path: Path, reader: CatchUpReader, text_deque: deque[str]):
        keep_ends = self._keep_ends
        take_all = self._is_closed
        if not path.is_file():
            return
        reader.catch_up(path)
        for line in reader.produce_lines(take_all=take_all, keep_ends=keep_ends):
            text_deque.append(line)

    def _mkstemp_internal(self) -> Path:
        filehandle, filepath = tempfile.mkstemp(dir=self._fio_folder.as_posix())
        os.close(filehandle)
        return Path(filepath)
    
    def readline_out(self) -> Iterable[str]:
        while len(self._out_text_deque) > 0:
            yield self._out_text_deque.popleft()
        
    def readline_err(self) -> Iterable[str]:
        while len(self._err_text_deque) > 0:
            yield self._err_text_deque.popleft()

    def unlink(self) -> None:
        if self._out_path.is_file():
            self._out_path.unlink()
        if self._err_path.is_file():
            self._err_path.unlink()
