import ctypes
from .bit_view import BitView
from .utility import handle_error
from .base import raw


class ITriggerStatesView:
    """Provides an array-like view to device's input triggers.
    Input triggers cannot be set, thus this class does not have __setitem__.
    """
    def __init__(self, device):
        """Constructor
        Unlike OTriggerStatesView, this class stores a cached version of triggers and not a device to look them up.
        Since input triggers cannot be modified, they can be safely copied in the constructor.

        Parameters
        ----------
        device : device.Device
            NVX device. See device.py
        """
        self.triggers = BitView(ctypes.c_uint(0), 0, 8)  # Observe only bits [0, 8)
        handle_error(raw.NVXGetTriggers(device.device_handle, ctypes.byref(self.triggers.value)))

    def __len__(self):
        return 8

    def __str__(self):
        return str(self.triggers)

    def __getitem__(self, idx):
        """Get a trigger state

        Parameters
        ----------
        idx : int

        Returns
        -------
        bool
            trigger state
        """
        return self.triggers[idx]

    # No __setitem__: input triggers are const


class OTriggerStatesView:
    """Provides an array-like view to device's output triggers.
    Unlike ITriggerStatesView, output triggers can be modified.
    """
    def __init__(self, device):
        """Constructor

        Parameters
        ----------
        device : device.Device
            NVX device. See device.py
        """
        self.device = device

    def __len__(self):
        return 8

    def __str__(self):
        return str(list(self))

    def __getitem__(self, idx):
        """Get a trigger state
        Unfortunately, trigger values cannot be cached, since output triggers can be modified from different instances
        of OTriggerStatesView.

        Parameters
        ----------
        idx : int

        Returns
        -------
        bool
            trigger state
        """
        triggers = BitView(ctypes.c_uint(0), 8, 16)  # Observe only bits [8, 16)
        handle_error(raw.NVXGetTriggers(self.device.device_handle, ctypes.byref(triggers.value)))
        return triggers[idx]

    def __setitem__(self, idx, x):
        """Set an output trigger

        Parameters
        ----------
        idx : int
        x : bool

        Raises
        ------
        IndexError
            if index is not in range [0, 8)
        """
        triggers = BitView(ctypes.c_uint(0), 8, 16)  # Observe only bits [8, 16)
        handle_error(raw.NVXGetTriggers(self.device.device_handle, ctypes.byref(triggers.value)))

        triggers[idx] = x

        handle_error(raw.NVXSetTriggers(self.device.device_handle, triggers.value))


class TriggerStatesView:
    """Provides a view into device's triggers.
    This is a convenience class, provided to access device's triggers in a more pythonic way.
    Triggers can be accessed in 3 ways:
    - triggers['i5'] - access input trigger 5 (or 'o' for output triggers)
    - triggers['input', 5] - for a more verbose version of the previous command
    - triggers.input[5] - using properties <input> and <output> to access or store triggers separately.
    """
    def __init__(self, device):
        self.device = device

    @property
    def input(self):
        """Input triggers of the device. Cannot be modified."""
        return ITriggerStatesView(self.device)

    @property
    def output(self):
        """Output triggers of the device. Can be modified."""
        return OTriggerStatesView(self.device)

    def __len__(self):
        return 16

    def __iter__(self):
        """Returns an iterator to the input+output trigger keys."""
        for i in range(0, 8):
            yield 'i' + str(i)
        for i in range(0, 8):
            yield 'o' + str(i)

    def keys(self):
        """Returns an iterator to the input+output trigger keys."""
        return self.__iter__()

    def values(self):
        """Returns an iterator to the input+output trigger states."""
        for key in self.keys():
            yield self[key]

    def items(self):
        """Returns an iterator to the input+output trigger (keys, values)."""
        for key in self:
            yield (key, self[key])

    def __contains__(self, key):
        """Checks if a trigger with a particular name exists.

        Parameters
        ----------
        key : str or tuple(str, int)
            Trigger key: 'i0' or ('input', 0)
            'i' for input, 'o' for output, followed by an index in range [0, 8)

        Returns
        -------
        bool
            True, if this trigger exists, False otherwise
        """
        try:
            self._unpack_key(key)
        except (KeyError, IndexError, TypeError):
            return False
        return True

    def _unpack_key(self, key):
        """Converts index, passed to __getitem__ or __setitem__, to a more workable format. Handles any errors.

        Parameters
        ----------
        key : str or tuple(str, int)
            Trigger key: 'i0' or ('input', 0)
            'i' for input, 'o' for output, followed by an index in range [0, 8)

        Raises
        ------
        TypeError
            if key is not a tuple or a string
        KeyError
            if the key-part (input/output) is not recognised
        IndexError
            if the key-part was recognised, but the index-part was not recognised or incorrect.
        """
        is_output = False
        index = 0

        if isinstance(key, str):
            if (len(key) != 2) or (key[0] not in "io") or (not key[1].isdigit()):
                raise KeyError("Expected a correctly formatted key, got " + key +
                               " (see the docs on TriggerStatesView.__getitem__ for proper indexing)")

            index = int(key[1])

            if index >= 8:
                raise IndexError("Expected a trigger index 0-7, got " + key[1])

            if key[0] == 'o':
                is_output = True
        elif isinstance(key, tuple):
            if len(key) != 2:
                raise KeyError("Expected a correctly formatted key, got (" + repr(key) +
                               " (see the docs on TriggerStatesView.__getitem__ for proper indexing)")

            extracted_key, extracted_idx = key

            if extracted_key not in ["input", "output"]:
                raise KeyError("Expected a correctly formatted key, got (" +
                               str(extracted_key) + ", " +
                               str(extracted_idx) +
                               ") (see the docs on TriggerStatesView.__getitem__ for proper indexing)")

            if extracted_idx < 0 or extracted_idx >= 8:
                raise IndexError("Expected a trigger index 0-7, got " + str(extracted_idx))
            index = extracted_idx

            if extracted_key[0] == 'o':
                is_output = True
        else:
            raise TypeError("Expected a correctly formatted index, got " + repr(key) +
                            " (see the docs on TriggerStatesView.__getitem__ for proper indexing)")

        return is_output, index

    def __getitem__(self, key):
        """Return a trigger state.

        Parameters
        ----------
        key : str or tuple
            A string containing index of format 'i1' or 'o5' (i for input, o for output, followed by an index), or
            a tag ('input', 'output') and an index [0, 8).

        Returns
        -------
        bool
            Requested trigger's state
        """
        is_output, index = self._unpack_key(key)

        if is_output:
            return self.output[index]
        else:
            return self.input[index]

    def __setitem__(self, key, value):
        """Set a trigger state.
        Keys follow the same syntax as in __getitem__, but note that input triggers cannot be set, and
        KeyError will be raised if you try.

        Parameters
        ----------
        key : str or tuple
            A string containing index of format 'i1' or 'o5' (i for input, o for output, followed by an index), or
            a tag ('input', 'output') and an index [0, 8).
        value : bool
            Value to set.
        """
        is_output, index = self._unpack_key(key)

        if is_output:
            self.output[index] = value
        else:
            raise KeyError("Cannot set input triggers")

    def __str__(self):
        return str(dict(self))
