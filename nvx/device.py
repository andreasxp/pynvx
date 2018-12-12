"""
NVX hardware device

"""
import ctypes
from .structs import Version, Settings, Property, DataStatus, ErrorStatus, Gain, PowerSave, \
    ImpedanceSetup, ImpedanceMode, ImpedanceSettings, Voltages, FrequencyBandwidth, Pll
from .base import raw, get_count
from .utility import handle_error, set_bit
from .sample import Sample
from .impedance import Impedance


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

        self.index = index
        if 0 <= index < get_count():
            self.device_handle = raw.NVXOpen(index)
        else:
            raise ValueError(
                "no device with index " + str(index) + " (only " + str(get_count()) + " devices detected)")

        if self.device_handle == 0:
            raise RuntimeError("Could not create a device: NVXOpen returned NULL")

        # This function has side effects that are required for the device to work properly
        self.get_voltages()

    def get_version(self):
        """Get version info about NVX

        Returns
        -------
        structs.Version
            NVX version info. See structs.py
        """
        ver = Version()
        handle_error(raw.NVXGetVersion(self.device_handle, ctypes.byref(ver)))
        return ver

    def get_settings(self):
        """Get device acquisition settings

        Returns
        -------
        structs.Settings
            device settings. See structs.py
        """
        settings = Settings()
        handle_error(raw.NVXGetSettings(self.device_handle, ctypes.byref(settings)))
        return settings

    def set_settings(self, settings):
        """Set device acquisition settings
        
        Parameters
        ----------
        settings : structs.Settings
        """
        handle_error(raw.NVXSetSettings(self.device_handle, ctypes.byref(settings)))

    def get_property(self):
        """Get device acquisition property

        Returns
        -------
        structs.Property
            device property. See structs.py
        """
        prop = Property()
        handle_error(raw.NVXGetProperty(self.device_handle, ctypes.byref(prop)))
        return prop

    def start(self):
        """Start data acquisition"""
        handle_error(raw.NVXStart(self.device_handle))

    def stop(self):
        """Stop data acquisition"""
        handle_error(raw.NVXStop(self.device_handle))

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
        prop = self.get_property()
        buffer_size_bytes = prop.count_eeg * 4 + prop.count_aux * 4 + 8
        buffer = ctypes.cast(ctypes.create_string_buffer(buffer_size_bytes), ctypes.c_void_p)

        ret = raw.NVXGetData(self.device_handle, buffer, buffer_size_bytes)
        handle_error(ret)
        if ret == 0:  # no more data to return
            return None

        return Sample(buffer, prop.count_eeg, prop.count_aux)

    def get_data_status(self):
        """Get device acquisition data status

        Returns
        -------
        structs.DataStatus
            device data status. See structs.py
        """
        status = DataStatus()
        handle_error(raw.NVXGetDataStatus(self.device_handle, ctypes.byref(status)))
        return status

    def get_error_status(self):
        """Get device acquisition error status

        Returns
        -------
        structs.ErrorStatus
            device error status. See structs.py
        """
        status = ErrorStatus()
        handle_error(raw.NVXGetErrorStatus(self.device_handle, ctypes.byref(status)))
        return status

    def _get_triggers(self):
        """Get state of triggers (input and output)
        This function is for internal use only. Consider using get_input_trigger or get_output_trigger instead.

        Returns
        -------
        ctypes.c_uint
            triggers states, folded into 32 bits: 8-bit inputs (bits 0 - 7) + 8-bit outputs (bits 8 - 15) + 16 MSB reserved bits.
        """
        triggers = ctypes.c_uint(0)
        handle_error(raw.NVXGetTriggers(self.device_handle, ctypes.byref(triggers)))
        return triggers

    def get_input_trigger(self, index):
        """Get state of an input trigger
        
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
            triggers state
        """
        if not 0 <= index < 8:
            raise ValueError("invalid index " + str(index) + ": there are 8 input triggers")

        # TODO: verify bit ordering (current: lowest first)
        # TODO: ask if triggers are the same as channels in Sample
        return bool(self._get_triggers() & (1 << index))

    def get_output_trigger(self, index):
        """Get state of an output trigger
        
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
            triggers state
        """
        if not 0 <= index < 8:
            raise ValueError("invalid index " + str(index) + ": there are 8 output triggers")

        # TODO: verify bit ordering (current: lowest first)
        # TODO: ask if triggers are the same as channels in Sample
        return bool(self._get_triggers() & (1 << 8 << index))

    def _set_triggers(self, triggers):
        """Set state of triggers (output only)
        This function is for internal use only. Consider using set_output_trigger instead.

        Parameters
        ----------
        triggers : ctypes.c_uint
            triggers states, folded into 32 bits: 8-bit inputs (bits 0 - 7) + 8-bit outputs (bits 8 - 15) + 16 MSB reserved bits.
        """
        handle_error(raw.NVXSetTriggers(self.device_handle, ctypes.c_uint(triggers)))

    def set_output_trigger(self, index, value):
        """Set state of an output trigger
        
        Parameters
        ----------
        index : int
        value : bool
        
        Raises
        ------
        ValueError
            if index is not in range [0, 8)
        """
        if not 0 <= index < 8:
            raise ValueError("invalid index " + str(index) + ": there are 8 output triggers")

        # TODO: verify bit ordering (current: lowest first)
        triggers = self._get_triggers()
        self._set_triggers(set_bit(triggers, index, value))

    def get_aux_gain(self):
        """Get aux gain

        Returns
        -------
        structs.Gain
            gain value. See structs.py
        """
        gain = Gain()
        handle_error(raw.NVXGetAuxGain(self.device_handle, ctypes.byref(gain)))
        return gain

    def set_aux_gain(self, gain):
        """Set aux gain

        Parameters
        ----------
        gain : structs.Gain
            gain value. See structs.py
        """
        handle_error(raw.NVXSetAuxGain(self.device_handle, gain))

    def get_power_save(self):
        """Get power save mode

        Returns
        -------
        structs.PowerSave
            power save value (0 or 1, as enum). See structs.py
        """
        power_save = PowerSave()
        handle_error(raw.NVXGetPowerSave(self.device_handle, ctypes.byref(power_save)))
        return power_save

    def set_power_save(self, power_save):
        """Set power save mode

        Parameters
        ----------
        power_save : structs.PowerSave
            power save value (0 or 1, as enum). See structs.py
        """
        handle_error(raw.NVXSetPowerSave(self.device_handle, PowerSave(power_save)))

    def get_impedance_data(self):
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
        prop = self.get_property()
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * 4
        buffer = (ctypes.c_uint * buffer_size)()

        handle_error(raw.NVXImpedanceGetData(self.device_handle, buffer, buffer_size_bytes))

        return Impedance(buffer, prop.count_eeg)

    def get_impedance_setup(self):
        """Get setup for impedance mode

        Returns
        -------
        structs.ImpedanceSetup
            impedance setup. See structs.py
        """
        impedance_setup = ImpedanceSetup()
        handle_error(raw.NVXImpedanceGetSetup(self.device_handle, ctypes.byref(impedance_setup)))
        return impedance_setup

    def set_impedance_setup(self, impedance_setup):
        """Set setup for impedance mode

        Parameters
        ----------
        impedance_setup : structs.ImpedanceSetup
            impedance setup. See structs.py
        """
        handle_error(raw.NVXImpedanceSetSetup(self.device_handle, ctypes.byref(impedance_setup)))

    def get_impedance_mode(self):
        """Get current impedance mode

        Returns
        -------
        structs.ImpedanceMode
            impedance mode. See structs.py
        """
        impedance_mode = ImpedanceMode()
        handle_error(raw.NVXImpedanceGetMode(self.device_handle, ctypes.byref(impedance_mode)))
        return impedance_mode

    def set_impedance_mode(self, mode):
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
        values : a list-like container of objects, convertible to ctypes.c_uint
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
        prop = self.get_property()
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

    def get_impedance_settings(self):
        """Get settings for impedance mode

        Returns
        -------
        structs.ImpedanceSettings
            impedance settings. See structs.py
        """
        impedance_settings = ImpedanceSettings()
        handle_error(raw.NVXImpedanceGetSettings(self.device_handle, ctypes.byref(impedance_settings)))
        return impedance_settings

    def set_impedance_settings(self, settings):
        """Set settings for impedance mode

        Parameters
        ----------
        settings : structs.ImpedanceSettings
            impedance settings. See structs.py
        """
        handle_error(raw.NVXImpedanceSetSettings(self.device_handle, ctypes.byref(settings)))

    def get_voltages(self):
        """Get voltages

        Returns
        -------
        structs.Voltages
            voltages. See structs.py
        """
        voltages = Voltages()
        handle_error(raw.NVXGetVoltages(self.device_handle, ctypes.byref(voltages)))
        return voltages

    def set_active_shield_gain(self, gain):
        """Set gain in ActiveShield mode
        
        Parameters
        ----------
        gain : int
            impedance settings in range [1, 100]. Default gain is 100.
            
        Raises
        ------
        ValueError
            if gain is not in range [0, 100]
        """
        if not 1 <= gain <= 100:
            raise ValueError("gain must be in range [1, 100], got " + str(gain))

        handle_error(raw.NVXSetActiveShieldGain(self.device_handle, ctypes.c_uint(gain)))

    def get_polarization(self):
        """Get polarization of the electrodes

        Returns
        -------
        list of float
            polarisation of electrodes
        """
        # TODO: ask how many electrodes there are (assuming count_eeg + GND)
        prop = self.get_property()
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_double)
        buffer = (ctypes.c_double * buffer_size)()

        handle_error(raw.NVXSetElectrodes(self.device_handle, buffer, buffer_size_bytes))

        # Convert to a list of floats
        result = []
        for i in range(0, buffer_size):
            result.append(float(buffer[i]))

        return result

    def get_sample_rate_count(self):
        """Get device sample rate count

        Returns
        -------
        int
            sample rate count
        """
        count = ctypes.c_uint()
        handle_error(raw.NVXGetSampeRateCount(self.device_handle, ctypes.byref(count)))
        return count

    def get_frequency_bandwidth(self):
        """Get frequency bandwidth

        Returns
        -------
        list of structs.FrequencyBandwidth
            frequency bandwidths. See structs.py
        """
        # TODO: ask how large the array should be (assuming count_eeg + GND)
        prop = self.get_property()
        buffer_size = prop.count_eeg + 1
        buffer_size_bytes = buffer_size * ctypes.sizeof(FrequencyBandwidth)
        buffer = (FrequencyBandwidth * buffer_size)()

        handle_error(raw.NVXGetFrequencyBandwidth(self.device_handle, buffer, buffer_size_bytes))
        
        result = [buffer[i] for i in range(buffer_size)]
        return result

    def _get_channel_states(self):
        """Get enabled channels
        This function is not recommended for external use. Consider using get_eeg_channel_state or 
        get_aux_channel_state instead

        Returns
        -------
        list of bool
            channel states
        """
        prop = self.get_property()
        buffer_size = prop.count_eeg + prop.count_aux
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_bool)
        buffer = (ctypes.c_bool * buffer_size)()

        handle_error(raw.NVXGetChannelsEnabled(self.device_handle, buffer, buffer_size_bytes))
        
        result = [bool(buffer[i]) for i in range(buffer_size)]
        return result

    def _set_channel_states(self, values):
        """Set enabled channels
        This function is not recommended for external use. Consider using set_eeg_channel_state or 
        set_aux_channel_state instead
        
        Parameters
        ----------
        values : a list-like container of objects, convertible to ctypes.c_bool
            example - a list of bool
        """
        prop = self.get_property()
        buffer_size = prop.count_eeg + prop.count_aux
        buffer_size_bytes = buffer_size * ctypes.sizeof(ctypes.c_bool)
        buffer = (ctypes.c_bool * buffer_size)()

        for i in range(0, buffer_size):
            buffer[i] = ctypes.c_bool(values[i])

        handle_error(raw.NVXSetChannelsEnabled(self.device_handle, buffer, buffer_size_bytes))

    def get_eeg_channel_state(self, index):
        """Get the state of an eeg channel
        
        Parameters
        ----------
        index : int
        
        Raises
        ------
        ValueError
            if index is not in range [0, count_eeg)
            
        Returns
        -------
        bool
            channel state
        """
        # TODO: verify that eeg and aux channels are in correct order (assuming eeg before aux)
        prop = self.get_property()
        if not 0 <= index < prop.count_eeg:
            raise ValueError(
                "no channel with index " + str(index) + " (only " + str(prop.count_eeg) + " eeg channels present)")

        return self._get_channel_states()[index]

    def get_aux_channel_state(self, index):
        """Get the state of an aux channel
        
        Parameters
        ----------
        index : int
        
        Raises
        ------
        ValueError
            if index is not in range [0, count_aux)
            
        Returns
        -------
        bool
            channel state
        """
        # TODO: verify that eeg and aux channels are in correct order (assuming eeg before aux)
        prop = self.get_property()
        if not 0 <= index < prop.count_aux:
            raise ValueError(
                "no channel with index " + str(index) + " (only " + str(prop.count_aux) + " aux channels present)")

        return self._get_channel_states()[prop.count_eeg + index]

    def set_eeg_channel_state(self, index, value):
        """Set the state of an eeg channel
        
        Parameters
        ----------
        index : int
        value : bool
        
        Raises
        ------
        ValueError
            if index is not in range [0, count_eeg)
        """
        # TODO: verify that eeg and aux channels are in correct order (assuming eeg before aux)
        prop = self.get_property()
        if not 0 <= index < prop.count_eeg:
            raise ValueError(
                "no channel with index " + str(index) + " (only " + str(prop.count_eeg) + " eeg channels present)")

        buffer = self._get_channel_states()
        buffer[index] = ctypes.c_bool(value)
        self._set_channel_states(buffer)

    def set_aux_channel_state(self, index, value):
        """Set the state of an aux channel
        
        Parameters
        ----------
        index : int
        value : bool
        
        Raises
        ------
        ValueError
            if index is not in range [0, count_aux)
        """
        # TODO: verify that eeg and aux channels are in correct order (assuming eeg before aux)
        prop = self.get_property()
        if not 0 <= index < prop.count_aux:
            raise ValueError(
                "no channel with index " + str(index) + " (only " + str(prop.count_aux) + " aux channels present)")

        buffer = self._get_channel_states()
        buffer[prop.count_eeg + index] = ctypes.c_bool(value)
        self._set_channel_states(buffer)

    def get_pll(self):
        # TODO: verify that NVXGetPll return type is error code (assuming it is)
        pll = Pll()
        handle_error(raw.NVXGetPll(self.device_handle, ctypes.byref(pll)))
        return pll

    def set_pll(self, pll):
        # TODO: verify that NVXSetPll return type is error code (assuming it is)
        handle_error(raw.NVXSetPll(self.device_handle, ctypes.byref(pll)))

    def __del__(self):
        handle_error(raw.NVXClose(self.index))
