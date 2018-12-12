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


def set_bit(v, index, x):
    """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value"""
    mask = 1 << index   # Compute mask, an integer with just bit 'index' set.
    v &= ~mask          # Clear the bit indicated by the mask (if x is False)
    if x:
        v |= mask         # If x was True, set the bit indicated by the mask.
    return v            # Return the result, we're done.


def is_64bit():
    return sys.maxsize > 2 ** 32
