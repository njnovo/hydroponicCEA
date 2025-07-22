import RPi.GPIO as GPIO
import time
import threading

# --- Motor Class Definition ---
class Motor:
    """
    A class to control a stepper motor connected to a Raspberry Pi
    via a microstep driver.
    """
    def __init__(self, dir_pin, step_pin, enable_pin):
        """
        Initializes the Motor class with the specified GPIO pins.

        Args:
            dir_pin (int): The GPIO pin connected to the DIR+ (direction) input of the driver.
            step_pin (int): The GPIO pin connected to the PUL+ (pulse/step) input of the driver.
            enable_pin (int): The GPIO pin connected to the ENA+ (enable) input of the driver.
                              (Set to HIGH to disable, LOW to enable)
        """
        self.DIR_PIN = dir_pin
        self.STEP_PIN = step_pin
        self.ENABLE_PIN = enable_pin

        # Configure GPIO mode to BCM (Broadcom pin-numbering scheme)
        GPIO.setmode(GPIO.BCM)

        # Set up GPIO pins as outputs
        GPIO.setup(self.DIR_PIN, GPIO.OUT)
        GPIO.setup(self.STEP_PIN, GPIO.OUT)
        # Set enable pin to HIGH initially to disable the motor driver
        # This prevents the motor from holding position and drawing current when idle.
        GPIO.setup(self.ENABLE_PIN, GPIO.OUT, initial=GPIO.HIGH)

        # Internal flags and thread for motor control
        self._running = False  # Flag to control the motor's running state
        self._motor_thread = None # Thread object for background motor operation
        self._steps_per_second = 0 # Desired speed in steps per second
        self._direction = 0    # Current direction (0 or 1)

        print(f"Motor initialized: DIR={self.DIR_PIN}, STEP={self.STEP_PIN}, ENABLE={self.ENABLE_PIN}")

    def _motor_loop(self):
        """
        Internal method that runs in a separate thread to continuously pulse the motor.
        This loop continues as long as the _running flag is True.
        """
        # Enable the motor driver by setting the ENABLE_PIN to LOW
        GPIO.output(self.ENABLE_PIN, GPIO.LOW)
        # Set the motor direction
        GPIO.output(self.DIR_PIN, self._direction)

        # Calculate the delay between pulses based on the desired steps per second.
        # Each step requires two delays (one for HIGH, one for LOW).
        if self._steps_per_second > 0:
            # delay = (1 second / steps_per_second) / 2 (for HIGH and LOW)
            delay = 0.5 / self._steps_per_second
        else:
            # If steps_per_second is 0, use a small default delay to avoid division by zero
            # and allow the loop to run without immediately exiting if called incorrectly.
            delay = 0.001
            print("Warning: steps_per_second is 0, using default small delay.")

        # Main loop for pulsing the stepper motor
        while self._running:
            GPIO.output(self.STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.STEP_PIN, GPIO.LOW)
            time.sleep(delay)

        # When the _running flag becomes False, the loop exits.
        # Disable the motor driver to save power and prevent heating when stopped.
        GPIO.output(self.ENABLE_PIN, GPIO.HIGH)
        print("Motor thread finished.")

    def run_motor(self, steps_per_second, direction):
        """
        Starts the stepper motor rotation in a separate thread.

        Args:
            steps_per_second (int): The desired speed of the motor in steps per second.
                                    This determines how fast the motor rotates.
            direction (int): The direction of rotation (e.g., 0 for clockwise, 1 for counter-clockwise).
                             This corresponds to the state of the DIR_PIN.
        """
        if not self._running:
            self._steps_per_second = steps_per_second
            self._direction = direction
            self._running = True # Set the flag to True to start the motor loop

            # Create and start a new thread to run the _motor_loop function
            self._motor_thread = threading.Thread(target=self._motor_loop)
            self._motor_thread.daemon = True # Set as daemon so it exits when main program exits
            self._motor_thread.start()
            print(f"Motor started: Speed={steps_per_second} steps/sec, Direction={direction}")
        else:
            print("Motor is already running.")

    def motor_stop(self):
        """
        Stops the stepper motor.
        This sets the _running flag to False, which signals the motor thread to stop.
        It then waits for the motor thread to complete its current cycle and terminate.
        """
        if self._running:
            self._running = False # Set the flag to False to stop the motor loop
            if self._motor_thread:
                self._motor_thread.join() # Wait for the motor thread to finish
            print("Motor stopped.")
        else:
            print("Motor is not running.")

    def run_for_time(self, steps_per_second, direction, time):
        """
        Runs the motor for a specified time.
        """
        self.run_motor(steps_per_second, direction)
        time.sleep(time)
        self.motor_stop()

    def cleanup(self):
        """
        Cleans up all GPIO resources.
        It's crucial to call this when your script exits to release the pins.
        """
        GPIO.cleanup()
        print("GPIO cleaned up.")

# --- Main Function ---
def main():
    """
    Main function to demonstrate the usage of the Motor class.
    It runs the motor for 2 seconds, stops it, waits 0.5 seconds, and repeats.
    The loop continues until a KeyboardInterrupt (Ctrl+C) is detected.
    """
    # --- IMPORTANT: Configure your GPIO pins here (BCM numbering) ---
    # Replace these with the actual GPIO pins you connected to your driver.
    # Example:
    # DIR_PIN: Raspberry Pi GPIO pin connected to DIR+ on the driver
    # STEP_PIN: Raspberry Pi GPIO pin connected to PUL+ on the driver
    # ENABLE_PIN: Raspberry Pi GPIO pin connected to ENA+ on the driver
    DIR_PIN = 27
    STEP_PIN = 17
    ENABLE_PIN = 22

    # Create an instance of the Motor class
    motor = Motor(DIR_PIN, STEP_PIN, ENABLE_PIN)

    try:
        # Loop indefinitely until interrupted by the user
        while True:
            print("\n--- Cycle Start ---")
            print("Running motor for 2 seconds...")
            # Run the motor at 1000 steps per second in one direction (e.g., clockwise)
            motor.run_motor(steps_per_second=1000, direction=1)
            time.sleep(2) # Keep motor running for 2 seconds

            motor.motor_stop() # Stop the motor
            print("Motor stopped. Waiting for 0.5 seconds...")
            time.sleep(0.5) # Wait for 0.5 seconds before the next cycle

            # Optional: Run in the opposite direction for the next cycle
            print("Running motor for 2 seconds in opposite direction...")
            motor.run_motor(steps_per_second=1000, direction=0)
            time.sleep(2)
            motor.motor_stop()
            print("Motor stopped. Waiting for 0.5 seconds...")
            time.sleep(0.5)

            print("--- Cycle End ---")

    except KeyboardInterrupt:
        # This block is executed when the user presses Ctrl+C
        print("\nProgram interrupted by user (Ctrl+C).")
    finally:
        # Ensure GPIO pins are cleaned up properly when the script exits
        motor.cleanup()
        print("Program finished.")

# This ensures that main() is called only when the script is executed directly
if __name__ == "__main__":
    main()
