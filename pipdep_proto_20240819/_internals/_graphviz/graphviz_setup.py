import os
from pathlib import Path
from typing import Optional

from pipdep_proto_20240819._internals.dotenv_interim import scan_dotenv_keyname

def find_graphviz_binpath() -> Optional[Path]:
    for value, (source, line_idx, line) in scan_dotenv_keyname("GRAPHVIZ_BINPATH"):
        if len(value) == 0:
            continue
        candidate_path = Path(value)
        ### TODO make this more cross-platform.
        candidate_dot_paths = [
            candidate_path / "dot",
            candidate_path / "dot.exe",
        ]
        if candidate_path.is_dir() and any(dot_path.is_file() for dot_path in candidate_dot_paths):
            return candidate_path
        else:
            print(f"GRAPHVIZ_BINPATH value '{value}' is invalid; skipped. (From: {source}, line: {line_idx + 1})")
    return None

def init_graphviz_binpath(once_only: bool = True) -> None:
    if once_only:
        if hasattr(init_graphviz_binpath, "_once_only_has_executed"):
            return
    setattr(init_graphviz_binpath, "_once_only_has_executed", True)
    graphviz_binpath = find_graphviz_binpath()
    if graphviz_binpath is not None:
        ### TODO implement cross-platform support.
        ###      Separator for environment PATH is ';' on Windows and ':' on POSIX.
        ###      However, Python's os.pathsep is not correct for Windows.
        orig_path = os.environ["PATH"]
        path_to_add = os.path.abspath(graphviz_binpath)
        if path_to_add not in orig_path:
            new_path = path_to_add + ";" + orig_path
            os.environ["PATH"] = new_path
    else:
        ### TODO verify graphviz binaries accessible on PATH.
        ###      If not, raise an exception.
        pass
