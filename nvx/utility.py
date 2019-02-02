import sys


def handle_error(error_code):
    if error_code == -1:
        raise RuntimeError("invalid handle (such handle not present now)")
    if error_code == -2:
        raise RuntimeError("invalid function parameter(s)")
    if error_code == -3:
        raise RuntimeError("function fail (internal error)")
    if error_code == -4:
        raise RuntimeError("data rate error")


def is_64bit():
    return sys.maxsize > 2 ** 32
