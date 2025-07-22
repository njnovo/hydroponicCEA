from read_sensors.read_ph import CalibratedPHReader
from read_sensors.read_ec import CalibratedECReader
import time

ph_reader = CalibratedPHReader()
ec_reader = CalibratedECReader()

if __name__ == "__main__":
    while True:
        print(ph_reader.read_ph())
        print(ec_reader.read_ec())
        time.sleep(1)
