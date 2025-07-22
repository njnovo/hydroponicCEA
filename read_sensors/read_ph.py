import serial
import time
import json
import os

class CalibratedPHReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB1'
        self.baud_rate = 9600
  
    def read_ph(self):
        """Read pH value from sensor"""
        try:
            print(f"Attempting to connect to {self.serial_port}")
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                print("Serial connection established")
                ser.flushInput()
                print("Sending 'R' command")
                ser.write(b"R\r")
                time.sleep(1.0)
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"Raw response: {response}")
                    try:
                        # Try to convert to float to see if it's a valid number
                        float_val = float(response)
                        return float_val
                    except ValueError:
                        print(f"Could not convert response to float: {response}")
                        return None
                else:
                    print("No data received from sensor")
                    return None
        except Exception as e:
            print(f"Error reading pH: {str(e)}")
            return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    
    while True:
        ph = reader.read_ph()
        print(f"pH reading: {ph}")
        time.sleep(1)
