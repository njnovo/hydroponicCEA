import serial
import time
import json
import os

class CalibratedECReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB1'
        self.baud_rate = 9600

    def send_command(ser, cmd):
        full_cmd = cmd + '\r'
        ser.write(full_cmd.encode())
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        print(f">>> {cmd}")
        print(f"<<< {response}")
        return response
    
    def read_raw_ec(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                return self.send_command(ser, "R")
                
        except Exception as e:
            print(f"Error reading EC: {e}")
            return None
    
    def read_ec(self):
        raw_value = self.read_raw_ec()
        raw_value.split(",")
        return float(raw_value[:4])


if __name__ == "__main__":
    reader = CalibratedECReader()
    while True:
        print(reader.read_ec())
        time.sleep(.5)