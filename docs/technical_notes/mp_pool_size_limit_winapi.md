# Upper limit for multiprocessing pool size on WinAPI for Python 3.12.x and below

For Python < 3.13, on WINAPI platforms, the maximum number of processes
that can be specified in multiprocessing.Pool(processes) is 61.

## Root cause

WinAPI function "WaitForMultipleObjects" supports waiting for at most 64 handles with
a single blocking call. MSDN documentation recommends creating helper threads to deal
with thousands of handles.

A few handles are reserved internally for I/O and robustness reasons, leaving 61 available
for receiving communications from subprocesses.

## Status

The workaround has been implemented in Python development trunk and is slated for release
with Python 3.13, tentatively scheduled for Q4 2024.

### References

  - **BPO-26903** https://bugs.python.org/issue26903
  - **GH-89240** https://github.com/python/cpython/issues/89240
  - **PR-107873** https://github.com/python/cpython/pull/107873
