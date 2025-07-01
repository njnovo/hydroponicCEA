import serial
import time

def read_ph_usb():
    with serial.Serial('/dev/ttyACM0', 9600, timeout=1) as ser:
        ser.flushInput()
        ser.write(b"R\r")
        time.sleep(1.0)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Raw response: {response}")
            try:
                # Split the response if it's comma-separated
                parts = response.split(",")
                ph_value = float(parts[0])  # First value should be pH
                return ph_value
            except (ValueError, IndexError):
                print(f"Unexpected response: {response}")
                return None

if __name__ == "__main__":
    ph = read_ph_usb()
    if ph is not None:
        print(f"pH: {ph}")
    else:
        print("Failed to read pH")
