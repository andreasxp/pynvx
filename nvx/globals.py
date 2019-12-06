"""Global variables defined by the driver."""

DEVICES_COUNT_MAX = 3
"""Max devices count connected to media converter"""

EL_LED_OFF = 0  # LEDs are off
EL_LED_GREEN = 1 << 0
EL_LED_RED = 1 << 1
EL_LED_YELLOW = EL_LED_GREEN | EL_LED_RED
"""Electrodes LEDs definitions"""

EL_SWITCH_ON = 1 << 2  # input analog switch to GND
EL_SWITCH_OFF = 0 << 2  # input analog switch to input
"""Electrodes analog switch definition"""

PLL_FREQ_MAX = int(27e6)
