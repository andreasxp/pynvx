"""
NVX Data sample

"""
import ctypes


# Sample holds one data sample from a Device
class Sample:
    """Sample represents a data slice, returned by Device.get_data"""
    def __init__(self, raw_data, count_eeg, count_aux):
        self.raw_data = raw_data
        self.count_eeg = count_eeg
        self.count_aux = count_aux

    def eeg_data(self, index):
        """Get data from an eeg channel
        
        Parameters
        ----------
        index : int

        Returns
        -------
        int
            requested data
        """
        if index >= self.count_eeg:
            raise ValueError(
                "no channel with index " + str(index)
                + " (only " + str(self.count_eeg) + " eeg channels present)")

        result = ctypes.cast(self.raw_data.value + index*4, ctypes.POINTER(ctypes.c_int))[0]
        return result

    def aux_data(self, index):
        """Get data from an aux channel
        
        Parameters
        ----------
        index : int

        Returns
        -------
        int
            requested data
        """
        if index >= self.count_aux:
            raise ValueError(
                "no aux channel with index " + str(index)
                + " (only " + str(self.count_aux) + " aux channels present)")

        result = ctypes.cast(self.raw_data.value + self.count_eeg*4 + index*4, ctypes.POINTER(ctypes.c_int))[0]
        return result

    def _status(self):
        """Get the digital status
        This function is not recommended for external use. Consider using input_status or output_status instead.

        Returns
        -------
        int
            Folded status: digital inputs (bits 0 - 7) + output (bits 8 - 15) state + 16 MSB reserved bits
        """
        result = ctypes.cast(self.raw_data.value + self.count_eeg * 4 + self.count_aux * 4,
                             ctypes.POINTER(ctypes.c_uint))[0]
        return result

    def input_status(self, index):
        """Get the digital status of an input channel
        
        Parameters
        ----------
        index : int
        
        Raises
        ------
        ValueError
            if index is not in range [0, 8)

        Returns
        -------
        bool
            channel status
        """
        if not 0 <= index < 8:
            raise ValueError("invalid index " + str(index) + ": there are 8 input channels")

        # TODO: verify bit ordering (current: lowest first)
        return bool(self._status() & (1 << index))

    def output_status(self, index):
        """Get the digital status of an output channel
        
        Parameters
        ----------
        index : int
        
        Raises
        ------
        ValueError
            if index is not in range [0, 8)

        Returns
        -------
        bool
            channel status
        """
        if not 0 <= index < 8:
            raise ValueError("invalid index " + str(index) + ": there are 8 output channels")

        # TODO: verify bit ordering (current: lowest first)
        return self._status() & (1 << 8 << index)

    def counter(self):
        """Get a data sequencing cyclic counter for checking the data loss.

        Returns
        -------
        int
            counter
        """
        result = ctypes.cast(self.raw_data.value + self.count_eeg * 4 + self.count_aux * 4 + 4,
                             ctypes.POINTER(ctypes.c_uint))[0]
        return result
