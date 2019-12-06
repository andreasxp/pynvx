"""A collection of wrappers for C structs defined by the driver."""
import ctypes
from .c_enum import CEnum
from .globals import DEVICES_COUNT_MAX


class Version(ctypes.Structure):
    """Version info about NVX."""
    _fields_ = [
        ('dll', ctypes.c_ulonglong),
        ('driver', ctypes.c_ulonglong),
        ('cypress', ctypes.c_ulonglong),
        ('mc_fpga', ctypes.c_ulonglong),  # media converter fpga
        ('msp430', ctypes.c_ulonglong),
        ('cb_fpga', ctypes.c_ulonglong)  # carrier board fpga
    ]


class Mode(CEnum):
    """Mode enum."""
    NORMAL = 0  # normal data acquisition
    ACTIVE_SHIELD = 1  # data acquisition with ActiveShield
    IMPEDANCE = 2  # impedance measure
    TEST = 3  # test signal (square wave 200 uV, 1 Hz)
    GND = 4  # all electrodes connected to gnd
    IMP_GND = 5  # impedance measure, all electrodes connected to gnd


class Rate(CEnum):
    """Samples rate (physical) enum."""
    KHZ_10 = 0  # 10 kHz, all channels (default mode)
    KHZ_50 = 1  # 50 kHz, all channels
    KHZ_100 = 2  # 100 kHz, max 64 channels


class AdcFilter(CEnum):
    """ADC data filter, obsolete, not used."""
    NATIVE = 0  # no ADC data filter
    AVERAGING_2 = 1  # ADC data moving averaging filter by 2 samples


class Decimation(CEnum):
    """ADC data decimation."""
    DCM_0 = 0  # no decimation
    DCM_2 = 2  # decimation by 2
    DCM_5 = 5
    DCM_10 = 10
    DCM_20 = 20
    DCM_40 = 40


class Settings(ctypes.Structure):
    _fields_ = [
        ('mode', Mode),  # mode of acquisition
        ('rate', Rate),  # samples rate
        ('adc_filter', AdcFilter),  # ADC data filter, obsolete, not used
        ('decimation', Decimation),  # media converter fpga
    ]


class Property(ctypes.Structure):
    """Device property structure."""
    _fields_ = [
        ('count_eeg', ctypes.c_uint),  # numbers of Eeg channels
        ('count_aux', ctypes.c_uint),  # numbers of Aux channels
        ('triggers_in', ctypes.c_uint),  # numbers of input triggers
        ('triggers_out', ctypes.c_uint),  # numbers of output triggers
        ('rate', ctypes.c_float),  # Sampling rate, Hz
        ('resolution_eeg', ctypes.c_float),  # EEG amplitude scale coefficients, V/bit
        ('resolution_aux', ctypes.c_float),  # AUX amplitude scale coefficients, V/bit
        ('range_eeg', ctypes.c_float),  # EEG input range peak-peak, V
        ('range_aux', ctypes.c_float)  # AUX input range peak-peak, V
    ]


class Gain(CEnum):
    """Device gain structure."""
    GAIN_1 = 0  # gain = 1
    GAIN_5 = 1  # gain = 5


class PowerSave(CEnum):
    """Device power saving structure."""
    DISABLE = 0  # power save disable
    ENABLE = 1  # power save enable, only 64 Eeg channels and Aux


class DataStatus(ctypes.Structure):
    """Device property structure."""
    _fields_ = [
        ('samples', ctypes.c_uint),  # total samples
        ('errors', ctypes.c_uint),  # total errors
        ('rate', ctypes.c_float),  # data rate, Hz
        ('speed', ctypes.c_float)  # data speed, MB/s
    ]


class ErrorStatus(ctypes.Structure):
    """Device error status."""
    _fields_ = [
        ('samples', ctypes.c_uint),  # total samples
        ('crc', ctypes.c_uint),  # crc errors on data samples
        ('counter', ctypes.c_uint),  # counter errors on data samples
        ('devices', ctypes.c_uint * DEVICES_COUNT_MAX)  # errors on devices
    ]


class ImpedanceSetup(ctypes.Structure):
    """Impedance setup structure.

    Between Good and Bad level is indicate as both leds (yellow emulation).
    """
    _fields_ = [
        ('good', ctypes.c_uint),  # good level (green led indication), Ohm
        ('bad', ctypes.c_uint),  # bad level (red led indication), Ohm
        ('leds_disable', ctypes.c_uint),  # disable electrode's LEDs, if not zero
        ('timeout', ctypes.c_uint * DEVICES_COUNT_MAX)  # impedance mode timeout (0 - 65535), sec
    ]


class ImpedanceMode(ctypes.Structure):
    """Impedance control structure."""
    _fields_ = [
        # read-write information
        ('splitter', ctypes.c_uint),  # Current splitter for impedance measure, (0 .. splitters - 1).
                                      # if splitter == splitters, measure on all electrodes)
        # read-only information, ignored when write (set)
        ('splitters', ctypes.c_uint),  # count of splitters in actiCap device
        ('electrodes', ctypes.c_uint),  # electrodes channels count
        ('electrode_from', ctypes.c_uint),  # electrode from which impedance measure
        ('electrode_to', ctypes.c_uint),  # electrode to which impedance measure
        ('time', ctypes.c_uint)  # time in impedance mode, sec
    ]


class ScanFreq(CEnum):
    """Impedance scanning frequency structure."""
    HZ_30 = 0  # freq = 30 Hz
    HZ_80 = 1  # freq = 80 Hz


class ImpedanceSettings(ctypes.Structure):
    """Impedance settings structure."""
    _fields_ = [
        ('scan_freq', ScanFreq),  # scanning frequency
    ]


class Voltages(ctypes.Structure):
    _fields_ = [
        ('VDC', ctypes.c_float),  # power supply, V
        ('AVDD5A1', ctypes.c_float),  # analog-1 5.0, V
        ('AVDD5A2', ctypes.c_float),  # analog-2 5.0, V
        ('AVDD5AUX', ctypes.c_float),  # analog Aux 5.0, V
        # + mux
        # + voltages valid only during data acquisition
        ('DVDD3V3', ctypes.c_float),  # digital 3.3, V
        ('DVDD1V8', ctypes.c_float),  # digital 1.8, V
        ('DVDD1V2', ctypes.c_float),  # digital 1.2, V
        ('AVCC1', ctypes.c_float),  # analog VCC1
        ('AVCC2', ctypes.c_float),  # analog VCC2
        ('AVCC3', ctypes.c_float),  # analog VCC3
        ('AVCC4', ctypes.c_float),  # analog VCC4
        ('temperature', ctypes.c_float)  # celsius degrees
    ]


class FrequencyBandwidth(ctypes.Structure):
    """Frequency bandwidth structure."""
    _fields_ = [
        ('sample_rate', ctypes.c_uint),  # sample rate of device, mHz
        ('cutoff_freq', ctypes.c_uint),  # cutoff frequency of the -3 dB, mHz
        ('decim_from_rate', Rate),  # decimation from rate
        ('decimation', Decimation),  # decimation value
    ]


class Pll(ctypes.Structure):
    _fields_ = [
        ('pll_external', ctypes.c_uint),  # if 1 - use External clock for PLL, if 0 - use Internal 48 MHz
        ('adc_external', ctypes.c_uint),  # if 1 - out External clock to ADC, if 0 - use PLL output
        ('pll_frequency', ctypes.c_uint),  # PLL frequency (needs set if AdcExternal = 0), Hz
        ('phase', ctypes.c_uint),  # phase shift, degrees
        ('status', ctypes.c_uint)  # PLL status (read-only)
    ]













