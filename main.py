# Based on Example code for (GY-521) MPU6050 Accelerometer/Gyro Module
# Written in MicroPython by Warayut Poomiwatracanont JAN 2023
# Base Code: https://github.com/Lezgend/MPU6050-MicroPython/blob/main/main.py
# Current Project: https://github.com/MakerSidekick/MakerSidekick-Bot/blob/main/main.py

# === DEBUG SETTINGS ===
SET_DEBUG = False  # Will be set to True automatically if hardware fails

from ADXL345 import ADXL345
from machine import Pin, I2C
from time import sleep_ms
from buzzer_sounds import (
    startup_shush, startup_sequence, happy_sound,
    angry_sound, shook_sound, headpat_sound, curious_scared_sound
)
from happy_meter import meter as get_happy
from menu import open_menu
from pin_values import code_debug_pin_value
import ssd1306
import oled_functions
from collections import deque
import math

# === OLED HELPER FUNCTION ===
def safe_oled_update(display_type, value=None):
    """Safely update OLED - skip if OLED is not available"""
    if oled is not None:
        oled_functions.update_oled(oled, display_type, value, UPSIDE_DOWN, SET_DEBUG)
    elif SET_DEBUG:
        if value is not None:
            print(f"🖥️ OLED: {display_type} = {value}")
        else:
            print(f"🖥️ OLED: {display_type}")

# === OLED & I2C Initialization ===
i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)  # SCL=5, SDA=4
sleep_ms(100)  # Wait for I2C bus to settle

# Try to initialize OLED - enable debug mode if it fails
oled = None
try:
    oled = ssd1306.SSD1306_I2C(128, 64, i2c_bus)
    print("✅ OLED initialized successfully")
except OSError as e:
    SET_DEBUG = True  # Enable debug mode on failure
    print(f"⚠️ OLED initialization failed: {e}")
    print("🔧 Debug mode enabled: Continuing without OLED...")
    oled = None

# === DEVICES/SENSORS ===
# Initialize ADXL345 with error handling built-in
try:
    mpu = ADXL345(i2c_bus, SET_DEBUG)
    print("✅ ADXL345 initialized successfully")
except Exception as e:
    SET_DEBUG = True  # Enable debug mode on failure
    print(f"⚠️ ADXL345 initialization failed: {e}")
    print("🔧 Debug mode enabled: Creating basic dummy accelerometer...")
    
    # Simple fallback dummy class
    class BasicDummy:
        def read_accel_data(self):
            return (0, 0, 1000)
        def read_accel_abs(self):
            return 1000.0
        def is_shaking(self):
            return False
    mpu = BasicDummy()

debug_button = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)

# === DISPLAY SETTINGS ===
UPSIDE_DOWN = True  # Set to True to flip the display 180 degrees

# === EMOTIONAL STATE COUNTERS ===
happy_level = 50
movement_count = 0
shake_count = 0
headpat_count = 0
gentle_movement_count = 0

# === ROLLING AVERAGE FOR MOVEMENT DETECTION ===
# Use a deque to store recent movement force values
MOVEMENT_HISTORY_SIZE = 10
movement_history = deque([0] * MOVEMENT_HISTORY_SIZE, MOVEMENT_HISTORY_SIZE)

# === Constants ===
HEADPAT_THRESHOLD = 4
SHAKE_THRESHOLD = 7
MOVEMENT_SENSITIVITY = 2
GENTLE_MOVEMENT_THRESHOLD = 15 # How long gentle movement is needed for a reward
# Adjusted thresholds for the new rolling average method
GENTLE_MOVEMENT_MIN = 100 # Min threshold to be considered gentle movement (filters noise)
GENTLE_MOVEMENT_MAX = 35000 # Max threshold to be considered gentle movement
ROUGH_MOVEMENT = 80000

# === STARTUP/INTRO ===
print("🤖 Robot Pet Starting Up! (˶ᵔ ᵕ ᵔ˶)")
startup_shush()

safe_oled_update("happy", 85)
startup_sequence()
print("🎮 Robot Pet Ready! (っ´ω`)ﾉ")

# Initialize previous_accel for difference calculation
try:
    previous_accel = mpu.read_accel_data()
except Exception as e:
    previous_accel = (0, 0, 0)
    if SET_DEBUG:
        print(f"⚠️ Initial accel read failed: {e}")

# === MAIN LOOP ===
while True:
    try:
        # Read accelerometer data and calculate movement force
        try:
            current_accel = mpu.read_accel_data()
            
            # Calculate the difference from the previous reading
            diff_x = current_accel[0] - previous_accel[0]
            diff_y = current_accel[1] - previous_accel[1]
            diff_z = current_accel[2] - previous_accel[2]
            
            # Calculate the magnitude of the difference vector
            movement_force = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)
            
            # Update the previous acceleration value for the next iteration
            previous_accel = current_accel
            
            # Add the new force to our history
            movement_history.append(movement_force)
            
            if SET_DEBUG:
                print(f"📊 IMU: accel={current_accel}, force={movement_force:.1f}")
        except Exception as e:
            movement_force = 0
            if SET_DEBUG:
                print(f"💥 Accelerometer error: {e}")
        
        # Calculate the average movement force from the history
        average_force = sum(movement_history) / MOVEMENT_HISTORY_SIZE

        # Shake reactions
        if movement_count >= MOVEMENT_SENSITIVITY:
            print("😵 I'm getting dizzy! (⸝⸝๑﹏๑⸝⸝)")
            safe_oled_update("shake")
            shook_sound()
            sleep_ms(100)
            shook_sound()
            shake_count += 1
            movement_count = 0
            if shake_count >= SHAKE_THRESHOLD:
                happy_level = 0
                shake_count = 0
                print("💔 All trust lost! I'm extremely dizzy and sad...")
                sleep_ms(150)
                safe_oled_update("happy", 10)
            continue

        # Movement logic based on the average force
        if average_force <= GENTLE_MOVEMENT_MIN:
            # Reset counters if movement stops
            movement_count = 0
            gentle_movement_count = 0
        elif GENTLE_MOVEMENT_MIN < average_force <= GENTLE_MOVEMENT_MAX:
            # If movement is gentle, increment gentle counter
            gentle_movement_count += 1
            movement_count = 0 # Reset rough movement counter
            if gentle_movement_count >= GENTLE_MOVEMENT_THRESHOLD:
                print("😊 This is a nice stroll! (´▽｀)")
                happy_level = get_happy("add", happy_level, 0.1) # Gradual increase
                gentle_movement_count = 0 # Reset after reward
        elif average_force >= ROUGH_MOVEMENT:
            # If movement is rough, increment rough counter
            movement_count += 1
            gentle_movement_count = 0 # Reset gentle counter
            if happy_level < 75:
                angry_sound()
                print("😠 Hey! What was that for! ヽ(｀Д´)ﾉ")
            else:
                curious_scared_sound()
                print("😮 Whoa, are you taking me somewhere? (ﾟοﾟ)")
            
            # Safe happiness adjustment
            try:
                happy_level = get_happy("reduce", happy_level)
            except TypeError:
                # Fallback for function signature issues
                happy_level = max(0, happy_level - 10)

        # Regular mood display
        safe_oled_update("happy", happy_level)

        # Debug menu access
        if debug_button.value() == 0:
            open_menu()
            startup_sequence()
            safe_oled_update("happy", 85)

        sleep_ms(50)  # Faster loop for better shake detection (was 150ms)

    except Exception as e:
        print("Error in main loop:", e)
        sleep_ms(1000)