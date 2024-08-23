from collections.abc import Collection, Iterable
from typing import Any, Union, overload

from pipdep_proto_20240819._internals.dependency_graph import DependencyGraph
from pipdep_proto_20240819._internals.package_info import PackageInfo


class PackageSet(Collection[PackageInfo]):
    _infos: list[PackageInfo]
    _idxs: set[int]

    def __init__(self) -> None:
        self._infos = list[PackageInfo]()
        self._idxs = set[int]()

    def add(self, pkinfo: PackageInfo) -> None:
        if pkinfo._internal_id in self._idxs:
            return
        self._infos.append(pkinfo)
        self._idxs.add(pkinfo._internal_id)

    def add_resolved(
        self,
        dg: DependencyGraph,
        items: Union[int, str, PackageInfo, Iterable[int], Iterable[str], Iterable[PackageInfo], Iterable[Union[int, str, PackageInfo]]],
    ) -> None:
        assert isinstance(dg, DependencyGraph)
        assert items is not None
        if isinstance(items, (int, str, PackageInfo)):
            items = [items]
        else:
            assert isinstance(items, Iterable)
            assert all(isinstance(item, (int, str, PackageInfo)) for item in items)
        dg_count = len(dg.installed)
        invalid_items = list[Any]()
        for item in items:
            if isinstance(item, PackageInfo):
                self.add(item)
            elif isinstance(item, int):
                if 0 <= item < dg_count:
                    self.add(dg.installed[item])
                else:
                    invalid_items.append(item)
            elif isinstance(item, str):
                if item in dg.lookup:
                    self.add(dg.installed[dg.lookup[item]])
                else:
                    invalid_items.append(item)
            else:
                invalid_items.append(item)
        if invalid_items:
            for item in invalid_items:
                if isinstance(item, int):
                    print(f"Error: Invalid item: {repr(item)}")
                    print("    Installed packages are indexed from 0 to", (dg_count - 1))
                elif isinstance(item, str):
                    alikes = dg.search_alike(item)
                    if len(alikes) >= 1:
                        print(f"Error: Ambiguous item: {repr(item)}")
                        print("    Did you mean:")
                        for pkinfo in alikes:
                            print(f"        {pkinfo.name} ({pkinfo.version})")
                    else:
                        print(f"Error: Invalid item: {repr(item)}")
                        print("    No installed package matches the pattern.")
            raise ValueError(f"Invalid items: {invalid_items}")

    def __len__(self) -> int:
        return len(self._idxs)

    @overload
    def __contains__(self, item: int) -> bool: ...
    @overload
    def __contains__(self, item: str) -> bool: ...
    @overload
    def __contains__(self, item: PackageInfo) -> bool: ...

    def __contains__(self, item: Union[int, str, PackageInfo]) -> bool:
        if isinstance(item, int):
            return item in self._idxs
        elif isinstance(item, str):
            return any(item in pkinfo.aliases for pkinfo in self._infos)
        elif isinstance(item, PackageInfo):
            return item._internal_id in self._idxs
        else:
            return False

    def __iter__(self) -> Iterable[PackageInfo]:
        yield from self._infos
