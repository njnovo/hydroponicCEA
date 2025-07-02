import serial
import time

class ORPReader:
    def __init__(self):
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 9600

    def send_command(self,ser, cmd):
        full_cmd = cmd + '\r'
        ser.write(full_cmd.encode())
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        return response
    
    def read_raw_orp(self):
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                return self.send_command(ser, "R")
                
        except Exception as e:
            print(f"Error reading EC: {e}")
            return None

if __name__ == "__main__":
    reader = ORPReader()
    while True:
        time.sleep(.5)
        print("    " + reader.read_raw_orp())
