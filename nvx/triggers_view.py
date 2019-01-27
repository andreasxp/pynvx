import ctypes
from .utility import handle_error
from .base import raw


class ConstBitView:
    """Provide array-like access to bits, folded into a ctypes value. No modification is allowed."""
    def __init__(self, value=ctypes.c_uint(0), begin=0, end=None):
        """Constructor
        Assigns value as a source of bits, with optional begin and end to limit bit visibility.

        Parameters
        ----------
        value : ctypes.c_uint or a similar raw integer type
            Raw value from which to extract bits from
        begin : int
            Which bit (count from lowest) to consider first
        end : int
            Which bit (count from lowest) to consider AFTER last. Ex.: for range [0, 8) end = 8
            None (default) is equivalent to ctypes.sizeof(value)*8
        """
        if end is None:
            end = ctypes.sizeof(value)*8

        if end - begin <= 0 or end - begin > ctypes.sizeof(value)*8:
            raise ValueError(
                "Invalid range. end - begin must be in range [1, 32], got " +
                str(end) + " - " + str(begin) + " = " + str(end - begin))

        self.value = value
        self.begin = begin
        self.end = end

    def __len__(self):
        return self.end - self.begin

    def __str__(self):
        string = "["
        for i in range(0, len(self)-1):
            string += self[i]
            string += ", "
        string += self[len(self)-1]
        string += "]"

    def __getitem__(self, index):
        """Extract a bit

        Parameters
        ----------
        index : int

        Returns
        -------
        bool
            extracted bit

        Raises
        ------
        IndexError
            if index is not in range [0, len(self))
        """
        if index < 0 or index >= len(self):
            raise IndexError("Index (" + str(index) + ") not in range [0, " + str(len(self)) + ")")

        return bool(self.value.value & (1 << (self.begin + index)))


class BitView(ConstBitView):
    """Provide array-like access to bits, folded into a ctypes value."""
    def __init__(self, value=ctypes.c_uint(0), begin=0, end=None):
        """Constructor
        Assigns value as a source of bits, with optional begin and end to limit bit visibility.

        Parameters
        ----------
        value : ctypes.c_uint or a similar raw integer type
            Raw value from which to extract bits from
        begin : int
            Which bit (count from lowest) to consider first
        end : int
            Which bit (count from lowest) to consider AFTER last. Ex.: for range [0, 8) end = 8
            None (default) is equivalent to ctypes.sizeof(value)*8
        """
        super().__init__(value, begin, end)

        if end is None:
            end = ctypes.sizeof(value) * 8

        if end - begin <= 0 or end - begin > ctypes.sizeof(value) * 8:
            raise ValueError(
                "Invalid range. end - begin must be in range [1, 32], got " +
                str(end) + " - " + str(begin) + " = " + str(end - begin))

        self.value = value
        self.begin = begin
        self.end = end

    def __setitem__(self, index, x):
        """Set a bit to value (True or False)

        Parameters
        ----------
        index : int
        x : bool

        Raises
        ------
        IndexError
            if index is not in range [0, len(self))
        """
        if index < 0 or index >= len(self):
            raise IndexError("Index (" + str(index) + ") not in range [0, " + str(len(self)) + ")")

        self.value.value &= ~(1 << self.begin + index)  # Clear target bit
        self.value.value |=  (x << self.begin + index)  # Set target bit to x


class InputTriggersView(ConstBitView):
    """Provides an array-like view to device's input triggers.
    Input triggers cannot be set, thus this class does not have __setitem__.
    """
    def __init__(self, raw_device):
        """Constructor
        Unlike OutputTriggersView, it's technically possible to construct this class without a device,
        because since you can't set an input trigger, this class is basically equivalent to ConstBitView.
        This constructor is provided for convenience, and to make this class more similar to OutputTriggersView.

        Parameters
        ----------
        raw_device : ctypes.c_void_p
            Raw pointer to the device, provided by NVX. Same as Device.device_handle
        """
        triggers = ctypes.c_uint(0)
        handle_error(raw.NVXGetTriggers(raw_device, ctypes.byref(triggers)))

        super().__init__(triggers, 0, 8)


class OutputTriggersView(BitView):
    """Provides an array-like view to device's input triggers.
    Unlike InputTriggersView, output triggers can be modified.
    """
    def __init__(self, raw_device):
        """Constructor
        Unlike OutputTriggersView, it's technically possible to construct this class without a device,
        because since you can't set an input trigger, this class is basically equivalent to ConstBitView.
        This constructor is provided for convenience, and to make this class more similar to OutputTriggersView.

        Parameters
        ----------
        raw_device : ctypes.c_void_p
            Raw pointer to the device, provided by NVX. Same as Device.device_handle
        """
        self.device_handle = raw_device

        triggers = ctypes.c_uint(0)
        handle_error(raw.NVXGetTriggers(self.device_handle, ctypes.byref(triggers)))

        super().__init__(triggers, 8, 16)

    def __setitem__(self, index, x):
        """Set an output trigger
        Overrides base class version of this method.

        Parameters
        ----------
        index : int
        x : bool

        Raises
        ------
        IndexError
            if index is not in range [0, 8)
        """
        super().__setitem__(index, x)
        handle_error(raw.NVXSetTriggers(self.device_handle, self.value))


class TriggersView:
    """Provides a view into device's triggers.
    This is a convenience class, provided to access device's triggers in a more pythonic way.
    Triggers can be accessed in 3 ways:
    - triggers['i5'] - access input trigger 5 (or 'o' for output triggers)
    - triggers['input', 5] - for a more verbose version of the previous command
    - triggers.input[5] - using properties <input> and <output> to access or store triggers separately.
    """
    def __init__(self, raw_device):
        self.device_handle = raw_device

    @property
    def input(self):
        """Input triggers of the device. Cannot be modified."""
        return InputTriggersView(self.device_handle)

    @property
    def output(self):
        """Output triggers of the device. Can be modified."""
        return OutputTriggersView(self.device_handle)

    def _unpack_key(self, key):
        """Converts index, passed to __getitem__ or __setitem__, to a more workable format. Handles any errors.

        Parameters
        ----------
        key : str or tuple
            key to process

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
                               " (see the docs on TriggersView.__getitem__ for proper indexing)")

            index = int(key[1])

            if index >= 8:
                raise IndexError("Expected a trigger index 0-7, got " + key[1])

            if key[0] == 'o':
                is_output = True
        elif isinstance(key, tuple):
            if len(key) != 2:
                raise KeyError("Expected a correctly formatted key, got (" + repr(key) +
                               " (see the docs on TriggersView.__getitem__ for proper indexing)")

            extracted_key, extracted_idx = key

            if extracted_key not in ["input", "output"]:
                raise KeyError("Expected a correctly formatted key, got (" +
                               str(extracted_key) + ", " +
                               str(extracted_idx) +
                               ") (see the docs on TriggersView.__getitem__ for proper indexing)")

            if extracted_idx < 0 or extracted_idx >= 8:
                raise IndexError("Expected a trigger index 0-7, got " + str(extracted_idx))
            index = extracted_idx

            if extracted_key[0] == 'o':
                is_output = True
        else:
            raise TypeError("Expected a correctly formatted index, got " + repr(key) +
                            " (see the docs on TriggersView.__getitem__ for proper indexing)")

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
