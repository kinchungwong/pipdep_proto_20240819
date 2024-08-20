import datetime
from datetime import timezone

UTC = timezone.utc

def print_banner(c: str = "="):
    assert len(c) == 1
    print(c * 80)

def make_timestamp_string() -> str:
    return datetime.datetime.now(UTC).strftime(r"%Y%m%d_%H%M%S_%f")
