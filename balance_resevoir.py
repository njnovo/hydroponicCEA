import time
from read_sensors.read_ph import CalibratedPHReader
from read_sensors.read_ec import CalibratedECReader
from actuators.motor import Motor
from calibration.reservoir_logger import ReservoirLogger, ReservoirAdjustment
from typing import Optional

# Optional import for ultrasonic sensor
try:
    from read_sensors.read_ultra import UltrasonicReader
    ULTRASONIC_AVAILABLE = True
except (ImportError, RuntimeError):
    ULTRASONIC_AVAILABLE = False
    print("Note: Ultrasonic sensor support not available - will use default volume")

def main():
    # Initialize sensors and motors
    ph_reader = CalibratedPHReader()
    ec_reader = CalibratedECReader()
    
    # Initialize ultrasonic sensor if available
    ultra_reader: Optional[UltrasonicReader] = None
    if ULTRASONIC_AVAILABLE:
        try:
            ultra_reader = UltrasonicReader(
                trigger_pin=23,  # GPIO23
                echo_pin=24,     # GPIO24
                tub_height_cm=40.0,  # Adjust these dimensions
                tub_length_cm=60.0,  # to match your
                tub_width_cm=40.0,   # actual tub
                sensor_offset_cm=2.0  # Distance sensor is mounted from top
            )
            print("Ultrasonic sensor initialized successfully")
        except Exception as e:
            print(f"Failed to initialize ultrasonic sensor: {e}")
            ultra_reader = None

    fertilizer_part_a = Motor(17, 27, 22)
    fertilizer_part_b = Motor(23, 24, 25)
    ph_up = Motor(20, 21, 16)
    ph_down = Motor(13, 19, 12)

    # Initialize reservoir logger
    logger = ReservoirLogger()

    # Target values
    TARGET_PH = 5.8
    TARGET_EC = 1100
    MIN_VOLUME = 20.0  # Minimum volume in liters to operate
    WARNING_VOLUME = 75.0  # Volume threshold for low water warning
    
    def apply_adjustments(recommendations):
        """Apply the recommended motor runtimes and return total runtime for each motor"""
        runtimes = {
            'ph_up': 0.0,
            'ph_down': 0.0,
            'fert_a': 0.0,
            'fert_b': 0.0
        }
        
        # Apply pH adjustments
        if recommendations['ph_up'] > 0:
            runtime = recommendations['ph_up']
            ph_up.run_for_time(10, 1, runtime)  # 10 steps/sec
            runtimes['ph_up'] = runtime
        elif recommendations['ph_down'] > 0:
            runtime = recommendations['ph_down']
            ph_down.run_for_time(10, 1, runtime)
            runtimes['ph_down'] = runtime
            
        # Apply EC adjustments
        if recommendations['fert_a'] > 0:
            runtime = recommendations['fert_a']
            fertilizer_part_a.run_for_time(10, 1, runtime)
            runtimes['fert_a'] = runtime
            # Wait briefly between part A and B
            time.sleep(2)
            fertilizer_part_b.run_for_time(10, 1, runtime)
            runtimes['fert_b'] = runtime
            
        return runtimes

    print("Starting reservoir management system...")
    print(f"Target values - pH: {TARGET_PH}, EC: {TARGET_EC}")

    try:
        while True:
            try:
                # Read current volume if sensor available
                current_volume = None
                if ultra_reader is not None:
                    current_volume = ultra_reader.get_water_volume_l()
                    if current_volume is not None:
                        print(f"\nCurrent water volume: {current_volume:.1f}L")
                        
                        # Check if volume is too low
                        if current_volume < MIN_VOLUME:
                            print(f"Warning: Water level too low ({current_volume:.1f}L < {MIN_VOLUME}L)")
                            print("Please add water to the reservoir.")
                            time.sleep(300)  # Wait 5 minutes
                            continue
                        elif current_volume < WARNING_VOLUME:
                            print(f"\n⚠️  Warning: Water level is getting low ({current_volume:.1f}L < {WARNING_VOLUME}L)")
                            print("Please fill up the reservoir soon to maintain optimal operation.")
                    
                # Update logger's volume (will use default if current_volume is None)
                logger.volume_liters = current_volume
                
                # Read current values
                current_ph = ph_reader.read_ph()
                current_ec = float(ec_reader.read_ec())
                
                if current_ph is None or current_ec is None:
                    print("Error: Could not read pH or EC. Waiting 5 minutes...")
                    time.sleep(300)
                    continue
                
                print(f"Current readings - pH: {current_ph:.2f}, EC: {current_ec:.0f}")
                
                # Get recommended adjustments
                recommendations = logger.get_recommended_runtime(
                    current_ph=current_ph,
                    target_ph=TARGET_PH,
                    current_ec=current_ec,
                    target_ec=TARGET_EC
                )
                
                # If any adjustments are needed
                if any(v > 0 for v in recommendations.values()):
                    print("\nAdjustments needed:")
                    for motor, runtime in recommendations.items():
                        if runtime > 0:
                            print(f"- {motor}: {runtime:.1f} seconds")
                    
                    # Apply adjustments and get actual runtimes
                    runtimes = apply_adjustments(recommendations)
                    
                    # Wait for mixing
                    print("\nWaiting 5 minutes for mixing...")
                    time.sleep(300)  # 5 minutes
                    
                    # Read new values
                    new_ph = ph_reader.read_ph()
                    new_ec = float(ec_reader.read_ec())
                    new_volume = ultra_reader.get_water_volume_l() if ultra_reader else None
                    
                    if None in (new_ph, new_ec):
                        print("Error: Could not read sensors after adjustment")
                        time.sleep(300)
                        continue
                    
                    # Print readings
                    if new_volume is not None:
                        print(f"New readings - pH: {new_ph:.2f}, EC: {new_ec:.0f}, Volume: {new_volume:.1f}L")
                    else:
                        print(f"New readings - pH: {new_ph:.2f}, EC: {new_ec:.0f}")
                    
                    # Log the adjustment
                    adjustment = ReservoirAdjustment(
                        timestamp=time.time(),
                        ph_before=current_ph,
                        ph_after=new_ph,
                        ec_before=current_ec,
                        ec_after=new_ec,
                        ph_up_runtime=runtimes['ph_up'],
                        ph_down_runtime=runtimes['ph_down'],
                        fert_a_runtime=runtimes['fert_a'],
                        fert_b_runtime=runtimes['fert_b'],
                        volume_liters=new_volume if new_volume is not None else logger.DEFAULT_VOLUME
                    )
                    logger.log_adjustment(adjustment)
                    
                    # Print statistics
                    stats = logger.get_statistics()
                    print("\nSystem Statistics:")
                    print(f"- Total adjustments: {stats['total_adjustments']}")
                    print(f"- pH buffer capacity: {stats['current_ph_buffer_capacity']:.4f} pH/sec")
                    print(f"- EC response factor: {stats['current_ec_response_factor']:.2f} EC/sec")
                    if stats['last_24h_adjustments'] > 0:
                        print(f"- Average pH change (24h): {stats['average_ph_change']:.2f}")
                        print(f"- Average EC change (24h): {stats['average_ec_change']:.2f}")
                else:
                    print("No adjustments needed.")
                
                # Wait for next check (1 hour)
                print("\nWaiting 1 hour until next check...")
                time.sleep(3600)
                
            except Exception as e:
                print(f"Error during operation: {e}")
                print("Waiting 5 minutes before retry...")
                time.sleep(300)
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        if ultra_reader is not None:
            ultra_reader.cleanup()

if __name__ == "__main__":
    main()
