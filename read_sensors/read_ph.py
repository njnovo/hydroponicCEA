import serial
import time
import json
import os

class CalibratedPHReader:
    def __init__(self, config_file='ph_calibration_data.json'):
        self.config_file = config_file
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 9600
        self.calibration_data = None
        self.load_calibration()
    
    def load_calibration(self):
        """Load calibration data from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.calibration_data = json.load(f)
                print(f"Calibration data loaded from {self.config_file}")
                print(f"Calibration date: {self.calibration_data.get('calibration_date', 'Unknown')}")
                return True
            else:
                print(f"Warning: No calibration file found: {self.config_file}")
                print("Using raw readings without calibration")
                return False
        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False
    
    def read_raw_ph(self):
        """Read raw pH value from sensor"""
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
                ser.flushInput()
                ser.write(b"R\r")
                time.sleep(1.0)
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    return float(response[:4])
        except Exception as e:
            print(f"Error reading pH: {e}")
            return None
    
    def apply_calibration(self, raw_value):
        """Apply calibration curve to raw reading"""
        if not self.calibration_data or 'calibration_curve' not in self.calibration_data:
            print("No calibration data available - returning raw value")
            return raw_value
        
        curve = self.calibration_data['calibration_curve']
        calibrated_ph = curve['slope'] * raw_value + curve['intercept']
        return calibrated_ph
    
    def read_calibrated_ph(self, num_readings=3, stability_threshold=0.1):
        """Read calibrated pH with stability checking"""
        readings = []
        
        for i in range(num_readings):
            raw_value = self.read_raw_ph()
            if raw_value is not None:
                calibrated_value = self.apply_calibration(raw_value)
                readings.append(calibrated_value)
                print(f"Reading {i+1}: Raw={raw_value:.3f}, Calibrated={calibrated_value:.2f}")
            else:
                print(f"Failed to get reading {i+1}")
                return None
            
            if i < num_readings - 1:  # Don't sleep after last reading
                time.sleep(1)
        
        # Check stability
        if len(readings) >= 2:
            std_dev = sum((x - sum(readings)/len(readings))**2 for x in readings)**0.5 / len(readings)**0.5
            if std_dev <= stability_threshold:
                avg_reading = sum(readings) / len(readings)
                return avg_reading, std_dev
            else:
                print(f"Readings not stable (std dev: {std_dev:.3f})")
                return sum(readings) / len(readings), std_dev
        
        return readings[0] if readings else None, 0.0

def read_ph_usb():
    """Legacy function for backward compatibility"""
    reader = CalibratedPHReader()
    result = reader.read_calibrated_ph()
    if result is not None:
        if isinstance(result, tuple):
            return result[0]  # Return just the pH value, not the tuple
        return result
    return None

if __name__ == "__main__":
    reader = CalibratedPHReader()
    
    print("=== Calibrated pH Reader ===")
    if reader.calibration_data:
        print("✓ Using calibrated readings")
        curve = reader.calibration_data['calibration_curve']
        print(f"Calibration quality (R²): {curve['r_squared']:.4f}")
    else:
        print("⚠ Using raw readings (no calibration)")
    
    print("\nTaking pH reading...")
    result = reader.read_calibrated_ph()
    
    if result is not None:
        if isinstance(result, tuple):
            ph, std_dev = result
            print(f"pH: {ph:.2f} ± {std_dev:.3f}")
        else:
            print(f"pH: {result:.2f}")
    else:
        print("Failed to read pH")
