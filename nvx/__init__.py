"""
NVX adapter for python

"""
# Expose important parts as members nvx
from .base import raw, get_dll_version, set_emulation, get_count
from .structs import Version, Settings, Property, DataStatus, ErrorStatus, Gain, PowerSave, \
    ImpedanceSetup, ImpedanceMode, ImpedanceSettings, Voltages, FrequencyBandwidth, Pll
from .device import Device
from .sample import Sample
from .impedance import Impedance
