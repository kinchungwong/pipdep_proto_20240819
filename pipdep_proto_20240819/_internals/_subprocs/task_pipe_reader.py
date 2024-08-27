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
from catchup_reader_20240825.catchup_reader.src.catchup_reader import CatchUpReader


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
    _excs: list[Exception]

    def __init__(self, folder: Path, keep_ends: bool = False) -> None:
        self._fio_folder = folder if folder is not None else Path(tempfile.mkdtemp())
        self._keep_ends = keep_ends
        self._is_closed = False
        self._out_path = self._mkstemp_internal()
        self._err_path = self._mkstemp_internal()
        self._out_reader = CatchUpReader(seekable=True, keepends=keep_ends)
        self._err_reader = CatchUpReader(seekable=True, keepends=keep_ends)
        self._out_text_deque = deque()
        self._err_text_deque = deque()
        self._excs = list[Exception]()

    def mark_closed(self):
        self._is_closed = True

    def catch_up(self):
        if len(self._excs) > 0:
            return
        try:
            self._catch_up_internal(self._out_path, self._out_reader, self._out_text_deque)
            self._catch_up_internal(self._err_path, self._err_reader, self._err_text_deque)
        except Exception as e:
            self._excs.append(e)

    def _catch_up_internal(self, path: Path, reader: CatchUpReader, text_deque: deque[str]):
        if self._is_closed:
            reader.set_writer_as_stopped()
        if path.is_file():
            with path.open("rb") as file:
                reader.read(file)
        else:
            reader.read(None)
        text_deque.extend(reader.readlines())

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

    def get_exceptions(self) -> list[Exception]:
        return self._excs.copy()
