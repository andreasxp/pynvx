"""
NVX hardware device

"""
import ctypes
from threading import Thread
import time
import math

from .structs import Version, Settings, Property, DataStatus, ErrorStatus, Gain, PowerSave, \
    ImpedanceSetup, ImpedanceMode, ScanFreq, ImpedanceSettings, Voltages, FrequencyBandwidth, Pll, Rate
from .base import raw, get_count
from .utility import handle_error
from .sample import Sample
from .ring_buffer import RingBuffer
from .impedance import Impedance
from .trigger_states_view import TriggerStatesView
from .channel_states_view import ChannelStatesView


class Device:
    """Device represents a physical device connected to the system"""
    def __init__(self, index: int, buffer_time: float = 1.0):
        """Constructor
        Opens a hardware device for work.
        Device is closed when the object is deleted

        Parameters
        ----------
        index : int
            device index in the system. Must be in range [0, nvx.get_count())
        buffer_time
            amount of time for which the samples will be kept in seconds
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

        # Data collecting ----------------------------------------------------------------------------------------------
        self._buffer_time = buffer_time
        self._buffer = None  # Created at start()
        self._collector_thread = Thread(target=self._collect)
        self._delay_tolerance = 0.01

        # Member variables ---------------------------------------------------------------------------------------------
        self._index = index
        self._is_running = False  # Not for external use. Use start(), stop(), or is_running property instead.
        self._active_shield_gain = 100

        # Data acquisition rate (hz). Not always the same as source_rate property.
        # Not for external use. Use rate property instead.
        self._rate = 10000

        # Set source rate to the maximum. Seems that this results in the least delay. Unneeded samples are discarded
        # during collection.
        s = self._settings
        s.rate = Rate.KHZ_100
        self._settings = s

    @property
    def index(self):
        """Get device index"""
        return self._index

    @property
    def is_running(self):
        """Get the state of the data acquisition process"""
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

    # Settings and their properties ====================================================================================
    @property
    def _settings(self):
        """Get device acquisition settings
        This property is for internal use. Struct Settings has 4 members, (mode, rate, adc_filter, decimation), of which
        mode, rate and decimation can be accessed via their own properties (acquisition_mode, rate/source_rate and
        decimation), and adc_filter is deprecated in the DLL.

        Returns
        -------
        structs.Settings
            device settings. See structs.py
        """
        result = Settings()
        handle_error(raw.NVXGetSettings(self.device_handle, ctypes.byref(result)))
        return result

    @_settings.setter
    def _settings(self, value):
        """Set device acquisition settings
        This property is for internal use. Struct Settings has 4 members, (mode, rate, adc_filter, decimation), of which
        mode, rate and decimation can be accessed via their own properties (acquisition_mode, rate/source_rate and
        decimation), and adc_filter is deprecated in the DLL.

        Note: rate property uses structs.Property.rate as well as structs.Settings.rate.
        
        Parameters
        ----------
        value : structs.Settings
        """
        handle_error(raw.NVXSetSettings(self.device_handle, ctypes.byref(value)))

    @property
    def acquisition_mode(self):
        return self._settings.mode

    @acquisition_mode.setter
    def acquisition_mode(self, value):
        s = self._settings
        s.mode = value
        self._settings = s

    @property
    def decimation(self):
        return self._settings.mode

    @decimation.setter
    def decimation(self, value):
        s = self._settings
        s.decimation = value
        self._settings = s

    # Properties and their properties ==================================================================================
    @property
    def _properties(self):
        """Get device acquisition _properties

        Returns
        -------
        structs.Property
            device property. See structs.py
        """
        prop = Property()
        handle_error(raw.NVXGetProperty(self.device_handle, ctypes.byref(prop)))
        return prop

    @property
    def eeg_count(self):
        """Get the count of EEG channels."""
        return self._properties.count_eeg

    @property
    def aux_count(self):
        """Get the count of AUX channels."""
        return self._properties.count_aux

    @property
    def input_triggers_count(self):
        """Get the count of input triggers."""
        return self._properties.triggers_in

    @property
    def output_triggers_count(self):
        """Get the count of output triggers."""
        return self._properties.triggers_out

    @property
    def source_rate(self):
        """Get device's actual pull rate.
        self._properties.rate is always the same as self._settings.rate, but presented as a float instead of enum.

        Returns
        -------
        int
            device's internal pull rate. Always one of (10000, 50000, 100000). Default is 10000
        """
        return int(self._properties.rate)

    @property
    def eeg_resolution(self):
        """Get the EEG amplitude scale coefficients, in V/bit

        Returns
        -------
        float
        """
        return self._properties.resolution_eeg

    @property
    def aux_resolution(self):
        """Get the AUX amplitude scale coefficients, in V/bit

        Returns
        -------
        float
        """
        return self._properties.resolution_aux

    @property
    def eeg_range(self):
        """Get the EEG input range peak-peak, in V

        Returns
        -------
        float
        """
        return self._properties.range_eeg

    @property
    def aux_range(self):
        """Get the AUX input range peak-peak, in V

        Returns
        -------
        float
        """
        return self._properties.range_aux

    # Adjusted rate property ===========================================================================================
    @property
    def rate(self):
        """Get device's pull rate.
        This is the rate at which the device will output values, and is equal to source_rate by default.
        Otherwise, it is usually lower, and some samples will be discarded to meet this rate.

        Returns
        -------
        int
            device's sample output rate in range [1, 100000]
        """
        return self._rate

    @rate.setter
    def rate(self, value):
        if value <= 0:
            raise ValueError("sampling frequency too low: must not be less than 1, got " + str(value))
        elif value > 100000:
            raise ValueError("sampling frequency too high: must not be more than 100000, got " + str(value))

        # Set sampling frequency
        self._rate = value

    # ==================================================================================================================

    def _new_buffer(self):
        """Create a new internal buffer
        Not recommended for external use.
        """
        return RingBuffer(math.ceil(self.rate * self._buffer_time), dtype=object)

    def start(self):
        """Start data acquisition
        Starts the acquiring data process on the device. If data acquisition was already running, does nothing.
        """
        if not self.is_running:
            self._buffer = self._new_buffer()
            handle_error(raw.NVXStart(self.device_handle))
            self._is_running = True
            self._collector_thread.start()

    def stop(self):
        """Stop data acquisition
        Stops the device from acquiring data. If data acquisition was not running, does nothing.
        """
        if self.is_running:
            self._is_running = False
            self._collector_thread.join()
            handle_error(raw.NVXStop(self.device_handle))

    @property
    def delay_tolerance(self):
        """Get device's delay tolerance.
        Delay tolerance represents time in seconds, how much the device is allowed to wait before attempting to pull a
        data sample. Default time is 0.01 seconds, and can be set to 0 (although that might lead to inconsistent pull
        times due to thread locks fighting).

        Returns
        -------
        float
            Delay tolerance, seconds
        """
        return self._delay_tolerance

    @delay_tolerance.setter
    def delay_tolerance(self, value):
        """Set a new delay tolerance.
        Delay tolerance represents time in seconds, how much the device is allowed to wait before attempting to pull a
        data sample. Default time is 0.01 seconds. Delay tolerance is used in the collector thread, and thus cannot be
        set when the device is running.

        Warnings
        --------
        Setting delay_tolerance to 0 might lead to inconsistent pull times.

        Parameters
        ----------
        value : float
            delay tolerance in seconds

        Raises
        ------
        RuntimeError
            if the device is currently running
        """
        if self.is_running:
            raise RuntimeError("delay_tolerance cannot be set when the device is running")
        self._delay_tolerance = value

    def _get_data(self):
        """Get acquisition data
        Returns a data sample or None, if there are no more samples generated.
        Not recommended for external use. Consider using pull method instead.

        When the device is running, this class calls this function until there are no more samples to get.
        Otherwise, the internal buffer may overflow.

        Returns
        -------
        sample.Sample or None
            possible data sample. See sample.py
        """
        buffer_size_bytes = self.eeg_count * 4 + self.aux_count * 4 + 8
        buffer = ctypes.cast(ctypes.create_string_buffer(buffer_size_bytes), ctypes.c_void_p)

        ret = raw.NVXGetData(self.device_handle, buffer, buffer_size_bytes)
        handle_error(ret)
        if ret == 0:  # no more data to return
            return None

        return Sample(buffer, self.eeg_count, self.aux_count)

    def _collect(self):
        """Collect and process samples when running.
        Not recommended for external use.
        """
        while self.is_running:
            # Get new sample (returns None if no samples left)
            sample = self._get_data()

            if sample is not None and self._process(sample):
                self._buffer.append(sample)
            if sample is None and self.delay_tolerance > 0:
                time.sleep(self.delay_tolerance)

    def _process(self, sample):
        """Process a sample.
        Returns True if a sample is to be accepted.
        Not recommended for external use.
        """
        ratio = self.rate / self.source_rate

        cup0 = int(ratio * sample.counter)
        cup1 = int(ratio * (sample.counter+1))

        # if a cup was filled, accept sample
        return cup0 != cup1

    def pull_chunk(self):
        """Pull all samples from the device.

        Returns
        -------
        list
            requested samples. list can be empty, if no samples were generated since last call.
        """
        # TODO: is this actually thread-safe?
        result, self._buffer = self._buffer, self._new_buffer()
        return result

    @property
    def _data_status(self):
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
    def source_sample_count(self):
        """Returns how many samples were generated on the hardware device.
        Since Device implements rate downsampling, this number is equal or larger than the amount of samples passed to
        the device user.
        This value is the same as field 'samples' in data_status and error status, and provided here for convenience.

        Returns
        -------
        int
            samples count
        """
        return self._data_status.samples

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
        While internally Gain is used as an enum, this function returns an int for convenience.

        Returns
        -------
        int
            gain value (1 or 5). See also structs.Gain
        """
        gain = Gain()
        handle_error(raw.NVXGetAuxGain(self.device_handle, ctypes.byref(gain)))

        if gain == Gain.GAIN_1:
            return 1
        return 5

    @aux_gain.setter
    def aux_gain(self, value):
        """Set aux gain
        While internally Gain is used as an enum, this function accepts an int for convenience. That means that the only
        acceptable values for gain are 1 and 5.

        Raises
        ------
        ValueError
            if passed gain value is not 1 or 5.

        Parameters
        ----------
        value : int
            gain value. See structs.py
        """
        gain = Gain()
        if value == 1:
            gain = Gain.GAIN_1
        elif value == 5:
            gain = Gain.GAIN_5
        else:
            raise ValueError("expected a gain value of either 1 or 5, got " + str(value))
        handle_error(raw.NVXSetAuxGain(self.device_handle, gain))

    @property
    def power_save(self):
        """Get power save mode

        Returns
        -------
        bool
            True if power save mode is enabled, False otherwise.
        """
        ps = PowerSave()
        handle_error(raw.NVXGetPowerSave(self.device_handle, ctypes.byref(ps)))
        if ps == PowerSave.DISABLE:
            return False
        return True

    @power_save.setter
    def power_save(self, value):
        """Set power save mode

        Parameters
        ----------
        value : bool
            True to enable power save, False to disable.
        """
        ps = PowerSave.DISABLE
        if value:
            ps = PowerSave.ENABLE

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
        buffer_size = self.eeg_count + 1
        buffer_size_bytes = buffer_size * 4
        buffer = (ctypes.c_uint * buffer_size)()

        handle_error(raw.NVXImpedanceGetData(self.device_handle, buffer, buffer_size_bytes))

        return Impedance(buffer, self.eeg_count)

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
        buffer_size = self.eeg_count + 1
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
    def impedance_scan_frequency(self):
        """Get the impedance scanning frequency, in Hz
        While internally frequency is used as an enum (structs.ScanFreq) packaged in
        a struct (structs.ImpedanceSettings), this function returns an int for convenience.

        Returns
        -------
        int
            impedance scan frequency value (30 or 80 Hz). See also structs.ScanFreq
        """
        imp_settings = ImpedanceSettings()
        handle_error(raw.NVXImpedanceGetSettings(self.device_handle, ctypes.byref(imp_settings)))
        scan_freq = imp_settings.scan_freq

        if scan_freq == ScanFreq.HZ_30:
            return 30
        return 80

    @impedance_scan_frequency.setter
    def impedance_scan_frequency(self, value):
        """Set the impedance scanning frequency
        While internally frequency is used as an enum (structs.ScanFreq) packaged in
        a struct (structs.ImpedanceSettings), this function accepts an int for convenience.

        Raises
        ------
        ValueError
            if passed gain value is not 30 or 80.

        Parameters
        ----------
        value : int
            impedance scan frequency value value. See also structs.ScanFreq
        """
        imp_settings = ImpedanceSettings()
        if value == 30:
            imp_settings.scan_freq = ScanFreq.HZ_30
        elif value == 80:
            imp_settings.scan_freq = ScanFreq.HZ_80
        else:
            raise ValueError("expected a frequency value of either 30 or 80, got " + str(value))
        handle_error(raw.NVXImpedanceSetSettings(self.device_handle, ctypes.byref(imp_settings)))

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
        # TODO: ask how many electrodes there are (assuming self.eeg_count + GND)
        buffer_size = self.eeg_count + 1
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
        # TODO: ask how large the array should be (assuming self.eeg_count + GND)
        buffer_size = self.eeg_count + 1
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
        buffer_size = self.eeg_count + self.aux_count
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
        buffer_size = self.eeg_count + self.aux_count
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
