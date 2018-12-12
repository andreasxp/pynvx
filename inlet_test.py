from nvx_inlet import NVXInlet
import nvx
import time


def inlet_test():
    nvx.set_emulation(True)
    inlet = NVXInlet(index=0, fs=10000, eeg_channels=[1, 2, 3, 4, 5, 6, 7, 8], aux_channels=[0])

    print(inlet.device.get_settings().rate)

    while True:
        time.sleep(0.1)
        chunk = inlet.pull_chunk()

        if len(chunk) != 0:
            print("Have data: " + str(len(chunk)))
        # print(chunk)

        '''for piece in chunk:
            print(piece)'''


if __name__ == '__main__':
    inlet_test()
