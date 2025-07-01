import serial
import time

# === Configuration ===
PORT = "/dev/ttyUSB1" # Change if using different port
BAUD = 9600
TIMEOUT = 1

def send_command(ser, cmd):
    full_cmd = cmd + '\r'
    ser.write(full_cmd.encode())
    time.sleep(0.5)
    response = ser.readline().decode().strip()
    print(f">>> {cmd}")
    print(f"<<< {response}")
    return response

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
        time.sleep(2) # Allow time for device to initialize

        # Step 1: Clear old calibrations
        send_command(ser, "Cal,clear")

        # Step 2: Set K constant (probe cell factor)
        send_command(ser, "K,1.0")

        # Step 3: Set temperature compensation to 25°C
        send_command(ser, "T,25.0")

        # Step 4: Calibrate with 1413 µS/cm solution
        print("Place the probe in the 1413 µS/cm calibration solution now.")
        input("Press Enter when ready...")

        send_command(ser, "Cal,1413")

        # Step 5: Read back EC value
        print("\nReading EC value...")
        send_command(ser, "R")

        ser.close()

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
