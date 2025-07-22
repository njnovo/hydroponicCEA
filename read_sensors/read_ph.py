import serial
import time

class CalibratedPHReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB1'
        self.baud_rate = 9600
    
    def read_ph(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                ser.write(b'r\r')
                time.sleep(1.0)
                response = ser.readline().decode().strip()
                return float(response)
        except Exception as e:
            print(f"Error reading pH: {e}")
            return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    while True:
        print(reader.read_ph())
        time.sleep(1)
