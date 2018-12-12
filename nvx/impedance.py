"""
NVX Impedance data

"""


class Impedance:
    """Impedance holds impedance data from all N channels, as well as GND"""
    # Invalid (not connected) impedance value
    INVALID = 2147483647  # INT_MAX (assuming int is 4 bytes)

    def __init__(self, raw_data, count_eeg):
        self.raw_data = raw_data
        self.count_eeg = count_eeg

    def channel(self, index):
        """Get impedance from a channel

        Parameters
        ----------
        index : int

        Raises
        ------
        ValueError
            if index is not in range [0, count_eeg)

        Returns
        -------
        int or None
            impedance data, or None if the electrode is not connected
        """
        if index >= self.count_eeg:
            raise ValueError(
                "no channel with index " + str(index) + " (only " + str(self.count_eeg) + " channels present)")

        result = self.raw_data[index]
        if result == Impedance.INVALID:
            return None
        return result

    def ground(self):
        """Get impedance from GND

        Returns
        -------
        int or None
            impedance data, or None if the electrode is not connected
        """
        result = self.raw_data[self.count_eeg]
        if result == Impedance.INVALID:
            return None
        return result
