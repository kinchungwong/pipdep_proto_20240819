import multiprocessing


from pipdep_proto_20240819._internals._subprocs.task_list_executor import TaskListExecutor
from pipdep_proto_20240819._internals._subprocs.shell_task import ShellTask
from pipdep_proto_20240819._internals.utils import print_banner


def main():
    packages = [
        "numpy",
        "opencv-python",
        "opencv-contrib-python",
        "numba",
        "Cython",
        "pandas",
        "requests",
    ]

    ### Currently, running pip install with dry-run option will still cause
    ### the relevant packages, dependencies, and wheels to be downloaded.
    ### These downloads are cached and will be used in subsequent installs.
    ###
    ### https://github.com/pypa/pip/issues/12603
    ###
    ### This is somewhat by design, and somewhat an afterthought.
    ### For future versions of pip, this behavior may change, and the command
    ### arguments should be updated.

    tasks = list[ShellTask]()

    tasks.extend([
        ShellTask(["pip", "install", "--dry-run", "--ignore-installed", package_name])
        for package_name in packages
    ])

    tasks.append(
        ShellTask(["pip", "cache", "dir", "--verbose"])
    )

    tasks.append(
        ShellTask(["pip", "cache", "info", "--verbose"])
    )

    tasks.append(
        ShellTask(["pip", "cache", "list", "--verbose"])
    )

    dry_run_log = list[str]()

    def text_callback(text: str) -> None:
        dry_run_log.append(text)
        print(text)

    ### POOL_SIZE must be 1 because pip install cannot be parallelized 
    ### even in dry-run mode.
    POOL_SIZE = 1
    sleep_secs = 0.5
    tle = TaskListExecutor(tasks, POOL_SIZE, text_callback, sleep_secs)
    print_banner()
    with multiprocessing.Pool(POOL_SIZE) as pool:
        tle.run(pool)
    print_banner()
    
if __name__ == "__main__":
    main()
