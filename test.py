import nvx


def test():
    nvx.set_emulation(True)  # set emulation state, adds 1 pseudo-device
    dev = nvx.Device(0)  # create a device with index 0

    try:
        print("Collecting data. Ctrl-C to stop")
        print("Showing only some of the channels:")
        print("EEG channel 1|EEG channel 2|EEG channel 3|AUX channel 1|Counter")
        input("Press any key to start gathering data...")
        dev.start()  # start collecting data

        while True:
            sample = dev.get_data()  # Get one sample of data
            while sample is not None:   # While there is sample to recieve, do stuff with it
                print('EEG1:{:>8}|EEG2:{:>8}|EEG3:{:>8}|AUX1:{:>8}|COUNT:{:>8}'.format(
                    sample.eeg_data(0),
                    sample.eeg_data(1),
                    sample.eeg_data(2),
                    sample.aux_data(0),
                    sample.counter()  # Counts samples
                ))
                sample = dev.get_data()

    except KeyboardInterrupt:
        pass

    dev.stop()


if __name__ == '__main__':
    test()
