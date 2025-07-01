import serial
import time

# Change to your actual serial port (e.g., /dev/ttyUSB0 or COM3)
SERIAL_PORT = '/dev/ttyUSB0'  # or 'COM3' on Windows
BAUD_RATE = 9600
TIMEOUT = 1  # seconds

def read_ph_usb():
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
        # Clear any existing data
        ser.flushInput()

        # Send the "R" command to request a reading
        ser.write(b"R\r")
        time.sleep(1.0)  # Wait for the response

        # Read response from device
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            try:
                ph_value = float(response)
                return ph_value
            except ValueError:
                print(f"Unexpected response: {response}")
                return None

if __name__ == "__main__":
    ph = read_ph_usb()
    if ph is not None:
        print(f"pH: {ph}")
    else:
        print("Failed to read pH")
