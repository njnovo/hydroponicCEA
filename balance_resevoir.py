def __main__():
    import read_sensors.read_ph.CalibratedPHReader
    import read_sensors.read_ec.CalibratedECReader

    ph_reader = read_sensors.read_ph.CalibratedPHReader()
    ec_reader = read_sensors.read_ec.CalibratedECReader()

    while True:
        ph = ph_reader.read_calibrated_ph()
        ec = ec_reader.read_raw_ec()
        print(f"PH: {ph}, EC: {ec}")
        if(ph < 5.7):
            print("PH is too low, adding acid")
        elif(ph > 5.9):
            print("PH is too high, adding base")
        else:
            print("PH is within range")
        if(ec < 1000):
            print("EC is too low, adding fertilizer")
        elif(ec > 1200):
            print("EC is too high, oops, this code didn't work...")
        else:
            print("EC is within range")
        time.sleep(3600)
