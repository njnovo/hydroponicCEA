import serial
import time
import numpy as np
from scipy import stats
import os
import json

class PHCalibrator:
    def __init__(self, config_file='ph_calibration_data.json'):
        self.config_file = config_file
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 9600
        self.calibration_data = {}
        
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
    
    def get_stable_reading(self, buffer_name, target_ph, num_readings=5, stability_threshold=0.1):
        """Get stable reading for a calibration buffer"""
        print(f"\nCalibrating with {buffer_name} (pH {target_ph})")
        print("Please immerse the sensor in the calibration fluid and wait for it to stabilize.")
        input("Press Enter when ready...")
        
        readings = []
        print("Taking readings...")
        
        for i in range(num_readings):
            raw_value = self.read_raw_ph()
            if raw_value is not None:
                readings.append(raw_value)
                print(f"Reading {i+1}: {raw_value:.3f}")
            else:
                print(f"Failed to get reading {i+1}")
                return None
            
            time.sleep(2)
        
        # Check stability
        if len(readings) >= 3:
            std_dev = np.std(readings)
            if std_dev <= stability_threshold:
                avg_reading = np.mean(readings)
                print(f"Stable reading achieved: {avg_reading:.3f} ± {std_dev:.3f}")
                return avg_reading
            else:
                print(f"Readings not stable (std dev: {std_dev:.3f}). Please try again.")
                return None
        
        return np.mean(readings) if readings else None
    
    def calibrate_sensor(self):
        """Perform full calibration with pH 4, 7, and 10 buffers"""
        print("=== pH Sensor Calibration ===")
        print("This calibration will use pH 4, 7, and 10 buffer solutions.")
        print("Make sure you have clean calibration fluids ready.")
        
        calibration_points = [
            ("pH 4 Buffer", 4.0),
            ("pH 7 Buffer", 7.0),
            ("pH 10 Buffer", 10.0)
        ]
        
        raw_readings = []
        target_ph_values = []
        
        for buffer_name, target_ph in calibration_points:
            raw_reading = self.get_stable_reading(buffer_name, target_ph)
            if raw_reading is not None:
                raw_readings.append(raw_reading)
                target_ph_values.append(target_ph)
                print(f"✓ {buffer_name}: Raw = {raw_reading:.3f}, Target = {target_ph}")
            else:
                print(f"✗ Failed to calibrate with {buffer_name}")
                return False
        
        if len(raw_readings) >= 2:
            # Calculate calibration curve (linear regression)
            slope, intercept, r_value, p_value, std_err = stats.linregress(raw_readings, target_ph_values)
            
            self.calibration_data = {
                'calibration_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'calibration_points': {
                    'ph_4': {'raw': raw_readings[0], 'target': 4.0},
                    'ph_7': {'raw': raw_readings[1], 'target': 7.0},
                    'ph_10': {'raw': raw_readings[2], 'target': 10.0}
                },
                'calibration_curve': {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_value ** 2),
                    'std_error': float(std_err)
                }
            }
            
            print(f"\n=== Calibration Results ===")
            print(f"Slope: {slope:.6f}")
            print(f"Intercept: {intercept:.6f}")
            print(f"R-squared: {r_value**2:.6f}")
            print(f"Standard Error: {std_err:.6f}")
            
            if r_value**2 > 0.95:
                print("✓ Calibration quality is good (R² > 0.95)")
            else:
                print("⚠ Calibration quality is poor (R² < 0.95). Consider recalibrating.")
            
            return True
        else:
            print("Insufficient calibration points. Need at least 2 points.")
            return False
    
    def save_calibration(self):
        """Save calibration data to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            print(f"Calibration data saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving calibration: {e}")
            return False
    
    def load_calibration(self):
        """Load calibration data from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.calibration_data = json.load(f)
                print(f"Calibration data loaded from {self.config_file}")
                return True
            else:
                print(f"No calibration file found: {self.config_file}")
                return False
        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False
    
    def apply_calibration(self, raw_value):
        """Apply calibration curve to raw reading"""
        if not self.calibration_data or 'calibration_curve' not in self.calibration_data:
            print("No calibration data available")
            return None
        
        curve = self.calibration_data['calibration_curve']
        calibrated_ph = curve['slope'] * raw_value + curve['intercept']
        return calibrated_ph
    
    def test_calibration(self):
        """Test the calibration with a known buffer"""
        if not self.load_calibration():
            print("No calibration data available for testing")
            return
        
        print("\n=== Calibration Test ===")
        print("Please immerse the sensor in a known buffer solution (pH 4, 7, or 10)")
        buffer_choice = input("Enter the pH of the test buffer (4, 7, or 10): ")
        
        try:
            target_ph = float(buffer_choice)
            if target_ph not in [4.0, 7.0, 10.0]:
                print("Invalid pH value. Please use 4, 7, or 10.")
                return
        except ValueError:
            print("Invalid input. Please enter a number.")
            return
        
        print(f"Testing with pH {target_ph} buffer...")
        raw_reading = self.get_stable_reading(f"pH {target_ph} Buffer", target_ph)
        
        if raw_reading is not None:
            calibrated_ph = self.apply_calibration(raw_reading)
            error = abs(calibrated_ph - target_ph)
            
            print(f"\n=== Test Results ===")
            print(f"Raw reading: {raw_reading:.3f}")
            print(f"Calibrated pH: {calibrated_ph:.2f}")
            print(f"Expected pH: {target_ph:.1f}")
            print(f"Error: {error:.2f} pH units")
            
            if error < 0.2:
                print("✓ Calibration test passed (error < 0.2 pH units)")
            else:
                print("⚠ Calibration test failed (error > 0.2 pH units). Consider recalibrating.")

def main():
    calibrator = PHCalibrator()
    
    print("pH Sensor Calibration Tool")
    print("1. Perform new calibration")
    print("2. Test existing calibration")
    print("3. View calibration data")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == '1':
        if calibrator.calibrate_sensor():
            calibrator.save_calibration()
        else:
            print("Calibration failed")
    
    elif choice == '2':
        calibrator.test_calibration()
    
    elif choice == '3':
        if calibrator.load_calibration():
            print("\n=== Current Calibration Data ===")
            print(json.dumps(calibrator.calibration_data, indent=2))
        else:
            print("No calibration data found")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 