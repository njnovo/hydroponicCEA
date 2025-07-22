import RPi.GPIO as GPIO
import time
from typing import Optional

class UltrasonicReader:
    """
    Class to read water level from an HC-SR04 ultrasonic sensor.
    Calculates water volume in a rectangular reservoir based on dimensions
    and distance measurement.
    """
    
    def __init__(self, trigger_pin: int, echo_pin: int, 
                 tub_height_cm: float = 40.0,  # Standard storage tub height
                 tub_length_cm: float = 60.0,  # Typical 100L tub dimensions
                 tub_width_cm: float = 40.0,
                 sensor_offset_cm: float = 2.0,  # Distance sensor is mounted from top
                 max_volume_l: float = 100.0):
        """
        Initialize ultrasonic sensor with tub dimensions.
        
        Args:
            trigger_pin: GPIO pin connected to sensor's TRIG pin
            echo_pin: GPIO pin connected to sensor's ECHO pin
            tub_height_cm: Height of the storage tub in cm
            tub_length_cm: Length of the storage tub in cm
            tub_width_cm: Width of the storage tub in cm
            sensor_offset_cm: Distance sensor is mounted from top edge
            max_volume_l: Maximum volume in liters (for validation)
        """
        self.TRIGGER_PIN = trigger_pin
        self.ECHO_PIN = echo_pin
        self.tub_height = tub_height_cm
        self.tub_length = tub_length_cm
        self.tub_width = tub_width_cm
        self.sensor_offset = sensor_offset_cm
        self.max_volume = max_volume_l
        
        # Calculate tub volume for validation
        self.tub_volume_l = (tub_height_cm * tub_length_cm * tub_width_cm) / 1000
        if abs(self.tub_volume_l - max_volume_l) > 10:
            print(f"Warning: Calculated tub volume ({self.tub_volume_l:.1f}L) "
                  f"differs significantly from specified max volume ({max_volume_l}L)")
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIGGER_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        
        # Ensure trigger is low
        GPIO.output(self.TRIGGER_PIN, False)
        time.sleep(0.5)  # Let sensor settle
        
        print(f"Ultrasonic sensor initialized (TRIG: {trigger_pin}, ECHO: {echo_pin})")
        print(f"Tub dimensions: {tub_length_cm}cm x {tub_width_cm}cm x {tub_height_cm}cm")
    
    def measure_distance_cm(self) -> Optional[float]:
        """
        Measure distance using ultrasonic sensor.
        
        Returns:
            Distance in centimeters or None if measurement fails
        """
        try:
            # Send 10us pulse to trigger
            GPIO.output(self.TRIGGER_PIN, True)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.TRIGGER_PIN, False)
            
            # Wait for echo to go high
            pulse_start = time.time()
            timeout = pulse_start + 0.1  # 100ms timeout
            
            while GPIO.input(self.ECHO_PIN) == 0:
                pulse_start = time.time()
                if pulse_start > timeout:
                    return None
            
            # Wait for echo to go low
            pulse_end = time.time()
            while GPIO.input(self.ECHO_PIN) == 1:
                pulse_end = time.time()
                if pulse_end > timeout:
                    return None
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance_cm = pulse_duration * 17150  # Speed of sound = 343m/s
            
            return round(distance_cm, 1)
            
        except Exception as e:
            print(f"Error measuring distance: {e}")
            return None
    
    def get_water_level_cm(self) -> Optional[float]:
        """
        Get water level in centimeters from bottom of tub.
        
        Returns:
            Water level in cm or None if measurement fails
        """
        distance = self.measure_distance_cm()
        if distance is None:
            return None
            
        # Account for sensor offset and convert to water level from bottom
        water_level = self.tub_height - (distance + self.sensor_offset)
        
        # Validate reading
        if water_level < 0:
            print("Warning: Negative water level detected, sensor may need calibration")
            return 0
        elif water_level > self.tub_height:
            print("Warning: Water level exceeds tub height, sensor may need calibration")
            return self.tub_height
            
        return round(water_level, 1)
    
    def get_water_volume_l(self) -> Optional[float]:
        """
        Calculate current water volume in liters.
        
        Returns:
            Water volume in liters or None if measurement fails
        """
        water_level = self.get_water_level_cm()
        if water_level is None:
            return None
            
        # Calculate volume
        volume_l = (water_level * self.tub_length * self.tub_width) / 1000
        
        # Validate volume
        if volume_l > self.max_volume:
            print(f"Warning: Calculated volume ({volume_l:.1f}L) exceeds max volume")
            return self.max_volume
            
        return round(volume_l, 1)
    
    def cleanup(self):
        """Clean up GPIO pins"""
        GPIO.cleanup([self.TRIGGER_PIN, self.ECHO_PIN])

def main():
    """Test function"""
    # Example pins - adjust as needed
    TRIG_PIN = 23  # GPIO23
    ECHO_PIN = 24  # GPIO24
    
    reader = UltrasonicReader(TRIG_PIN, ECHO_PIN)
    
    try:
        while True:
            volume = reader.get_water_volume_l()
            if volume is not None:
                print(f"Water volume: {volume:.1f}L")
            else:
                print("Failed to read water level")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopping sensor readings")
    finally:
        reader.cleanup()

if __name__ == "__main__":
    main() 