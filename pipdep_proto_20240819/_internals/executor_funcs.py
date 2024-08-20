from collections.abc import Iterable
import multiprocessing
import multiprocessing.pool
import os
import subprocess
import tempfile
import time
from typing import Any, Callable


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
