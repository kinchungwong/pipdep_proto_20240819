from collections.abc import Iterable
import json
import multiprocessing
import multiprocessing.pool
from os.path import join as path_join
import pprint
from typing import Optional

from pipdep_proto_20240819._internals.utils import (
    print_banner, 
    make_timestamp_string,
)

from pipdep_proto_20240819._internals.executor_funcs import (
    subprocess_run_with_outtext, 
    multiprocess_map_async_then,
)


def pip_list_installed_packages() -> list[str]:
    args = ["pip", "list"]
    outtext = subprocess_run_with_outtext(args)
    package_names = list[str]()
    for n, line in enumerate(outtext):
        if n >= 2:
            package_names.append(line.split()[0])
    return package_names


def pip_show_installed(package_name: str) -> list[str]:
    args = ["pip", "show", package_name]
    outtext = subprocess_run_with_outtext(args)
    return outtext


def pip_get_installed_props(package_name: str, prop_names: Optional[Iterable[str]]) -> dict[str, str]:
    args = ["pip", "show", package_name]
    outtext = subprocess_run_with_outtext(args)
    prop_names = frozenset(prop_name.lower() for prop_name in prop_names) if prop_names else None
    prop_dict = dict[str, str]()
    for line in outtext:
        if not ":" in line:
            continue
        key = line.split(":", maxsplit=1)[0]
        if " " in key or "\t" in key:
            continue
        if prop_names and key.lower() not in prop_names:
            continue
        value = line[len(key) + 1:].strip()
        prop_dict[key] = value
    return prop_dict


def fn_get_requires(package_name: str) -> dict[str, str]:
    # prop_names = ["name", "requires", "required-by"]
    prop_names = None
    start_time = make_timestamp_string()
    prop_dict = pip_get_installed_props(package_name, prop_names=prop_names)
    stop_time = make_timestamp_string()
    prop_dict["my_timing_start_time"] = start_time
    prop_dict["my_timing_stop_time"] = stop_time
    return prop_dict


def fn_save_to_drive(package_name: str) -> dict[str, str]:
    prop_dict = fn_get_requires(package_name)
    output_dir = "/content/drive/MyDrive/Colab/pipdep/test_only"
    output_file = path_join(output_dir, package_name + ".json")
    with open(output_file, "w") as f:
        json.dump(prop_dict, f, indent=4)
    return prop_dict


if __name__ == "__main__":
    print_banner()
    package_names = pip_list_installed_packages()
    for package_name in package_names:
        print(package_name)
    print_banner()
    with multiprocessing.Pool(8) as pool:
        def fn_success(arg, result): 
            print_banner("-")
            pprint.pprint(result)
        def fn_failure(arg, exc):
            print_banner("-")
            print(f"failed: {arg} {str(exc)}")
        def fn_patience():
            return True
        fn = fn_get_requires
        args = package_names
        multiprocess_map_async_then(pool, fn, args, fn_success, fn_failure, fn_patience, wait_time=1.0)
    print_banner()

