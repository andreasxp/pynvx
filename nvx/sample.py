"""
NVX Data sample

"""
import ctypes
import numpy as np
from .channel_names import eeg_channel, aux_channel


# Sample holds one data sample from a Device
class Sample:
    """Sample represents a data slice, returned by Device.get_data"""
    def __init__(self, raw_data, eeg_count, aux_count):
        size = eeg_count + aux_count
        ctypes_array = (ctypes.c_int32 * size).from_address(raw_data.value)

        # TODO: Add local counter
        # TODO: Add time pulled
        # Numpy array representation of the EEG and AUX data
        self.data = np.ctypeslib.as_array(ctypes_array)
        self.eeg_count = eeg_count
        self.aux_count = aux_count

        # Status bitfield: digital inputs (bits 0 - 7) + output (bits 8 - 15) state + 16 MSB reserved bits
        self._status = ctypes.cast(raw_data.value + self.eeg_count * 4 + self.aux_count * 4,
                                   ctypes.POINTER(ctypes.c_uint))[0]

        # Data sequencing cyclic counter for checking for data loss.
        self.counter = ctypes.cast(raw_data.value + self.eeg_count * 4 + self.aux_count * 4 + 4,
                                   ctypes.POINTER(ctypes.c_uint))[0]

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
        if index >= self.eeg_count:
            raise ValueError(
                "no channel with index " + str(index)
                + " (only " + str(self.eeg_count) + " eeg channels present)")

        return self.data[index]

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
        if index >= self.aux_count:
            raise ValueError(
                "no aux channel with index " + str(index)
                + " (only " + str(self.aux_count) + " aux channels present)")

        return self.data[self.eeg_count + index]

    def __getitem__(self, channel_name):
        """Get data from an eeg or aux channel by name

        Parameters
        ----------
        channel_name : str
            Name of an EEG or AUX channel that is present in channel_names.py

        Raises
        ------
        KeyError
            if channel_name is not a valid eeg/aux channel name

        Returns
        -------
        int
            requested data
        """
        if channel_name in eeg_channel:
            return self.eeg_data(eeg_channel[channel_name])
        else:
            return self.aux_data(aux_channel[channel_name])

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
        return bool(self._status & (1 << index))

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
        return self._status & (1 << 8 << index)
