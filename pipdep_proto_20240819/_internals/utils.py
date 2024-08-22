from collections.abc import Iterable
import datetime
from datetime import timezone
from pathlib import Path
from typing import Union

UTC = timezone.utc

def print_banner(c: str = "="):
    assert len(c) == 1
    print(c * 80)

def make_timestamp_string() -> str:
    return datetime.datetime.now(UTC).strftime(r"%Y%m%d_%H%M%S_%f")

def iter_all_lines(file_path: Union[str, Path]) -> Iterable[str]:
    with file_path.open("r") as f:
        for line in f:
            yield line.strip()
