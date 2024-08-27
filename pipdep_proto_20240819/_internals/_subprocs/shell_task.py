from collections.abc import Iterable
import io
from pathlib import Path
import subprocess
from typing import NewType, Optional, Union, TypeAlias

from pipdep_proto_20240819._internals._subprocs.task_protocol import TaskProtocol

ShellTaskReturnCode = int

class ShellTask(TaskProtocol):
    _args: Iterable[str]
    _out_path: Optional[Path]
    _err_path: Optional[Path]
    _outcome: Union[None, ShellTaskReturnCode, Exception]

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
        self._outcome = None

    def set_fio_paths(self, out_path: Path, err_path: Path) -> None:
        if self._out_path is not None:
            raise Exception("out_path already set.")
        if self._err_path is not None:
            raise Exception("err_path already set.")
        assert isinstance(out_path, Path)
        assert isinstance(err_path, Path)
        self._out_path = out_path
        self._err_path = err_path

    def run(self) -> Union[ShellTaskReturnCode, Exception]:
        if self._out_path is None:
            raise Exception("out_path not set.")
        if self._err_path is None:
            raise Exception("err_path not set.")
        try:
            with self._out_path.open("wb+") as _out_pyfio:
                with self._err_path.open("wb+") as _err_pyfio:
                    subp_result = subprocess.run(
                        self._args,
                        stderr=_err_pyfio,
                        stdout=_out_pyfio,
                    )
                    self._outcome = ShellTaskReturnCode(subp_result.returncode)
        except Exception as e:
            self._outcome = e
        return self._outcome

    def has_exited(self) -> bool:
        return self._outcome is not None

    @property
    def out_path(self) -> Optional[Path]:
        return self._out_path

    @property
    def err_path(self) -> Optional[Path]:
        return self._err_path
