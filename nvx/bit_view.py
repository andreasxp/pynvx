import ctypes


class BitView:
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
        return str(list(self))

    def __getitem__(self, idx):
        """Extract a bit

        Parameters
        ----------
        idx : int

        Returns
        -------
        bool
            extracted bit

        Raises
        ------
        IndexError
            if index is not in range [0, len(self))
        """
        if idx < 0 or idx >= len(self):
            raise IndexError("Index (" + str(idx) + ") not in range [0, " + str(len(self)) + ")")

        return bool(self.value.value & (1 << (self.begin + idx)))

    def __setitem__(self, index, x):
        """Set a bit to value (True or False)

        Parameters
        ----------
        index : int
        x : convertible to bool

        Raises
        ------
        IndexError
            if index is not in range [0, len(self))
        """
        if index < 0 or index >= len(self):
            raise IndexError("Index (" + str(index) + ") not in range [0, " + str(len(self)) + ")")

        self.value.value &= ~(      1 << self.begin + index)  # Clear target bit
        self.value.value |=  (bool(x) << self.begin + index)  # Set target bit to x