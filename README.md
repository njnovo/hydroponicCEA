# pH Sensor Calibration System

This system provides automated calibration and reading capabilities for pH sensors using pH 4, 7, and 10 buffer solutions.

## Features

- **Automated Calibration**: Uses pH 4, 7, and 10 buffer solutions for accurate calibration
- **JSON Configuration**: Stores calibration data in simple JSON format
- **Stability Checking**: Ensures readings are stable before accepting calibration points
- **Quality Assessment**: Provides R-squared values to assess calibration quality
- **Calibrated Readings**: Applies calibration curve to raw sensor readings
- **Backward Compatibility**: Original `read_ph_usb()` function still works

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Calibrating the Sensor

Run the calibration script:
```bash
python ph_calibration.py
```

The script will guide you through the calibration process:

1. **Option 1**: Perform new calibration
   - Immerse sensor in pH 4 buffer solution
   - Wait for stable readings
   - Repeat for pH 7 and pH 10 buffers
   - Calibration data is automatically saved to `ph_calibration_data.json`

2. **Option 2**: Test existing calibration
   - Test the calibration with any known buffer solution

3. **Option 3**: View calibration data
   - Display current calibration parameters

### 2. Reading Calibrated pH Values

Use the updated `read_ph.py`:
```bash
python read_ph.py
```

The script will:
- Load calibration data from `ph_calibration_data.json`
- Take multiple readings for stability
- Apply the calibration curve
- Display both raw and calibrated values

### 3. Programmatic Usage

```python
from read_ph import CalibratedPHReader

# Create reader instance
reader = CalibratedPHReader()

# Read calibrated pH
ph_value, std_dev = reader.read_calibrated_ph()
print(f"pH: {ph_value:.2f} ± {std_dev:.3f}")

# Or use the legacy function
from read_ph import read_ph_usb
ph = read_ph_usb()
print(f"pH: {ph}")
```

## Calibration Process

### Required Materials
- pH 4 buffer solution
- pH 7 buffer solution  
- pH 10 buffer solution
- Clean containers for each buffer
- Distilled water for rinsing

### Calibration Steps
1. **Prepare**: Clean the sensor with distilled water
2. **pH 4**: Immerse in pH 4 buffer, wait for stabilization
3. **Rinse**: Clean sensor with distilled water
4. **pH 7**: Immerse in pH 7 buffer, wait for stabilization
5. **Rinse**: Clean sensor with distilled water
6. **pH 10**: Immerse in pH 10 buffer, wait for stabilization
7. **Save**: Calibration data is automatically saved

### Calibration Quality
- **R² > 0.95**: Good calibration
- **R² < 0.95**: Poor calibration, consider recalibrating
- **Error < 0.2 pH units**: Test passed
- **Error > 0.2 pH units**: Test failed, recalibrate

## Configuration Files

### ph_calibration_data.json
```json
{
  "calibration_date": "2024-01-01 12:00:00",
  "calibration_points": {
    "ph_4": {
      "raw": 1.234,
      "target": 4.0
    },
    "ph_7": {
      "raw": 2.345,
      "target": 7.0
    },
    "ph_10": {
      "raw": 3.456,
      "target": 10.0
    }
  },
  "calibration_curve": {
    "slope": 2.123456,
    "intercept": 1.654321,
    "r_squared": 0.998765,
    "std_error": 0.012345
  }
}
```

## Troubleshooting

### Common Issues

1. **"No calibration file found"**
   - Run `python ph_calibration.py` to create calibration data

2. **"Readings not stable"**
   - Ensure sensor is properly immersed
   - Wait longer for temperature stabilization
   - Check for air bubbles on sensor

3. **"Calibration quality is poor"**
   - Clean sensor thoroughly
   - Use fresh buffer solutions
   - Ensure proper temperature (20-25°C recommended)

4. **Serial communication errors**
   - Check USB connection
   - Verify correct port (`/dev/ttyACM0`)
   - Ensure sensor is powered on

### Maintenance
- Recalibrate monthly or when accuracy degrades
- Store buffer solutions properly (avoid contamination)
- Clean sensor regularly with distilled water
- Check calibration quality before important measurements

## Technical Details

### Calibration Curve
The system uses linear regression to create a calibration curve:
```
pH_calibrated = slope × raw_value + intercept
```

### Stability Checking
Readings are considered stable when:
- Standard deviation ≤ 0.1 pH units
- At least 3 consecutive readings taken

### Error Handling
- Graceful fallback to raw readings if no calibration data
- Detailed error messages for troubleshooting
- Automatic retry mechanisms for communication issues