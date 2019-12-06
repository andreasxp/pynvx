"""NVX-136 adapter for python.
NVX-136 is an amplifier for EEG recordings. This python module provides a way to interface with the hardware using a
wrapper, using the driver written in C as a dll.
"""
# Expose important parts as members nvx
from .base import raw, get_dll_version, set_emulation, get_count
from .structs import Version, Settings, Property, DataStatus, ErrorStatus, Gain, PowerSave, \
    ImpedanceSetup, ImpedanceMode, ImpedanceSettings, Voltages, FrequencyBandwidth, Pll
from .device import Device
from .sample import Sample
from .impedance import Impedance
from .ring_buffer import RingBuffer
