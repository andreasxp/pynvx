# pynvx
NVX wrapper for python.

## Installation
```
git clone https://github.com/andreasxp/pynvx
pip install -e pynvx
```

## Example usage
```python
import nvx

nvx.set_emulation(True)  # set emulation state, adds 1 pseudo-device
dev = nvx.Device(0)  # create a device with index 0

try:
    print("Collecting data. Ctrl-C to stop")
    print("Showing only some of the channels:")
    print("EEG channel 1|EEG channel 2|EEG channel 3|AUX channel 1|Counter")
    input("Press any key to start gathering data...")
    dev.start()  # start collecting data

    while True:
        samples = dev.pull_chunk()  # Get all collected data samples
        for sample in samples:   # While there is sample to recieve, do stuff with it
            print('EEG1:{:>8}|EEG2:{:>8}|EEG3:{:>8}|AUX1:{:>8}|COUNT:{:>8}'.format(
                sample.eeg_data(0),
                sample.eeg_data(1),
                sample.eeg_data(2),
                sample.aux_data(0),
                sample.counter  # Counts samples
            ))

except KeyboardInterrupt:
    pass

dev.stop()
```

## License
`pynvx` is licenced under the MIT license. It is free for personal commercial use. Note that the files listed under `nvx/dll` belong to [Medical Computer Systems Ltd](https://mks.ru/en/index/) and are subject to their own license and copyright.