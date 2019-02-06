from nvx import Device


class NVXInlet:
    def __init__(self, index, fs, delay_tolerance=0.0):
        self.device = Device(index)
        self.device.delay_tolerance = delay_tolerance
        self.device.rate = fs

    def start(self):
        self.device.start()

    def stop(self):
        self.device.stop()

    def pull_chunk(self):
        return self.device.pull_chunk()
