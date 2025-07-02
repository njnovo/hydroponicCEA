#!/usr/bin/env python3

import smbus2
import time
from typing import Tuple, Optional

class AtlasColorSensor:
    """Class to interface with Atlas Scientific EZO RGB Color sensor using I2C
    
    Physical Connections:
    - TX -> SCL of microcontroller/Pi
    - RX -> SDA of microcontroller/Pi
    - GND -> GND
    - VCC -> 3.3V-5V power supply
    - INT -> Not used in this implementation (interrupt pin)
    
    Note: On Raspberry Pi, you may need to:
    1. Enable I2C in raspi-config
    2. The default I2C address for Atlas RGB sensor is 0x70
    """
    
    # Atlas Scientific RGB Color sensor default I2C address
    DEFAULT_ADDRESS = 0x70
    
    def __init__(self, address=0x70, bus=1):
        """Initialize the color sensor.
        
        Args:
            address: I2C address of the sensor (default 0x70)
            bus: I2C bus number (default 1 for Raspberry Pi)
        """
        self.address = address
        self.bus = smbus2.SMBus(bus)

    def _send_command(self, cmd):
        try:
            self.bus.write_i2c_block_data(self.address, ord(cmd[0]), [ord(c) for c in cmd[1:]])
            time.sleep(0.9)  # Wait for processing
            
            response_length = self.bus.read_byte(self.address)
            response = self.bus.read_i2c_block_data(self.address, 0x00, response_length)
            return bytes(response).decode().strip()
        except:
            return None
            
    def read_rgb(self):
        """Returns (red, green, blue) values"""
        response = self._send_command("R")
        if response:
            return tuple(map(int, response.split(",")))
        return None
        
    def read_cie(self):
        """Returns (x, y, Y) CIE values"""
        response = self._send_command("C")
        if response:
            return tuple(map(float, response.split(",")))
        return None
        
    def read_lux(self):
        """Returns illuminance in lux"""
        response = self._send_command("L")
        if response:
            return float(response)
        return None

def main():
    sensor = AtlasColorSensor()
    try:
        while True:
            rgb = sensor.read_rgb()
            if rgb:
                r, g, b = rgb
                print(f"RGB Values - Red: {r}, Green: {g}, Blue: {b}")
            
            illuminance = sensor.read_lux()
            if illuminance is not None:
                print(f"Illuminance: {illuminance}")
            
            time.sleep(1)  # Wait before next reading
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings")

if __name__ == "__main__":
    main()
