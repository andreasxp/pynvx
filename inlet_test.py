from nvx_inlet import NVXInlet
import nvx
import time


def inlet_test():
    nvx.set_emulation(True)
    inlet = NVXInlet(index=0, fs=1000, delay_tolerance=0.01)
    inlet.start()

    start_time = time.time()

    while time.time() - start_time < 10:
        time.sleep(0.1)
        pull_time = time.time()
        chunk = inlet.pull_chunk()

        #if len(chunk) != 0:
        #    print("Have data: " + str(len(chunk)))
        # print(chunk)

        print("Pulled " + str(len(chunk)) + " chunks in " + str(time.time() - pull_time) + "s")

        sample = chunk[0]
        print("Fc3: "    + str(sample["Fc3"]))
        print("Aux2.1: " + str(sample["Aux2.1"]))

        '''for piece in chunk:
            print(piece)'''

    inlet.stop()
    print("Done.")


if __name__ == '__main__':
    inlet_test()
