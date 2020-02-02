/*----------------------------------------------------------------------------*/
/*
  NVX DLL header file
*/
/*----------------------------------------------------------------------------*/
#ifndef ModID_NVX_H
#define ModID_NVX_H
/*----------------------------------------------------------------------------*/
/* Includes */

/*----------------------------------------------------------------------------*/
/* Defines */

#ifdef __cplusplus
#define EXTERN_C extern "C"
#else
#define EXTERN_C
#endif

#ifdef nvx_EXPORTS
/*! NVX_API functions as being exported from a DLL */
#define NVX_API EXTERN_C __declspec(dllexport)
#else
/*! NVX_API functions as being imported from a DLL */
#define NVX_API EXTERN_C __declspec(dllimport)
#endif

/*! Error codes */
#define NVX_ERR_OK			(0)		/*!< Success (no errors) */
#define NVX_ERR_HANDLE		(-1)	/*!< Invalid handle (such handle not present now) */
#define NVX_ERR_PARAM		(-2)	/*!< Invalid function parameter(s) */
#define NVX_ERR_FAIL		(-3)	/*!< Function fail (internal error) */
#define NVX_ERR_DATA_RATE	(-4)	/*!< Data rate error */

/*! Invalid (not connected) impedance value */
#define NVX_IMP_INVALID (INT_MAX)

/*! Max devices count connected to media converter */
#define NVX_DEVICES_COUNT_MAX (3)

/*! Electrodes leds definitions */
#define NVX_EL_LED_OFF (0) /* Off leds */
#define NVX_EL_LED_GREEN (1 << 0) /* Green led on */
#define NVX_EL_LED_RED (1 << 1) /* Red led on */
#define NVX_EL_LED_YELLOW (AC_EL_LED_GREEN | AC_EL_LED_RED) /* Yellow led on */

/*! Electrodes analog switch definition */
#define NVX_EL_SWITCH_ON (1 << 2) /* Input analog switch to GND */
#define NVX_EL_SWITCH_OFF (0 << 2) /* Input analog switch to input */
/*----------------------------------------------------------------------------*/
/* Data Types */

#pragma pack(push, 1) /* override default packing for structures */

/* Version info about NVX */
typedef struct {
  unsigned long long Dll;
  unsigned long long Driver;
  unsigned long long Cypress;
  unsigned long long McFpga; /* media converter fpga */
  unsigned long long Msp430;
  unsigned long long CbFpga; /* carrier board fpga */
} t_NVXVersion;

/*! Mode enum */
typedef enum {
  NVX_MODE_NORMAL = 0, /* normal data acquisition */
  NVX_MODE_ACTIVE_SHIELD = 1, /* data acquisition with ActiveShield */
  NVX_MODE_IMPEDANCE = 2, /* impedance measure */
  NVX_MODE_TEST = 3, /* test signal (square wave 200 uV, 1 Hz)  */
  NVX_MODE_GND = 4, /* all electrodes connected to gnd */
  NVX_MODE_IMP_GND = 5, /* impedance measure, all electrodes connected to gnd */
} t_NVXMode;

/*! Samples rate (physical) enum */
typedef enum {
  NVX_RATE_10KHZ = 0, /* 10 kHz, all channels (default mode) */
  NVX_RATE_50KHZ = 1, /* 50 kHz, all channels */
  NVX_RATE_100KHZ = 2, /* 100 kHz, max 64 channels */
} t_NVXRate;

/*!  ADC data filter, obsolete, not used */
typedef enum {
	NVX_ADC_NATIVE = 0, /* no ADC data filter */
	NVX_ADC_AVERAGING_2 = 1, /* ADC data moving avaraging filter by 2 samples */
} t_NVXAdcFilter;

/*!  ADC data decimation */
typedef enum {
	NVX_DECIMATION_0 = 0, /* no decimation */
	NVX_DECIMATION_2 = 2, /* decimation by 2 */
	NVX_DECIMATION_5 = 5, /* decimation by 5 */
    NVX_DECIMATION_10 = 10, /* decimation by 10 */
    NVX_DECIMATION_20 = 20, /* decimation by 20 */
    NVX_DECIMATION_40 = 40, /* decimation by 40 */
} t_NVXDecimation;

typedef struct {
  t_NVXMode Mode; /* mode of acquisition */
  t_NVXRate Rate; /* samples rate */
  t_NVXAdcFilter AdcFilter; /* ADC data filter, obsolete, not used */
  t_NVXDecimation Decimation; /* ADC data decimation */
} t_NVXSettings;

/*! Device property structure */
typedef struct {
  unsigned int CountEeg;	/* numbers of Eeg channels */
  unsigned int CountAux;	/* numbers of Aux channels */
  unsigned int TriggersIn;  /* numbers of input triggers */
  unsigned int TriggersOut;	/* numbers of output triggers */
  float Rate;					/*!< Sampling rate, Hz */
  float ResolutionEeg;			/*!< EEG amplitude scale coefficients, V/bit */
  float ResolutionAux;			/*!< AUX amplitude scale coefficients, V/bit */
  float RangeEeg;				/*!< EEG input range peak-peak, V */
  float RangeAux;				/*!< AUX input range peak-peak, V */
} t_NVXProperty;

/*! Device gain structure */
typedef enum {
	NVX_GAIN_1 = 0, /* gain = 1 */
	NVX_GAIN_5 = 1, /* gain = 5 */
} t_NVXGain;

/*! Device power saving structure */
typedef enum {
	NVX_POWER_SAVE_DISABLE = 0, /* power save disable */
	NVX_POWER_SAVE_ENABLE = 1, /* power save enable, only 64 Eeg channels and Aux */
} t_NVXPowerSave;

/*! Device data status */
typedef struct {
  unsigned int Samples; /* Total samples */
  unsigned int Errors; /* Total errors */
  float Rate; /*!< Data rate, Hz */
  float Speed; /*!< Data speed, MB/s */
} t_NVXDataStatus;

/*! Device error status */
typedef struct {
  unsigned int Samples; /* Total samples */
  unsigned int Crc; /* Crc errors on data samples */
  unsigned int Counter; /* Counter errors on data samples */
  unsigned int Devices[NVX_DEVICES_COUNT_MAX]; /* Errors on devices */
} t_NVXErrorStatus;

/*! Impedance setup structure */
typedef struct {
  /*!< Between Good and Bad level is indicate as both leds (yellow emulation)*/
  unsigned int Good; /*!< Good level (green led indication), Ohm */
  unsigned int Bad; /*!< Bad level (red led indication), Ohm */
  unsigned int LedsDisable; /*!< Disable electrode's leds, if not zero */
  unsigned int TimeOut; /*!< Impedance mode time-out (0 - 65535), sec */
} t_NVXImpedanceSetup;

/*! Impedance control structure */
typedef struct {
  /* READ-WRITE information */
  unsigned int Splitter; /*!< Current splitter for impedance measure, (0 .. Splitters - 1) */
						 /*!< if = Splitters, measure on all electrodes) */
  /* READ-ONLY information, ignored when write (set) */
  unsigned int Splitters; /*!< Count of splitters in actiCap device */
  unsigned int Electrodes; /*!< Electrodes channels count */
  unsigned int ElectrodeFrom; /*!< Electrode from which impedance measure */
  unsigned int ElectrodeTo; /*!< Electrode to which impedance measure */
  unsigned int Time; /*!< Time in impedance mode, sec */
} t_NVXImpedanceMode;

/*! Impedance scanning frequency structure */
typedef enum {
	NVX_SCAN_FREQ_30 = 0, /* freq = 30 Hz */
	NVX_SCAN_FREQ_80 = 1, /* freq = 80 Hz */
} t_NVXScanFreq;

/*! Impedance settings structure */
typedef struct {
  t_NVXScanFreq ScanFreq; /*!< Scanning frequency */
} t_NVXImpedanceSettings;

typedef struct {
  float VDC;  /*!< Power supply, V */
  float AVDD5A1; /*!< Analog-1 5.0, V */
  float AVDD5A2; /*!< Analog-2 5.0, V */
  float AVDD5AUX; /*!< Analog Aux 5.0, V */
  // + mux
  // + voltages valid only during data acquisition
  float DVDD3V3; /*!< Digital 3.3, V */
  float DVDD1V8; /*!< Digital 1.8, V */
  float DVDD1V2; /*!< Digital 1.2, V */
  float AVCC1; /*!< Analog VCC1 */
  float AVCC2; /*!< Analog VCC2 */
  float AVCC3; /*!< Analog VCC3 */
  float AVCC4; /*!< Analog VCC4 */

  float Temperature; /*!< Celsius degrees */
} t_NVXVoltages;

/*! Frequency bandwidth structure */
typedef struct {
  unsigned int SampleRate; /*!<  Sample rate of device, mHz */
  unsigned int CutoffFreq; /*!< Cutoff frequency of the -3 dB, mHz */
  t_NVXRate DecimFromRate; /*!< Decimation from rate */
  t_NVXDecimation Decimation; /*!< Decimation value */
} t_NVXFrequencyBandwidth;

#pragma pack(pop) /* restore default packing for structures */
/*----------------------------------------------------------------------------*/
/* Functions */
/*----------------------------------------------------------------------------*/

/*!
  Function to set device emulation.
\param Enable - 32-bit variable: if 0 - device emulation disable, if 1 - device emulation enable
\return - error code
*/
NVX_API int NVXSetEmulation(unsigned int Enable);

/*!
  Function to get version info about NVX.
  Note:
  - if hDevice = NULL, only Dll version is valid.
\param hDevice - device handle
\param Version - pointer to structure with version
\return - error code
*/
NVX_API int NVXGetVersion(void *hDevice, t_NVXVersion *Version);

/*----------------------------------------------------------------------------*/
/*!
  Function return count of device currently connected to system.
\return - device count
*/
NVX_API unsigned int NVXGetCount(void);

/*----------------------------------------------------------------------------*/
/*!
  Function to open device for work.
\param Number - device number from 0 to NVXGetCount()
\return - device handle or NULL (if fail)
*/
NVX_API void* NVXOpen(unsigned int Number);

/*----------------------------------------------------------------------------*/
/*!
  Function to close device.
\param hDevice - device handle
\return - error code
*/
NVX_API int NVXClose(void *hDevice);

/*----------------------------------------------------------------------------*/
/*!
  Function to get device settings for acquisition.
\param hDevice - device handle
\param Settings - pointer to structure with settings
\return - error code
*/
NVX_API int NVXGetSettings(void *hDevice, t_NVXSettings *Settings);

/*----------------------------------------------------------------------------*/
/*!
  Function to set device settings for acquisition.
\param hDevice - device handle
\param Settings - pointer to structure with settings
\return - error code
*/
NVX_API int NVXSetSettings(void *hDevice, t_NVXSettings *Settings);

/*----------------------------------------------------------------------------*/
/*!
  Function to get device property of acquisition.
\param hDevice - device handle
\param Settings - pointer to structure with settings
\return - error code
*/
NVX_API int NVXGetProperty(void *hDevice, t_NVXProperty *Property);

/*----------------------------------------------------------------------------*/
/*!  
  Function to start data acquisition.
\param hDevice - device handle
\return - error code
*/
NVX_API int NVXStart(void *hDevice);

/*----------------------------------------------------------------------------*/
/*!  
  Function to stop data acquisition.
\param hDevice - device handle
\return - error code
*/
NVX_API int NVXStop(void *hDevice);

/*----------------------------------------------------------------------------*/
/*!  
  Function return accusition data from internal buffer.
  
  Data return format:
  
  Field										Offset in bytes			Type
  Data from the first channel				0						signed int
  Data from the second channel				4						signed int
  ...
  Data from the N channel					(N - 1) * 4				signed int
  Auxiliary data from the first channel		N * 4					signed int
  Auxiliary data from the second channel	N * 4 + 4				signed int
  ...
  Auxiliary data from the M channel			N * 4 + (M - 1) * 4		signed int
  Status									N * 4 + M * 4			unsigned int
  Counter									N * 4 + M * 4 + 4		unsigned int
  
  Where, N - numbers of Eeg channels, M - numbers of Aux channels, get from function NVXGetProperty.
  
  Field Status - Digital inputs (bits 0 - 7) + output (bits 8 - 15) state + 16 MSB reserved bits
  Field Counter - 32-bit data sequencing cyclic counter for checking the data loss.
  
  Needs call this function until not return <= 0, for prevent overflow of internal buffer.
\param hDevice - device handle
\param Buffer - pointer to buffer for device data.
\param Size - size of buffer for device data, bytes.
\return
  if > 0 - count of bytes copied to buffer
  if = 0 - no more data in internal buffer
  if < 0 - error code  
*/
NVX_API int NVXGetData(void *hDevice, void *Buffer, unsigned int Size);

/*----------------------------------------------------------------------------*/
/*!
  Function to get data status of acquisition.
\param hDevice - device handle
\param DataStatus - pointer to structure with data status
\return - error code
*/
NVX_API int NVXGetDataStatus(void *hDevice, t_NVXDataStatus *DataStatus);

/*----------------------------------------------------------------------------*/
/*!
  Function to get error status of acquisition.
\param hDevice - device handle
\param ErrorStatus - pointer to structure with error status
\return - error code
*/
NVX_API int NVXGetErrorStatus(void *hDevice, t_NVXErrorStatus *ErrorStatus);

/*----------------------------------------------------------------------------*/
/*!
  Function to get state of triggers (input and output).
  8-bit inputs (bits 0 - 7) + 8-bit outputs (bits 8 - 15) + 16 MSB reserved bits.
\param hDevice - device handle
\param Triggers - pointer to 32-bit variable for get state of triggers
\return - error code
*/
NVX_API int NVXGetTriggers(void *hDevice, unsigned int *Triggers);

/*----------------------------------------------------------------------------*/
/*!
  Function to set state of triggers (output only).
  8-bit inputs (bits 0 - 7) + 8-bit outputs (bits 8 - 15) + 16 MSB reserved bits.
\param hDevice - device handle
\param Triggers - 32-bit variable for set state of triggers
\return - error code
*/
NVX_API int NVXSetTriggers(void *hDevice, unsigned int Triggers);

/*----------------------------------------------------------------------------*/
/*!
  Function to get aux gain.
\param hDevice - device handle
\param Gain - gain value
\return - error code
*/
NVX_API int NVXGetAuxGain(void *hDevice, t_NVXGain *Gain);

/*----------------------------------------------------------------------------*/
/*!
  Function to set aux gain.
\param hDevice - device handle
\param Gain - gain value (1 or 5)
\return - error code
*/
NVX_API int NVXSetAuxGain(void *hDevice, t_NVXGain Gain);

/*----------------------------------------------------------------------------*/
/*!
  Function to get power save.
\param hDevice - device handle
\param PowerSave - power save value
\return - error code
*/
NVX_API int NVXGetPowerSave(void *hDevice, t_NVXPowerSave *PowerSave);

/*----------------------------------------------------------------------------*/
/*!
  Function to set power save.
  Note:
  -call before NVXSetChannelsEnabled function.
\param hDevice - device handle
\param PowerSave - power save value (0 or 1)
\return - error code
*/
NVX_API int NVXSetPowerSave(void *hDevice, t_NVXPowerSave PowerSave);

/*----------------------------------------------------------------------------*/
/*!
  Function to get impedance values for all EEG channels and ground in Ohm.

  Remarks (notes):
  - ~750 ms is required for measure impedance per 32 electrodes.
  - max impedance value ~ 300-500 kOhm
  - impedance measure from 0 Ohm to 120 kOhm with accuracity +/- 15%
  - work only in impedance mode.
  - ground electrode must be connected for impedance measure.
  - REF electrode (1-st electrode on 1-st module) must be connected for impedance measure.
  - if electrode not connect, value equal to NVX_IMP_INVALID(INT_MAX from <limits.h>)

\param hDevice - device handle
\param Buffer - pointer to destination buffer values in Ohm 
  for N channels (equal CountEeg field in t_NVXProperty) + 1 GND (ground).
\param Size - size of destination buffer, bytes
\return - error code
*/
NVX_API int NVXImpedanceGetData(void *hDevice, unsigned int *Buffer, unsigned int Size);

/*----------------------------------------------------------------------------*/
/*!
  Function to get setup for impedance mode.
\param hDevice - device handle
\param Setup - settings for impedance mode
\return - error code
*/
NVX_API int NVXImpedanceGetSetup(void *hDevice, t_NVXImpedanceSetup *Setup);

/*----------------------------------------------------------------------------*/
/*!
  Function to set setup for impedance mode.
\param hDevice - device handle
\param Setup - settings for impedance mode
\return - error code
*/
NVX_API int NVXImpedanceSetSetup(void *hDevice, t_NVXImpedanceSetup *Setup);

/*----------------------------------------------------------------------------*/
/*!
  Function to get current impedance mode.
  Note:
    - see t_NVXImpedanceMode structure decription,
      fields Splitter, ElectrodeFrom, ElectrodeTo
	  is valid only in impedance mode      
\param hDevice - device handle
\param Control - pointer to t_NVXImpedanceMode structure
\return - error code
*/
NVX_API int NVXImpedanceGetMode(void *hDevice, t_NVXImpedanceMode *Mode);

/*----------------------------------------------------------------------------*/
/*!
  Function to set current impedance mode.
  Note:
    - must call in impedance mode 
    - see t_NVXImpedanceMode structure decription
    - only Splitter field is apply, all other's are ignored      
\param hDevice - device handle
\param Control - pointer to t_NVXImpedanceMode structure
\return - error code
*/
NVX_API int NVXImpedanceSetMode(void *hDevice, t_NVXImpedanceMode *Mode);

/*----------------------------------------------------------------------------*/
/*!
  Function to direct set (control) electrode's state (leds and analog switch) in all modes.

  Remarks (notes):
    - direct control of electrodes is start automatic with call of this function
    - for disable direct control of electrodes call NVXSetElectrodes(Id, NULL, 0)
    - to simplify control is needs to set states of all electrodes at one time
    - for set electrodes colors recomend use NVX_EL_LED_XXX (see defines) values.

  Warning (limitations) of using:
    - During data acquisition due to switching supply current (i.e. leds), 
      analog power supply voltage ripple is appear. Which follows to crosstalk 
      to low level input signal and to distortion (add some pulsation)
      after switching supply current (i.e. leds).
    - in Impedance mode input analog switch is not accessable.
    - in Impedance mode it is not recomend to call this function very frequently 
      (> few times per 1 sec) or to change (from previous state) too many electrodes, 
      because this will significantly increase impedance measure time (cycle) - see below.
    - After success call this function device will execute this command:
	  ~ 50 ms per 32 electrodes states changes from previous state

\param hDevice - device handle
\param Buffer - pointer to source buffer values for electrodes states
  for N channels (equal CountEeg field in t_NVXProperty) + 1 GND (ground).
\param Size - size of source buffer, bytes
\return - error code
*/
NVX_API int NVXSetElectrodes(void *hDevice, unsigned int *Buffer, unsigned int Size);

/*----------------------------------------------------------------------------*/
/*!
  Function to get settings for impedance mode.
\param hDevice - device handle
\param Setup - settings for impedance mode
\return - error code
*/
NVX_API int NVXImpedanceGetSettings(void *hDevice, t_NVXImpedanceSettings *Settings);

/*----------------------------------------------------------------------------*/
/*!
  Function to set settings for impedance mode.
\param hDevice - device handle
\param Setup - settings for impedance mode
\return - error code
*/
NVX_API int NVXImpedanceSetSettings(void *hDevice, t_NVXImpedanceSettings *Settings);

/*----------------------------------------------------------------------------*/
/*!
  Function to get device settings for acquisition.
\param hDevice - device handle
\param Settings - pointer to buffer for results
\return - error code
*/
NVX_API int NVXGetVoltages(void *hDevice, t_NVXVoltages *Voltages);

/*----------------------------------------------------------------------------*/
/*!
  Function to set gain in ActiveShield mode.
  Note:
	- at default gain = 100.
	- gain value must be from 1 to 100
\param hDevice - device handle
\param Gain - gain value (1 - 100)
\return - error code
*/
NVX_API int NVXSetActiveShieldGain(void *hDevice, unsigned int Gain);

/*----------------------------------------------------------------------------*/
/*!
  Function to get polarization of the electrodes.
\param hDevice - device handle
\param Count -  pointer to buffer for polarization data
\param Size - size of buffer for polarization data, bytes
\return - error code
*/
NVX_API int NVXGetPolarization(void *hDevice, double *Buffer, unsigned int Size);

/*----------------------------------------------------------------------------*/
/*!
  Function to get device sample rate count.
\param hDevice - device handle, if hDevice = NULL, then returns default value
\param Count - pointer to 32-bit variable
\return - error code
*/
NVX_API int NVXGetSampeRateCount(void *hDevice, unsigned int *Count);

/*----------------------------------------------------------------------------*/
/*!
  Function to get frequency bandwidth.
\param hDevice - device handle, if hDevice = NULL, then returns default value
\param Count -  pointer to array of t_NVXFrequencyBandwidth
\param Size - size of array of t_NVXFrequencyBandwidth for bandwidth data, bytes
\return - error code
*/
NVX_API int NVXGetFrequencyBandwidth(void *hDevice, t_NVXFrequencyBandwidth *FrequencyBandwidth, unsigned int Size);

/*----------------------------------------------------------------------------*/
/*!
  Function to get channels enabled.
\param hDevice - device handle
\param Count -  pointer to buffer for channels
\param Size - size of buffer for channels, Size = (CountEeg + CountAux) * sizeof(bool) bytes,
  CountEeg and CountAux get from field in t_NVXProperty
\return - error code
*/
NVX_API int NVXGetChannelsEnabled(void *hDevice, bool *Buffer, unsigned int Size);


/*----------------------------------------------------------------------------*/
/*!
  Function to set channels enabled.
  Note: 
	-call only in stop mode;
	-call after NVXSetPowerSave function.
\param hDevice - device handle
\param Count -  pointer to buffer for channels
\param Size - size of buffer for channels, Size = (CountEeg + CountAux) * sizeof(bool) bytes,
  CountEeg and CountAux get from field in t_NVXProperty
\return - error code
*/
NVX_API int NVXSetChannelsEnabled(void *hDevice, bool *Buffer, unsigned int Size);

/*----------------------------------------------------------------------------*/
#define NVX_PLL_FREQ_MAX ((int)27.0e6)

typedef struct {
  unsigned int PllExternal; /* if 1 - use External clock for PLL, if 0 - use Internal 48 MHz */
  unsigned int AdcExternal; /* if 1 - out External clock to ADC, if 0 - use PLL output */
  unsigned int PllFrequency; /* PLL frequency (needs set if AdcExternal = 0), Hz */
  unsigned int Phase; /* Phase shift, degrees */
  // + Read-only
  unsigned int Status; /* PLL status */
} t_NVXPll;

NVX_API int NVXGetPll(void *hDevice, t_NVXPll *Pll);
NVX_API int NVXSetPll(void *hDevice, t_NVXPll *Pll);
/*----------------------------------------------------------------------------*/
#endif /* ModID_XXX_H */
