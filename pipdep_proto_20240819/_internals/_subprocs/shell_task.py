from collections.abc import Iterable
import io
from pathlib import Path
import subprocess
from typing import Optional

from pipdep_proto_20240819._internals._subprocs.task_protocol import TaskProtocol

class ShellTask(TaskProtocol):
    _args: Iterable[str]
    _out_path: Optional[Path]
    _err_path: Optional[Path]
    _out_pyfio: Optional[io.BufferedRandom]
    _err_pyfio: Optional[io.BufferedRandom]
    _returncode: Optional[int]

    def __init__(
        self,
        args: Iterable[str],
    ):
        assert not isinstance(args, str)
        assert isinstance(args, Iterable)
        assert all(isinstance(arg, str) for arg in args)
        self._args = list(args)
        self._out_path = None
        self._err_path = None
        self._out_pyfio = None
        self._err_pyfio = None
        self._returncode = None
    
    def set_fio_paths(self, out_path: Path, err_path: Path) -> None:
        if self._out_path is not None:
            raise Exception("out_path already set.")
        if self._err_path is not None:
            raise Exception("err_path already set.")
        assert isinstance(out_path, Path)
        assert isinstance(err_path, Path)
        self._out_path = out_path
        self._err_path = err_path

    def run(self):
        if self._out_path is None:
            raise Exception("out_path not set.")
        if self._err_path is None:
            raise Exception("err_path not set.")
        self._out_pyfio = self._out_path.open("wb+")
        self._err_pyfio = self._err_path.open("wb+")
        try:
            subp_result = subprocess.run(
                self._args,
                stderr=self._err_pyfio,
                stdout=self._out_pyfio,
            )
            self._returncode = subp_result.returncode
        finally:
            self._out_pyfio.close()
            self._err_pyfio.close()
            self._out_pyfio = None
            self._err_pyfio = None
        pass

    def has_exited(self) -> bool:
        return self._returncode is not None

    @property
    def out_path(self) -> Optional[Path]:
        return self._out_path
    
    @property
    def err_path(self) -> Optional[Path]:
        return self._err_path
