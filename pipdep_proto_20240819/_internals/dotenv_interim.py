from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from pipdep_proto_20240819._internals.utils import iter_all_lines

###
### Interim quick hack
### All functionalities in this module will be replaced by python-dotenv.
###

def list_dotenv_files() -> list[Path]:
    """Lists all dotenv files in the workspace.

    Remarks:
        This is a quick hack to get it working while waiting for the
        integration with python-dotenv.
    """
    workspace_dir = Path.cwd()
    candidates = [
        workspace_dir / ".env.local",
        workspace_dir / ".env",
    ]
    results = list[str]()
    for candidate in candidates:
        if candidate.is_file():
            results.append(candidate)
    return results


def scan_dotenv_keyname(key: str, dotenv_files: Optional[Iterable[Path]] = None) -> list[tuple[str, tuple[Path, int, str]]]:
    """Scans all dotenv files for the specified key.

    Returns:
        list[tuple[str, tuple[Path, int, str]]]:
            A list of tuples containing the value (str) and the occurrence (tuple).
            The occurrence is a tuple containing the file path (Path), the line number (int),
            and the line content (str).
    """
    if dotenv_files is None:
        dotenv_files = list_dotenv_files()
    results = list[tuple[str, str, Path]]()
    for dotenv_file in dotenv_files:
        for line_idx, cfg_line in enumerate(iter_all_lines(dotenv_file)):
            pos_eq = cfg_line.find("=")
            if pos_eq < 0:
                continue
            left = cfg_line[:pos_eq]
            if left.strip() != key:
                continue
            value = cfg_line[pos_eq + 1:].strip()
            results.append((value, (dotenv_file, line_idx, cfg_line)))
    return results
