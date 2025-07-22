import serial
import time
import json
import os

class CalibratedECReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 9600

    def send_command(self,ser, cmd):
        full_cmd = cmd + '\r'
        ser.write(full_cmd.encode())
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        return response.split(",")[0]
    
    def read_ec(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                return float(self.send_command(ser, "R"))/1000
                
        except Exception as e:
            print(f"Error reading EC: {e}")
            return None

if __name__ == "__main__":
    reader = CalibratedECReader()
    while True:
        time.sleep(.5)
        print(reader.read_ec())
