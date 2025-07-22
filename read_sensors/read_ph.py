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
                ser.flushOutput()
                
                # Try different command formats
                commands = [
                    b"R\r",      # Basic R command
                    b"R\r\n",    # R with CR+LF
                    b"r\r",      # lowercase r
                    b"RT\r"      # RT command some pH sensors use
                ]
                
                for cmd in commands:
                    print(f"\nTrying command: {cmd}")
                    ser.write(cmd)
                    time.sleep(1.0)
                    
                    if ser.in_waiting > 0:
                        response = ser.read(ser.in_waiting)
                        print(f"Raw bytes received: {response}")
                        try:
                            decoded = response.decode('utf-8').strip()
                            print(f"Decoded response: {decoded}")
                            try:
                                float_val = float(decoded)
                                print(f"Valid pH value: {float_val}")
                                return float_val
                            except ValueError:
                                print(f"Could not convert to float: {decoded}")
                        except UnicodeDecodeError:
                            print(f"Could not decode bytes as UTF-8")
                    else:
                        print("No response received")
                
                print("\nNo valid response from any command")
                return None
                    
        except Exception as e:
            print(f"Error reading pH: {str(e)}")
            return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    
    print("\nTesting pH sensor communication...")
    print("Press Ctrl+C to stop\n")
    
    while True:
        ph = reader.read_ph()
        print(f"\nFinal pH reading: {ph}")
        time.sleep(2)  # Increased delay between attempts
