from nvx import Device
from nvx.structs import Rate
import time
from threading import Thread, Lock


class NVXInlet:
    def __init__(self, index, fs, delay_tolerance=0.0):
        self.device = Device(index)
        self.delay_tolerance = delay_tolerance

        # Downsampling -------------------------------------------------------------------------------------------------
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

        # Data collecting ----------------------------------------------------------------------------------------------
        self.buffer = []
        self.buffer_lock = Lock()
        self.collector_thread = Thread(target=self._collect)
        self.stop_flag = False

    def start(self):
        self.device.start()
        self.collector_thread.start()

    def stop(self):
        self.stop_flag = True
        self.device.stop()
        self.collector_thread.join()

    def _collect(self):
        while not self.stop_flag:
            # Get new sample (returns None if no samples left)
            sample = self.device.get_data()
            if sample is not None and self._process_sample():
                self.buffer_lock.acquire()
                try:
                    self.buffer.append(sample)
                finally:
                    self.buffer_lock.release()
            if sample is None and self.delay_tolerance > 0:
                time.sleep(self.delay_tolerance)

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
        self.buffer_lock.acquire()
        result = None
        try:
            result, self.buffer = self.buffer, []
        finally:
            self.buffer_lock.release()
        return result

    def __del__(self):
        self.stop()
