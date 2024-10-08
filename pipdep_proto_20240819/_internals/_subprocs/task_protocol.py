from pathlib import Path
from typing import Protocol, runtime_checkable

@runtime_checkable
class TaskProtocol(Protocol):
    @property
    def out_path(self) -> Path: ...
    @property
    def err_path(self) -> Path: ...
    def set_fio_paths(self, out_path: Path, err_path: Path) -> None: ...
    def run(self) -> None: ...
    def has_exited(self) -> bool: ...
