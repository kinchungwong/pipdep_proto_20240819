import collections.abc
from collections.abc import Iterable, Mapping
import datetime
from datetime import timezone
import json
import multiprocessing
import multiprocessing.pool
import os
from os.path import isfile, isdir
from os.path import join as path_join
import pprint
from queue import Queue
import shutil
import subprocess
import sys
import tempfile
import time
import typing
from typing import Any, Callable, Optional, Union

UTC = timezone.utc


def subprocess_run_with_outtext(args: Iterable[str]) -> list[str]:
    returncode: int
    text: Iterable[str] = []
    tmp_fd, tmp_name = tempfile.mkstemp(text=True)
    try:
        tmp_file = os.fdopen(tmp_fd, "w+")
        subp_result = subprocess.run(args, stderr=subprocess.STDOUT, stdout=tmp_file)
        returncode = subp_result.returncode
        if returncode == 0:
            tmp_file.seek(0)
            text = tmp_file.readlines()
    finally:
        tmp_file.close()
        try:
            os.remove(tmp_name)
        except:
            pass
        pass
    if returncode != 0:
        raise Exception(f"command {args} failed with code {returncode}.")
    return [line.rstrip("\n") for line in text]


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


def make_timestamp_string() -> str:
    return datetime.datetime.now(UTC).strftime(r"%Y%m%d_%H%M%S_%f")


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


def print_banner(c: str = "="):
    assert len(c) == 1
    print(c * 80)


def multiprocess_map_async_then(
    pool: Any, 
    fn: Callable, 
    args: Iterable, 
    fn_success: Callable, 
    fn_failure: Callable,
    fn_patience: Callable,
    wait_time: float=1.0,
) -> None:
    pool_apply_async = pool.apply_async
    count = len(args)
    args = list(args)
    async_results: list[multiprocessing.pool.ApplyResult] = [None] * count
    for idx, arg in enumerate(args):
        if not isinstance(arg, tuple):
            arg = (arg,)
        async_results[idx] = pool_apply_async(fn, args=arg)
    idx_pending = set[int](range(count))
    while len(idx_pending) > 0 and fn_patience():
        new_idx_outcomes = list[tuple[int, bool]]()
        for idx in idx_pending:
            async_result = async_results[idx]
            if not async_result.ready():
                continue
            outcome = async_result.successful()
            new_idx_outcomes.append((idx, outcome))
        for idx, outcome in new_idx_outcomes:
            if outcome:
                fn_success(args[idx], async_results[idx].get())
            else:
                async_result = async_results[idx]
                try:
                    exc = async_result.get()
                except Exception as exc:
                    fn_failure(args[idx], exc)
            idx_pending.remove(idx)
        time.sleep(wait_time)


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

