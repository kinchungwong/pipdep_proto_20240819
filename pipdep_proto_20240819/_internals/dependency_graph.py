from collections.abc import Mapping
import json
from os.path import isdir
from pathlib import Path
from typing import Optional, Union

from pipdep_proto_20240819._internals.package_info import PackageInfo

class DependencyGraph:
    """
        installed: list[PackageInfo]
            List of installed packages.
        lookup: dict[str, int]
            Lookup table for package names and aliases. Each is mapped into the index
            on the installed list.
        deps: dict[int, set[int]]
            Dependency graph. The key is the index of the package on the installed list.
            The value is the set of indices of the dependent packages.
    """
    source_dir: Path
    json_files: list[Path]
    installed: list[PackageInfo]
    lookup: dict[str, int]
    deps: dict[int, set[int]]

    def __init__(self, source_dir: Union[Path, str]):
        if not isinstance(source_dir, Path):
            source_dir = Path(source_dir)
        assert source_dir.is_dir()
        self.source_dir = source_dir
        self.json_files = None
        self.installed = list[PackageInfo]()
        self.lookup = dict[str, int]()
        self.deps = dict[int, set[int]]()
        self._list_json_files()
        self._parse_json_files()
        self._compute_dependencies()

    def search_alike(self, pattern: str) -> list[PackageInfo]:
        patterns = self._normalize_name(pattern).split("_")
        idx_matches = set[int]()
        for lookup_name, idx in self.lookup.items():
            if all((sub_pattern in lookup_name) for sub_pattern in patterns):
                idx_matches.add(idx)
        return [
            self.installed[idx] for idx in sorted(idx_matches)
        ]

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
            pkinfo = self._add_or_get_package(name)
            pkinfo.version = data["Version"]
            pkinfo.dependencies = self._split_comma(data.get("Requires", ""))

    def _compute_dependencies(self):
        for pkinfo in self.installed:
            idx = pkinfo._internal_id
            self.deps[idx] = set()
            for dep_name in pkinfo.dependencies:
                dep_pkinfo = self._try_get_package(dep_name)
                if dep_pkinfo is None:
                    print(f"Warning: {pkinfo.name} depends on {dep_name}, but it is not installed")
                    continue
                dep_idx = dep_pkinfo._internal_id
                self.deps[idx].add(dep_idx)

    def _try_get_package(self, name: str) -> Optional[PackageInfo]:
        n_name = self._normalize_name(name)
        idx = self.lookup.get(n_name, -1)
        if idx >= 0:
            return self.installed[idx]
        return None

    def _add_or_get_package(self, name: str) -> PackageInfo:
        n_name = self._normalize_name(name)
        idx = self.lookup.get(n_name, -1)
        if idx >= 0:
            pkinfo = self.installed[idx]
            assert pkinfo._internal_id == idx
            pkinfo.aliases.add(name)
            return pkinfo
        idx = len(self.installed)
        pkinfo = PackageInfo(name)
        pkinfo._internal_id = idx
        self.installed.append(pkinfo)
        self.lookup[n_name] = idx
        pkinfo.aliases.add(n_name)
        if name != n_name:
            self.lookup[name] = idx
            pkinfo.aliases.add(name)
        return pkinfo

    def _normalize_name(self, name: str) -> str:
        return "".join(
            c if c.isalnum() else "_" for c in name.lower()
        )
    
    def _split_comma(self, comma_str: str) -> list[str]:
        result = list[str]()
        for item in comma_str.split(","):
            item_strip = item.strip()
            if len(item_strip) == 0:
                continue
            result.append(item_strip)
        return result
