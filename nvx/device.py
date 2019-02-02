"""
NVX hardware device

"""
import ctypes
from .structs import Version, Settings, Property, DataStatus, ErrorStatus, Gain, PowerSave, \
    ImpedanceSetup, ImpedanceMode, ImpedanceSettings, Voltages, FrequencyBandwidth, Pll
from .base import raw, get_count
from .utility import handle_error
from .sample import Sample
from .impedance import Impedance
from .trigger_states_view import TriggerStatesView
from .channel_states_view import ChannelStatesView


class Device:
    """Device represents a physical device connected to the system"""
    def __init__(self, index):
        """Constructor
        Opens a hardware device for work.
        Device is closed when the object is deleted

        Parameters
        ----------
        index : int
            device index in the system. Must be in range [0, nvx.get_count())
        """
        # Opening device -----------------------------------------------------------------------------------------------
        if 0 <= index < get_count():
            self.device_handle = raw.NVXOpen(index)
        else:
            raise ValueError(
                "no device with index " + str(index) + " (only " + str(get_count()) + " devices detected)")

        if self.device_handle == 0:
            raise RuntimeError("Could not create a device: NVXOpen returned NULL")

        # This getter has side effects that are required for the device to work properly
        self.voltages

        # Member variables ---------------------------------------------------------------------------------------------
        self.index = index
        self._is_running = False  # Not for external use. Use start(), stop(), or is_running property instead.
        self._active_shield_gain = 100

    @property
    def is_running(self):
        return self._is_running

    @property
    def version(self):
        """Version info about NVX

        Returns
        -------
        structs.Version
            NVX version info. See structs.py
        """
        ver = Version()
        handle_error(raw.NVXGetVersion(self.device_handle, ctypes.byref(ver)))
        return ver

    @property
    def settings(self):
        """Get device acquisition settings

        Returns
        -------
        structs.Settings
            device settings. See structs.py
        """
        settings = Settings()
        handle_error(raw.NVXGetSettings(self.device_handle, ctypes.byref(settings)))
        return settings

    @settings.setter
    def settings(self, value):
        """Set device acquisition settings
        
        Parameters
        ----------
        value : structs.Settings
        """
        handle_error(raw.NVXSetSettings(self.device_handle, ctypes.byref(value)))

    @property
    def properties(self):
        """Get device acquisition properties

        Returns
        -------
        structs.Property
            device property. See structs.py
        """
        prop = Property()
        handle_error(raw.NVXGetProperty(self.device_handle, ctypes.byref(prop)))
        return prop

    def start(self):
        """Start data acquisition
        Starts the acquiring data process on the device. If data acquisition was already running, does nothing.
        """
        if not self.is_running:
            handle_error(raw.NVXStart(self.device_handle))
            self._is_running = True

    def stop(self):
        """Stop data acquisition
        Stops the device from acquiring data. If data acquisition was not running, does nothing.
        """
        if self.is_running:
            handle_error(raw.NVXStop(self.device_handle))
            self._is_running = False

    # TODO: Add threads
    # TODO: make pythonic
    def get_data(self):
        """Get acquisition data
        Returns a data sample or None, if there are no more samples generated.
        
        Warnings
        --------
        When the device is running, you should call this function until there are no more samples to get. 
        Otherwise, the internal buffer may overflow.

        Returns
        -------
        sample.Sample or None
            possible data sample. See sample.py
        """
        prop = self.properties
        buffer_size_bytes = prop.count_eeg * 4 + prop.count_aux * 4 + 8
        buffer = ctypes.cast(ctypes.create_string_buffer(buffer_size_bytes), ctypes.c_void_p)

        ret = raw.NVXGetData(self.device_handle, buffer, buffer_size_bytes)
        handle_error(ret)
        if ret == 0:  # no more data to return
            return None

        return Sample(buffer, prop.count_eeg, prop.count_aux)

    @property
    def data_status(self):
        """Get device acquisition data status

        Returns
        -------
        structs.DataStatus
            device data status. See structs.py
        """
        status = DataStatus()
        handle_error(raw.NVXGetDataStatus(self.device_handle, ctypes.byref(status)))
        return status

    @property
    def error_status(self):
        """Get device acquisition error status

        Returns
        -------
        structs.ErrorStatus
            device error status. See structs.py
        """
        status = ErrorStatus()
        handle_error(raw.NVXGetErrorStatus(self.device_handle, ctypes.byref(status)))
        return status

    @property
    def trigger_states(self):
        """Provides a view into device's trigger states

        Returns
        -------
        TriggerStatesView
            Triggers' view. See trigger_states_view.py
        """
        return TriggerStatesView(self)

    @property
    def aux_gain(self):
        """Get aux gain

        Returns
        -------
        structs.Gain
            gain value. See structs.py
        """
        gain = Gain()
        handle_error(raw.NVXGetAuxGain(self.device_handle, ctypes.byref(gain)))
        return gain

    @aux_gain.setter
    def aux_gain(self, gain):
        """Set aux gain

        Parameters
        ----------
        gain : structs.Gain
            gain value. See structs.py
        """
        handle_error(raw.NVXSetAuxGain(self.device_handle, gain))

    @property
    def power_save(self):
        """Get power save mode

        Returns
        -------
        structs.PowerSave
            power save value (0 or 1, as enum). See structs.py
        """
        ps = PowerSave()
        handle_error(raw.NVXGetPowerSave(self.device_handle, ctypes.byref(ps)))
        return ps

    @power_save.setter
    def power_save(self, ps):
        """Set power save mode

        Parameters
        ----------
        ps : structs.PowerSave
            power save value (0 or 1, as enum). See structs.py
        """
        handle_error(raw.NVXSetPowerSave(self.device_handle, PowerSave(ps)))

    @property
    def impedance_data(self):
        """Get impedance values for all EEG channels and ground in Ohm
        
        Remarks (notes):
        - ~750 ms is required for measure impedance per 32 electrodes;
        - max impedance value ~ 300-500 kOhm;
        - impedance measure from 0 Ohm to 120 kOhm with accuracy +/- 15%;
        - works only in impedance mode;
        - ground electrode must be connected for impedance measure;
        - REF electrode (1-st electrode on 1-st module) must be connected for impedance measure;
        - if electrode is not connected, Impedance object will return None.
        
        Returns
        -------
        impedance.Impedance
            channels impedance. See impedance.py
        """
        prop = self.properties
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * 4
        buffer = (ctypes.c_uint * buffer_size)()

        handle_error(raw.NVXImpedanceGetData(self.device_handle, buffer, buffer_size_bytes))

        return Impedance(buffer, prop.count_eeg)

    @property
    def impedance_setup(self):
        """Get setup for impedance mode

        Returns
        -------
        structs.ImpedanceSetup
            impedance setup. See structs.py
        """
        setup = ImpedanceSetup()
        handle_error(raw.NVXImpedanceGetSetup(self.device_handle, ctypes.byref(setup)))
        return setup

    @impedance_setup.setter
    def impedance_setup(self, setup):
        """Set setup for impedance mode

        Parameters
        ----------
        setup : structs.ImpedanceSetup
            impedance setup. See structs.py
        """
        handle_error(raw.NVXImpedanceSetSetup(self.device_handle, ctypes.byref(setup)))

    @property
    def impedance_mode(self):
        """Get current impedance mode

        Returns
        -------
        structs.ImpedanceMode
            impedance mode. See structs.py
        """
        impedance_mode = ImpedanceMode()
        handle_error(raw.NVXImpedanceGetMode(self.device_handle, ctypes.byref(impedance_mode)))
        return impedance_mode

    @impedance_mode.setter
    def impedance_mode(self, mode):
        """Set current impedance mode

        Parameters
        ----------
        mode : structs.ImpedanceMode
            impedance mode. See structs.py
        """
        handle_error(raw.NVXImpedanceGetMode(self.device_handle, ctypes.byref(mode)))

    def set_electrodes(self, values):
        """Directly set (control) electrodes states (LEDs and analog switches) in all modes
        
        Remarks (notes):
        - by calling this function, direct control of electrodes starts automatically;
        - to disable direct control of electrodes call set_electrodes_auto;
        - currently, you need to set all electrodes states at once;
        - To set electrodes colors it's recommended to use NVX_EL_LED_XXX (see globals.py) values.
        
        Parameters
        ----------
        values : a list-like container of objects, each convertible to ctypes.c_uint
            example - a list of int
        
        Warnings
        --------
        - During data acquisition due to switching supply current (i.e. LEDs), a ripple in analog power supply voltage
        appears. This leads to crosstalk to low level input signal and to distortion (and some pulsation) after
        switching supply current (i.e. LEDs);
        - in Impedance mode input analog switch is not accessible;
        - in Impedance mode it is not recommended to call this function very frequently;
        (> few times per 1 sec) or to change (from previous state) too many electrodes, 
        because this will significantly increase impedance measure time (cycle) - see below;
        - After a successful call to this function the device will execute this command:
        ~ 50 ms per 32 electrodes states changes from previous state
        """
        prop = self.properties
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * 4
        buffer = (ctypes.c_uint * buffer_size)()

        for i in range(0, buffer_size):
            buffer[i] = ctypes.c_uint(values[i])

        handle_error(raw.NVXSetElectrodes(self.device_handle, buffer, buffer_size_bytes))

    def set_electrodes_auto(self):
        """Enable automatic LED control
        If automatic LED control was disabled by the set_electrodes function, it can be restored by calling this
        """
        handle_error(raw.NVXSetElectrodes(self.device_handle, None, 0))

    @property
    def impedance_settings(self):
        """Get settings for impedance mode

        Returns
        -------
        structs.ImpedanceSettings
            impedance settings. See structs.py
        """
        settings = ImpedanceSettings()
        handle_error(raw.NVXImpedanceGetSettings(self.device_handle, ctypes.byref(settings)))
        return settings

    @impedance_settings.setter
    def impedance_settings(self, settings):
        """Set settings for impedance mode

        Parameters
        ----------
        settings : structs.ImpedanceSettings
            impedance settings. See structs.py
        """
        handle_error(raw.NVXImpedanceSetSettings(self.device_handle, ctypes.byref(settings)))

    @property
    def voltages(self):
        """Get voltages

        Returns
        -------
        structs.Voltages
            voltages. See structs.py
        """
        voltages = Voltages()
        handle_error(raw.NVXGetVoltages(self.device_handle, ctypes.byref(voltages)))
        return voltages

    @property
    def active_shield_gain(self):
        """Get gain in ActiveShield mode

        Returns
        -------
        int
            Gain value
        """
        return self._active_shield_gain

    @active_shield_gain.setter
    def active_shield_gain(self, gain):
        """Set gain in ActiveShield mode
        
        Parameters
        ----------
        gain : int
            impedance settings in range [1, 100]. Default gain is 100.
            
        Raises
        ------
        ValueError
            if gain is not in range [1, 100]
        """
        if not 1 <= gain <= 100:
            raise ValueError("gain must be in range [1, 100], got " + str(gain))

        handle_error(raw.NVXSetActiveShieldGain(self.device_handle, ctypes.c_uint(gain)))
        self._active_shield_gain = gain

    @property
    def polarization(self):
        """Get polarization of the electrodes

        Returns
        -------
        list of float
            polarisation of electrodes
        """
        # TODO: ask how many electrodes there are (assuming count_eeg + GND)
        prop = self.properties
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_double)
        buffer = (ctypes.c_double * buffer_size)()

        handle_error(raw.NVXSetElectrodes(self.device_handle, buffer, buffer_size_bytes))

        # Convert to a list of floats
        result = []
        for i in range(0, buffer_size):
            result.append(float(buffer[i]))

        return result

    @property
    def sample_rate_count(self):
        """Get device sample rate count

        Returns
        -------
        int
            sample rate count
        """
        count = ctypes.c_uint()
        handle_error(raw.NVXGetSampeRateCount(self.device_handle, ctypes.byref(count)))
        return count

    @property
    def frequency_bandwidth(self):
        """Get frequency bandwidth

        Returns
        -------
        list of structs.FrequencyBandwidth
            frequency bandwidths. See structs.py
        """
        # TODO: ask how large the array should be (assuming count_eeg + GND)
        prop = self.properties
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * ctypes.sizeof(FrequencyBandwidth)
        buffer = (FrequencyBandwidth * buffer_size)()

        handle_error(raw.NVXGetFrequencyBandwidth(self.device_handle, buffer, buffer_size_bytes))
        
        result = [buffer[i] for i in range(buffer_size)]
        return result

    @property
    def _channel_states(self):
        """Get enabled channels
        This function is not recommended for external use. Consider using get_eeg_channel_state or 
        get_aux_channel_state instead

        Returns
        -------
        list of bool
            channel states
        """
        prop = self.properties
        buffer_size = prop.count_eeg + prop.count_aux
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_bool)
        buffer = (ctypes.c_bool * buffer_size)()

        handle_error(raw.NVXGetChannelsEnabled(self.device_handle, buffer, buffer_size_bytes))

        return buffer

    @_channel_states.setter
    def _channel_states(self, values):
        """Set enabled channels
        This function is not recommended for external use. Consider using channel_states property instead.

        Warnings
        --------
        This function assumes that the size of passed array is correct. Otherwise, some bad things can happen.

        Parameters
        ----------
        values : a ctypes array of ctypes.c_bool of size count_eeg+count_aux
            values to set
        """
        prop = self.properties
        buffer_size = prop.count_eeg + prop.count_aux
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_bool)

        handle_error(raw.NVXSetChannelsEnabled(self.device_handle, values, buffer_size_bytes))

    @property
    def channel_states(self):
        """Get a nice and user-friendly view into channel states.
        Returns channel states, that can be looked up either by name, or by an index.

        Returns
        -------
        ChannelStatesView
            A view into channel states. See channel_states_view.py
        """
        return ChannelStatesView(self)

    @property
    def pll(self):
        # TODO: verify that NVXGetPll return type is error code (assuming it is)
        pll = Pll()
        handle_error(raw.NVXGetPll(self.device_handle, ctypes.byref(pll)))
        return pll

    @pll.setter
    def pll(self, value):
        # TODO: verify that NVXSetPll return type is error code (assuming it is)
        handle_error(raw.NVXSetPll(self.device_handle, ctypes.byref(value)))

    def __del__(self):
        # Errors in the destructor are ignored
        if self.is_running:
            raw.NVXStop(self.device_handle)
        raw.NVXClose(self.index)
