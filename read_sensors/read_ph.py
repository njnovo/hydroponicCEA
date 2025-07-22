import serial
import time
import json
import os

class CalibratedPHReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB1'
        self.baud_rate = 9600

    def send_command(self, ser, cmd):
        full_cmd = cmd + '\r'
        ser.write(full_cmd.encode())
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        return response.split(",")[0]
    
    def read_ph(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                return float(self.send_command(ser, "r"))
                
        except Exception as e:
            print(f"Error reading pH: {e}")
            return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    while True:
        time.sleep(.5)
        print(reader.read_ph())
