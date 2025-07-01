import serial
import time
import json
import os

class CalibratedECReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB1'
        self.baud_rate = 9600
    
    def read_raw_ec(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                ser.flushInput()
                ser.write(b"R\r")
                time.sleep(1.0)
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    return response
                
        except Exception as e:
            print(f"Error reading EC: {e}")
            return None
        
if __name__ == "__main__":
    reader = CalibratedECReader()
    while True:
        print(reader.read_raw_ec())
        time.sleep(.5)