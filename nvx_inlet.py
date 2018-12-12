from nvx import Device
from nvx.structs import Rate


class NVXInlet:
    def __init__(self, index, fs, eeg_channels, aux_channels):
        self.device = Device(index)
        self.eeg_channels = eeg_channels
        self.aux_channels = aux_channels

        self.total_counter = 0
        self.accepted_counter = 0

        # Figure out what sampling frequency to use and how much to downsample
        sample_rate = None
        self.sample_ratio = 0  # Ratio representing how many samples are accepted to how many will come in
        if fs <= 10000:
            sample_rate = Rate.KHZ_10
            self.sample_ratio = fs / 10000
        elif fs <= 50000:
            sample_rate = Rate.KHZ_50
            self.sample_ratio = fs / 50000
        elif fs <= 100000:
            sample_rate = Rate.KHZ_100
            self.sample_ratio = fs / 100000
        else:
            raise ValueError("sampling frequency too high: must be not more than 100000, got " + str(fs))

        # Set sampling frequency
        settings = self.device.get_settings()
        settings.rate = sample_rate
        self.device.set_settings(settings)

        # Maybe you should not start this right away, and instead add start and stop methods
        self.device.start()

    # Process a sample
    # Increments necessary counters, returns True if sample to be accepted
    def _process_sample(self):
        current_ratio = 0
        if self.total_counter != 0:
            current_ratio = self.accepted_counter / self.total_counter

        self.total_counter += 1

        if current_ratio <= self.sample_ratio:
            # Accept sample
            self.accepted_counter += 1
            return True
        else:
            # Reject sample
            return False

    def pull_chunk(self):
        result = []

        # Get new sample (returns None if no samples left)
        sample = self.device.get_data()
        while sample is not None:
            if self._process_sample():
                # Part of a matrix/data sample with only some select channels
                trimmed_sample = []

                # Push all required eeg channels' data
                for eeg_channel in self.eeg_channels:
                    trimmed_sample.append(sample.eeg_data(eeg_channel))

                # Push all required aux channels' data
                for aux_channel in self.aux_channels:
                    trimmed_sample.append(sample.aux_data(aux_channel))

                # Append sample to the matrix
                result.append(trimmed_sample)

            # Get new sample
            sample = self.device.get_data()

        return result

