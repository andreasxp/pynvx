import ctypes
from .channel_names import eeg_channel, aux_channel


class EegStatesView:
    """A view into eeg channels' states. (on/off)"""
    def __init__(self, device):
        """Constructor
        You should not construct this by yourself. This class is returned by ChannelStatesView eeg property.

        Parameters
        ----------
        device : nvx.Device
            Device from which the states are requested.
        """
        self.device = device

    def __len__(self):
        return self.device.properties.count_eeg

    def __getitem__(self, idx):
        """Get an eeg channel state using a channel index.

        Parameters
        ----------
        idx : int
            Channel index

        Raises
        ------
        IndexError
            If idx is not in range [0, len(self))

        Returns
        -------
        bool
            requested channel's state (on/off)
        """
        size = len(self)
        if not 0 <= idx < size:
            raise IndexError("no channel with index " + str(idx) +
                             " (only " + str(size) + " eeg channels present)")

        return self.device._channel_states[idx]

    def __setitem__(self, idx, value):
        """Set an eeg channel state (on/off).
        This function can only be called when the device is not running.

        Parameters
        ----------
        idx : int
            Channel index
        value : bool
            State to set

        Raises
        ------
        IndexError
            If idx is not in range [0, len(self))
        RuntimeError
            If the device is running when the function is called
        """
        if self.device.is_running:
            raise RuntimeError("cannot set a channel state when the device is running")

        size = len(self)
        if not 0 <= idx < size:
            raise IndexError("no channel with index " + str(idx) +
                             " (only " + str(size) + " eeg channels present)")

        states = self.device._channel_states
        states[idx] = ctypes.c_bool(value)
        self.device._channel_states = states


class AuxStatesView:
    """A view into aux channels' states. (on/off)"""
    def __init__(self, device):
        """Constructor
        You should not construct this by yourself. This class is returned by ChannelStatesView aux property.

        Parameters
        ----------
        device : nvx.Device
            Device from which the states are requested.
        """
        self.device = device

    def __len__(self):
        return self.device.properties.count_aux

    def __getitem__(self, idx):
        """Get an aux channel state using a channel index.

        Parameters
        ----------
        idx : int
            Channel index

        Raises
        ------
        IndexError
            If idx is not in range [0, len(self))

        Returns
        -------
        bool
            requested channel's state (on/off)
        """
        size = len(self)
        if not 0 <= idx < size:
            raise IndexError("no channel with index " + str(idx) +
                             " (only " + str(size) + " aux channels present)")

        return self.device._channel_states[self.device.properties.count_eeg + idx]

    def __setitem__(self, idx, value):
        """Set an aux channel state (on/off).
        This function can only be called when the device is not running.

        Parameters
        ----------
        idx : int
            Channel index
        value : bool
            State to set

        Raises
        ------
        IndexError
            If idx is not in range [0, len(self))
        RuntimeError
            If the device is running when the function is called
        """
        if self.device.is_running:
            raise RuntimeError("cannot set a channel state when the device is running")

        size = len(self)
        if not 0 <= idx < size:
            raise IndexError("no channel with index " + str(idx) +
                             " (only " + str(size) + " aux channels present)")

        states = self.device._channel_states
        states[self.device.properties.count_eeg + idx] = ctypes.c_bool(value)
        self.device._channel_states = states


class ChannelStatesView:
    """Provides a view into a device's channels' states.
    States can be accessed in two ways:
    view['T7'] - by channel name (either eeg or aux)
    view.eeg[0] - by index (or view.aux[0] for aux channels)
    """
    def __init__(self, device):
        """Constructor
        You should not construct this by yourself. This class is returned by device's channel_states property.

        Parameters
        ----------
        device : nvx.Device
            Device from which the states are requested.
        """
        self.device = device

    @property
    def eeg(self):
        """Get eeg channels' states"""
        return EegStatesView(self.device)

    @property
    def aux(self):
        """Get aux channels' states"""
        return AuxStatesView(self.device)

    def __iter__(self):
        """Returns an iterator to the EEG+AUX channel keys."""
        for key in eeg_channel:
            yield key
        for key in aux_channel:
            yield key

    def keys(self):
        """Returns an iterator to the EEG+AUX channel keys."""
        for key in eeg_channel:
            yield key
        for key in aux_channel:
            yield key

    def values(self):
        """Returns an iterator to the EEG+AUX channel states."""
        for key in eeg_channel:
            yield self[key]
        for key in aux_channel:
            yield self[key]

    def items(self):
        """Returns an iterator to the EEG+AUX (keys, values)."""
        for key in eeg_channel:
            yield (key, self[key])
        for key in aux_channel:
            yield (key, self[key])

    def __contains__(self, key):
        """Checks if a channel with a particular name exists.
        See channel_names.py for a list of available names.

        Parameters
        ----------
        key : str
            Name of an EEG or AUX channel

        Returns
        -------
        bool
            True, if this channel exists, False otherwise
        """
        if key in eeg_channel or key in aux_channel:
            return True
        return False

    def __getitem__(self, key):
        """Get a channel state (on/off) using a channel name.

        Parameters
        ----------
        key : str
            Name of an EEG or AUX channel that is present in channel_names.py

        Raises
        ------
        KeyError
            if name is not a valid eeg/aux channel name

        Returns
        -------
        bool
            requested channel's state (on/off)
        """
        if key in eeg_channel:
            return self.eeg[eeg_channel[key]]
        else:
            return self.aux[aux_channel[key]]

    def __setitem__(self, key, value):
        """Set a channel state (on/off) using a channel name.

        Parameters
        ----------
        key : str
            Name of an EEG or AUX channel that is present in channel_names.py
        value : bool
            State to set

        Raises
        ------
        KeyError
            if name is not a valid eeg/aux channel name
        """
        if key in eeg_channel:
            self.eeg[eeg_channel[key]] = value
        else:
            self.aux[aux_channel[key]] = value

    def __str__(self):
        return str(dict(self))
