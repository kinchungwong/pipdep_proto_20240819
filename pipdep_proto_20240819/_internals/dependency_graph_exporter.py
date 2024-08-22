from collections import deque
from collections.abc import Iterable
from typing import Optional, Union

import graphviz

from pipdep_proto_20240819._internals._graphviz.graphviz_setup import init_graphviz_binpath
from pipdep_proto_20240819._internals.dependency_graph import DependencyGraph


class DependencyGraphExporter:
    """Renders a DependencyGraph into a graphviz.Digraph object.
    """
    _dg: DependencyGraph
    _included_names: list[str]
    _excluded_names: list[str]
    _included: set[int]
    _excluded: set[int]
    _filtered: Optional[set[int]]

    def __init__(
        self, 
        dg: DependencyGraph,
        included: Iterable[Union[int, str]],
        excluded: Iterable[Union[int, str]] = None,
    ) -> None:
        assert isinstance(dg, DependencyGraph)
        self._dg = dg
        self._included_names = []
        self._excluded_names = []
        self._included = set()
        self._excluded = set()
        self._populate_included(included)
        if excluded is not None:
            self._populate_excluded(excluded)
        self._filtered = None

    def export_digraph(self, *args, **kwargs) -> graphviz.Digraph:
        init_graphviz_binpath()
        if self._filtered is None:
            self._build()
        dot = graphviz.Digraph(*args, **kwargs)
        for idx in self._filtered:
            pkinfo = self._dg.installed[idx]
            dot.node(str(idx), pkinfo.name + r"\n" + str(pkinfo.version))
        for idx in self._filtered:
            dep_idx_set = self._dg.deps[idx]
            for dep_idx in dep_idx_set:
                if dep_idx in self._filtered:
                    dot.edge(str(idx), str(dep_idx))
        return dot

    def _validate_items(self, items: Iterable[Union[int, str]]) -> list[Union[int, str]]:
        """Validates the format of all items, and their existence on the
        given DependencyGraph.

        Returns:
            list[Union[int, str]]:
                A list of non-valid items is returned, to assist in error reporting
                and user guidance.
        Note:
            If an item does not match exactly, DependencyReport automatically
            uses search_alike() to list potential matches as part of the error message.
        """
        assert not isinstance(items, str)
        assert isinstance(items, Iterable)
        assert all(isinstance(item, (int, str)) for item in items)
        invalid_items = list[Union[int, str]]()
        for item in items:
            if not self._validate_item(item):
                invalid_items.append(item)
        return invalid_items

    def _validate_item(self, item: Union[int, str]) -> bool:
        if isinstance(item, int):
            return 0 <= item < len(self._dg.installed)
        elif isinstance(item, str):
            return item in self._dg.lookup
        else:
            return False

    def _invalids_summarize_and_raise(self, invalid_items: list[Union[int, str]]) -> None:
        for item in invalid_items:
            print(f"Error: Invalid item: {repr(item)}")
            if isinstance(item, int):
                print("Installed packages are indexed from 0 to", len(self._dg.installed)-1)
            elif isinstance(item, str):
                print("Did you mean:")
                for pkinfo in self._dg.search_alike(item):
                    print(f"    {pkinfo.name} ({pkinfo.version})")
        raise ValueError("Invalid items in included list.")

    def _populate_included(self, included: Iterable[Union[int, str]]) -> None:
        invalid_items = self._validate_items(included)
        if len(invalid_items) > 0:
            self._invalids_summarize_and_raise(invalid_items)
        for item in included:
            assert not isinstance(included, str)
            assert isinstance(included, Iterable)
            assert all(isinstance(item, (int, str)) for item in included)
            name, idx = self._lookup(item)
            self._included_names.append(name)
            self._included.add(idx)

    def _populate_excluded(self, excluded: Iterable[Union[int, str]]) -> None:
        invalid_items = self._validate_items(excluded)
        if len(invalid_items) > 0:
            self._invalids_summarize_and_raise(invalid_items)
        for item in excluded:
            assert not isinstance(excluded, str)
            assert isinstance(excluded, Iterable)
            assert all(isinstance(item, (int, str)) for item in excluded)
            name, idx = self._lookup(item)
            self._excluded_names.append(name)
            self._excluded.add(idx)

    def _lookup(self, key: Union[int, str]) -> tuple[str, int]:
        if isinstance(key, int):
            assert 0 <= key < len(self._dg.installed)
            pkinfo = self._dg.installed[key]
            return pkinfo.name, key
        elif isinstance(key, str):
            assert key in self._dg.lookup
            idx = self._dg.lookup[key]
            pkinfo = self._dg.installed[idx]
            return pkinfo.name, idx
        else:
            raise ValueError(f"Invalid type in lookup: ({type(key)}) {repr(key)}")

    def _build(self) -> None:
        added = set[int](self._included)
        visited = set[int]()
        queue = deque[int](self._included)
        while len(queue) > 0:
            cur_idx = queue.popleft()
            visited.add(cur_idx)
            cur_deps = self._dg.deps[cur_idx]
            for dep_idx in cur_deps:
                if dep_idx in added:
                    continue
                if dep_idx in self._excluded:
                    continue
                added.add(dep_idx)
                queue.append(dep_idx)
        self._filtered = visited
