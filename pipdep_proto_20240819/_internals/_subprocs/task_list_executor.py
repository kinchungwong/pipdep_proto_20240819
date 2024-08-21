import builtins
from collections import deque
from collections.abc import Iterable
import multiprocessing
import multiprocessing.pool
import os
from pathlib import Path
import tempfile
import time
from typing import Callable, Optional


from pipdep_proto_20240819._internals._subprocs.task_protocol import TaskProtocol
from pipdep_proto_20240819._internals._subprocs.pool_protocol import PoolProtocol
from pipdep_proto_20240819._internals._subprocs.task_pipe_reader import TaskPipeReader


class TaskListExecutor:
    """External process execution controller for a fixed list of tasks,
    with concurrent text output handling.
    """
    _pool: PoolProtocol
    _tasks: list[TaskProtocol]
    _fios: list[TaskPipeReader]
    _ar: list[multiprocessing.pool.ApplyResult]
    _max_in_flight: int
    _not_started: deque[int]
    _self_is_running: bool
    _in_flight: set[int]
    _succeeded: set[int]
    _failed: set[int]
    _fio_folder: tempfile.TemporaryDirectory
    _sleep_secs: float
    _text_callback: Callable[[str], None]

    def __init__(
        self, 
        pool: PoolProtocol, 
        tasks: Iterable[TaskProtocol], 
        max_in_flight: int,
        text_callback: Optional[Callable[[str], None]] = None,
        sleep_secs: float=0.1,
    ) -> None:
        """ Initialize the executor with a multiprocessing.Pool, a list of tasks, and the 
        maximum number of tasks to run concurrently.
        """
        assert isinstance(pool, PoolProtocol)
        assert all(isinstance(task, TaskProtocol) for task in tasks)
        assert isinstance(max_in_flight, int) and max_in_flight >= 1
        assert isinstance(sleep_secs, (int, float)) and sleep_secs > 0.0
        self._pool = pool
        self._tasks = list(tasks)
        count = len(self._tasks)
        self._fios = [None] * count
        self._ar = [None] * count
        self._max_in_flight = int(max_in_flight)
        self._not_started = deque(range(count))
        self._self_is_running = False
        self._in_flight = set()
        self._succeeded = set()
        self._failed = set()
        self._fio_folder = tempfile.TemporaryDirectory()
        self._sleep_secs = float(sleep_secs)
        self._text_callback = text_callback or self._text_callback_default

    def run(self):
        if self._self_is_running:
            raise Exception("Already running.")
        self._self_is_running = True
        with self._fio_folder:
            while not self._has_completed():
                self._try_start_more()
                self._process_output()
                time.sleep(self._sleep_secs)
        self._self_is_running = False

    def _try_start_more(self) -> None:
        while self._has_startable() and self._can_start_more():
            idx = self._not_started.popleft()
            task = self._tasks[idx]
            fio = TaskPipeReader(folder=Path(self._fio_folder.name))
            self._fios[idx] = fio
            task.set_fio_paths(fio._out_path, fio._err_path)
            self._ar[idx] = self._pool.apply_async(task.run)
            self._in_flight.add(idx)

    def _process_output(self) -> None:
        if not self._has_in_flight():
            return
        running_set, success_set, failure_set = self._classify_status()
        for idx in self._in_flight:
            fio = self._fios[idx]
            is_stopped = idx not in running_set
            if is_stopped:
                fio.mark_closed()
            fio.catch_up()
            for out_line in fio.readline_out():
                self._text_callback(f"[{idx}] OUT {out_line}")
            for out_line in fio.readline_err():
                self._text_callback(f"[{idx}] ERR {out_line}")
            if is_stopped:
                ### "RUNNING" is not used: contradicts with if(is_stopped).
                msg = "SUCCESS" if idx in success_set else "FAILURE" if idx in failure_set else "RUNNING"
                self._text_callback(f"[{idx}] {msg}")
                fio.unlink()
        self._in_flight = running_set
        self._succeeded.update(success_set)
        self._failed.update(failure_set)

    def _classify_status(self) -> tuple[set[int], set[int], set[int]]:
        running_set = set()
        success_set = set()
        failure_set = set()
        for idx in self._in_flight:
            ar = self._ar[idx]
            if not ar.ready():
                running_set.add(idx)
            elif ar.successful():
                success_set.add(idx)
            else:
                failure_set.add(idx)
        return running_set, success_set, failure_set

    def _has_startable(self) -> bool:
        return len(self._not_started) > 0

    def _can_start_more(self) -> bool:
        return len(self._in_flight) < self._max_in_flight

    def _has_in_flight(self) -> bool:
        return len(self._in_flight) > 0

    def _has_completed(self) -> bool:
        task_count = len(self._tasks)
        success_count = len(self._succeeded)
        failure_count = len(self._failed)
        return success_count + failure_count == task_count

    def _text_callback_default(self, s: str) -> None:
        builtins.print(s)
