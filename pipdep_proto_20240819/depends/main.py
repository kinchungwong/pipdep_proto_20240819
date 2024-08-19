from collections.abc import Iterable, Mapping
import json
import os
from os.path import isfile, isdir
from os.path import join as path_join
import pathlib
from pathlib import Path
import pprint

class DependencyGraph:
    source_dir: Path
    json_files: list[Path]
    names: list[str]
    lookup: dict[str, int]
    up_deps: dict[str, set[str]]
    down_deps: dict[str, set[str]]

    def __init__(self, source_dir: str):
        assert isdir(source_dir)
        self.source_dir = Path(source_dir)
        self.json_files = None
        self.names = list[str]()
        self.lookup = dict[str, int]()
        self.up_deps = dict[str, set[str]]()
        self.down_deps = dict[str, set[str]]()
        self._list_json_files()
        self._parse_json_files()
        self._verify()

    def _list_json_files(self):
        self.json_files = list[Path]()
        for entry in self.source_dir.iterdir():
            if entry.is_file() and entry.name.endswith(".json"):
                self.json_files.append(entry)

    def _parse_json_files(self):
        data: Mapping = None
        for json_file in self.json_files:
            with json_file.open() as f:
                data = json.load(f)
            name: str = data["Name"]
            version: str = data["Version"]
            requires: str = data["Requires"]
            required_by: str = data["Required-by"]
            requires = [
                rs 
                for r in requires.split(",")
                for rs in [r.strip()]
                if len(rs) > 0
            ]
            required_by = [
                rb 
                for r in required_by.split(",")
                for rb in [r.strip()]
                if len(rb) > 0
            ]
            self._add_name(name)
            for r in requires:
                self._add_name(r)
            for r in required_by:
                self._add_name(r)
            # print(name, version, requires, required_by)
            if name not in self.up_deps:
                self.up_deps[name] = set[str]()
            self.up_deps[name].update(requires)
            for rb in required_by:
                if rb not in self.down_deps:
                    self.down_deps[rb] = set[str]()
                self.down_deps[rb].update([name])

    def _verify(self):
        names = set(self.up_deps.keys()).union(set(self.down_deps.keys()))
        for name in names:
            dep_up = self.up_deps.get(name, set())
            dep_down = self.down_deps.get(name, set())
            dep_up_compare = [s.lower().replace("-", "").replace("_", "") for s in dep_up]
            dep_down_compare = [s.lower().replace("-", "").replace("_", "") for s in dep_down]
            diffs = set(dep_up_compare).symmetric_difference(set(dep_down_compare))
            if diffs:
                print(f"Error: {name} has different up and down dependencies")
                print(f"  Up: {sorted(dep_up)}")
                print(f"  Down: {sorted(dep_down)}")
                print(f"  Diff: {sorted(diffs)}")

    def _add_name(self, name: str) -> int:
        idx = self.lookup.get(name, -1)
        if idx < 0:
            idx = len(self.names)
            self.names.append(name)
            self.lookup[name] = idx
        return idx

if __name__ == "__main__":
    workspace_dir = os.getcwd()
    source_dir = path_join(workspace_dir, "data/mock/google_colab_python3.10_20240819")
    dg = DependencyGraph(source_dir)
