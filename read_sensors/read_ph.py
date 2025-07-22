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
        print(f"Sending command: {cmd}")
        ser.write(full_cmd.encode())
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        print(f"Raw response: {response}")
        value = response.split(",")[0]
        print(f"Parsed value: {value}")
        return value
    
    def read_ph(self):
        try:
            print(f"\nAttempting to connect to {self.serial_port}")
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                print("Serial connection established")
                return float(self.send_command(ser, "r"))
                
        except Exception as e:
            print(f"Error reading pH: {e}")
            return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    print("\nStarting pH sensor readings...")
    print("Press Ctrl+C to stop\n")
    
    while True:
        ph = reader.read_ph()
        print(f"Final pH reading: {ph}")
        time.sleep(.5)
