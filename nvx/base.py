"""General variables and functions affecting all devices."""
import ctypes
import os
from .utility import handle_error, is_64bit
from .structs import Version

"""Raw dll for direct calls"""
raw = None
if is_64bit():
    raw = ctypes.cdll.LoadLibrary(os.path.dirname(__file__) + "/dll/x64/Release/NVX136.dll")
else:
    raw = ctypes.cdll.LoadLibrary(os.path.dirname(__file__) + "/dll/x86/Release/NVX136.dll")


def get_dll_version():
    """Get driver dll's version.

    Returns
    -------
    int
        current dll version
    """
    ver = Version()
    handle_error(
        raw.NVXGetVersion(ctypes.c_void_p(None), ctypes.pointer(ver))
    )
    return ver.dll


def set_emulation(state):
    """Enable/disable emulation state.
    Emulation state usually contains 1 device, and is useful for testing.

    Parameters
    ----------
    state : bool
        True if emulation is to be enabled, False otherwise
    """
    handle_error(
        raw.NVXSetEmulation(ctypes.c_uint(state))
    )


def get_count():
    """Count all connected hardware devices.
    You can operate a device by creating a Device with an index in range [0, get_count()).

    Returns
    -------
    int
        device count
    """
    return raw.NVXGetCount()
