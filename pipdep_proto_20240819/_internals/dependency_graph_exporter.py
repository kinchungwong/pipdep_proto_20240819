from collections import deque
from collections.abc import Iterable
from typing import Any, Optional, Union

import graphviz

from pipdep_proto_20240819._internals._graphviz.graphviz_setup import init_graphviz_binpath
from pipdep_proto_20240819._internals.dependency_graph import DependencyGraph
from pipdep_proto_20240819._internals.package_info import PackageInfo
from pipdep_proto_20240819._internals.package_set import PackageSet


class DependencyGraphExporter:
    """Renders a DependencyGraph into a graphviz.Digraph object.
    """
    _dg: DependencyGraph
    _included: PackageSet
    _excluded: Optional[PackageSet]
    _filtered: Optional[PackageSet]

    def __init__(
        self, 
        dg: DependencyGraph,
        included: PackageSet,
        excluded: Optional[PackageSet] = None,
    ) -> None:
        assert isinstance(dg, DependencyGraph)
        assert isinstance(included, PackageSet)
        if excluded is not None:
            assert isinstance(excluded, PackageSet)
            assert excluded._idxs.isdisjoint(included._idxs)
        self._dg = dg
        self._included = included
        self._excluded = excluded
        self._filtered = None

    def export_digraph(self, *args, **kwargs) -> graphviz.Digraph:
        self._ensure_graph_built()
        init_graphviz_binpath()
        dot = graphviz.Digraph(*args, **kwargs)
        filtered = self._filtered
        for pkinfo in filtered:
            assert isinstance(pkinfo, PackageInfo)
            idx = pkinfo._internal_id
            name = pkinfo.name
            s_version = str(pkinfo.version)
            dot.node(str(idx), name + r"\n" + str(s_version))
        for pkinfo in filtered:
            assert isinstance(pkinfo, PackageInfo)
            idx = pkinfo._internal_id
            dep_idx_set = self._dg.deps[idx]
            for dep_idx in dep_idx_set:
                if dep_idx in self._filtered:
                    dot.edge(str(idx), str(dep_idx))
        return dot

    def _ensure_graph_built(self) -> None:
        if self._filtered is not None:
            return
        included = self._included._idxs
        excluded = self._excluded._idxs if self._excluded is not None else set[int]()
        added = set[int](included)
        visited = set[int]()
        queue = deque[int](included)
        while len(queue) > 0:
            cur_idx = queue.popleft()
            visited.add(cur_idx)
            cur_deps = self._dg.deps[cur_idx]
            for dep_idx in cur_deps:
                if dep_idx in added:
                    continue
                if dep_idx in excluded:
                    continue
                added.add(dep_idx)
                queue.append(dep_idx)
        self._filtered = PackageSet()
        self._filtered.add_resolved(self._dg, visited)
