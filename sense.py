from read_sensors.read_ph import CalibratedPHReader
from read_sensors.read_ec import CalibratedECReader
import time
import os
ph_reader = CalibratedPHReader()
ec_reader = CalibratedECReader()

if __name__ == "__main__":
    while True:
        print(f'\rcurrent pH level (the acidity of the water, we want 5.8 +-0.1): {ph_reader.read_ph()} current ec level (the amount of fertilizer in the water, we want 1.8 +-0.1): {ec_reader.read_ec()}', end="\r", flush=True)

