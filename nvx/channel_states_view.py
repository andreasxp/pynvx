"""A collection of classes for viewing EEG and AUX channel states (on/off)."""
import ctypes
from .channel_names import eeg_channel, aux_channel


class EegStatesView:
    def __init__(self, device):
        """A view into EEG channels' states. (on/off).
        This class is not intended to be constructed manually. An instance is returned by `ChannelStatesView.eeg`
        property.

        Parameters
        ----------
        device : Device
            Device from which the states are requested.
        """
        self.device = device

    def __len__(self):
        return self.device.eeg_count

    def __getitem__(self, index):
        """Get an EEG channel state using a channel index.

        Parameters
        ----------
        index : int
            Channel index

        Raises
        ------
        IndexError
            If index is not in range [0, len(self))

        Returns
        -------
        bool
            requested channel's state (on/off)
        """
        size = len(self)
        if not 0 <= index < size:
            raise IndexError("no channel with index " + str(index) +
                             " (only " + str(size) + " EEG channels present)")

        return self.device._channel_states[index]

    def __setitem__(self, index, value):
        """Set an EEG channel state (on/off).
        This function can only be called when the device is not running.

        Parameters
        ----------
        index : int
            Channel index
        value : bool
            State to set

        Raises
        ------
        IndexError
            If index is not in range [0, len(self))
        RuntimeError
            If the device is running when the function is called
        """
        if self.device.is_running:
            raise RuntimeError("cannot set a channel state when the device is running")

        size = len(self)
        if not 0 <= index < size:
            raise IndexError("no channel with index " + str(index) +
                             " (only " + str(size) + " eeg channels present)")

        states = self.device._channel_states
        states[index] = ctypes.c_bool(value)
        self.device._channel_states = states


class AuxStatesView:
    def __init__(self, device):
        """A view into aux channels' states. (on/off).
        This class is not intended to be constructed manually. An instance is returned by `ChannelStatesView.aux`
        property.

        Parameters
        ----------
        device : nvx.device.Device
            Device from which the states are requested.
        """
        self.device = device

    def __len__(self):
        return self.device.aux_count

    def __getitem__(self, index):
        """Get an AUX channel state using a channel index.

        Parameters
        ----------
        index : int
            Channel index

        Raises
        ------
        IndexError
            If index is not in range [0, len(self))

        Returns
        -------
        bool
            requested channel's state (on/off)
        """
        size = len(self)
        if not 0 <= index < size:
            raise IndexError("no channel with index " + str(index) +
                             " (only " + str(size) + " AUX channels present)")

        return self.device._channel_states[self.device.eeg_count + index]

    def __setitem__(self, index, value):
        """Set an AUX channel state (on/off).
        This function can only be called when the device is not running.

        Parameters
        ----------
        index : int
            Channel index
        value : bool
            State to set

        Raises
        ------
        IndexError
            If index is not in range [0, len(self)).
        RuntimeError
            If the device is running when the function is called.
        """
        if self.device.is_running:
            raise RuntimeError("cannot set a channel state when the device is running")

        size = len(self)
        if not 0 <= index < size:
            raise IndexError("no channel with index " + str(index) +
                             " (only " + str(size) + " aux channels present)")

        states = self.device._channel_states
        states[self.device.eeg_count + index] = ctypes.c_bool(value)
        self.device._channel_states = states


class ChannelStatesView:
    def __init__(self, device):
        """Provides a view into a device's channels' states.
        States can be accessed in two ways:
        - view['T7'] - by channel name (either EEG or AUX)
        - view.eeg[0] - by index (or view.aux[0] for AUX channels)

        This class is not intended to be constructed manually. An instance is returned by Device.channel_states
        property.

        Parameters
        ----------
        device : nvx.device.Device
            Device from which the states are requested.
        """
        self.device = device

    @property
    def eeg(self):
        """Get EEG channels' states."""
        return EegStatesView(self.device)

    @property
    def aux(self):
        """Get AUX channels' states."""
        return AuxStatesView(self.device)

    def __iter__(self):
        """An iterator to the EEG+AUX channel keys."""
        for key in eeg_channel:
            yield key
        for key in aux_channel:
            yield key

    def keys(self):
        """An iterator to the EEG+AUX channel keys."""
        for key in eeg_channel:
            yield key
        for key in aux_channel:
            yield key

    def values(self):
        """An iterator to the EEG+AUX channel states."""
        for key in eeg_channel:
            yield self[key]
        for key in aux_channel:
            yield self[key]

    def items(self):
        """An iterator to the EEG+AUX (keys, values)."""
        for key in eeg_channel:
            yield (key, self[key])
        for key in aux_channel:
            yield (key, self[key])

    def __contains__(self, key):
        """Checks if a channel with a particular name exists.

        Parameters
        ----------
        key : str
            Name of an EEG or AUX channel.

        Returns
        -------
        bool
            True if this channel exists, False otherwise.

        See Also
        --------
        nvx.channel_names
            A list of available channel names.
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
            If name is not a valid EEG/AUX channel name.

        Returns
        -------
        bool
            Requested channel's state (on/off).
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
            If name is not a valid EEG/AUX channel name.
        """
        if key in eeg_channel:
            self.eeg[eeg_channel[key]] = value
        else:
            self.aux[aux_channel[key]] = value

    def __str__(self):
        return str(dict(self))
