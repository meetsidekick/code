# Based on Example code for (GY-521) MPU6050 Accelerometer/Gyro Module
# Written in MicroPython by Warayut Poomiwatracanont JAN 2023
# Base Code: https://github.com/Lezgend/MPU6050-MicroPython/blob/main/main.py
# Current Project: https://github.com/MakerSidekick/MakerSidekick-Bot/blob/main/main.py

# === DEBUG SETTINGS ===
SET_DEBUG = True  # Will be set to True automatically if hardware fails

from ADXL345 import ADXL345
from machine import Pin, ADC, I2C
from time import sleep_ms
from buzzer_sounds import (
    startup_shush, startup_sequence, happy_sound,
    angry_sound, shook_sound, headpat_sound, curious_scared_sound
)
from happy_meter import meter as get_happy
from menu import open_menu
from pin_values import touch_pin_value, code_debug_pin_value
import ssd1306
import oled_functions

# === OLED & I2C Initialization ===
i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)  # Faster I2C for ADXL345

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

touch_sensor = None
try:
    #touch_sensor = ADC(Pin(touch_pin_value))
    print("✅ Touch sensor initialized successfully")
except Exception as e:
    SET_DEBUG = True  # Enable debug mode on failure
    print(f"⚠️ Touch sensor initialization failed: {e}")
    print("🔧 Debug mode enabled: Continuing without touch sensor...")
    touch_sensor = None

debug_button = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)

# === DISPLAY SETTINGS ===
UPSIDE_DOWN = True  # Set to True to flip the display 180 degrees

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

# === EMOTIONAL STATE COUNTERS ===
happy_level = 35
headpat_count = 0
shake_count = 0
movement_count = 0

# === Constants ===
HEADPAT_THRESHOLD = 4
SHAKE_THRESHOLD = 7
MOVEMENT_SENSITIVITY = 2
GENTLE_MOVEMENT = 20      # Adjusted for new calculation method
ROUGH_MOVEMENT = 200      # Adjusted for new calculation method

# === STARTUP/INTRO ===
print("🤖 Robot Pet Starting Up! (˶ᵔ ᵕ ᵔ˶)")
startup_shush()
safe_oled_update("happy", 85)
startup_sequence()
print("🎮 Robot Pet Ready! (っ´ω`)ﾉ")

# === MAIN LOOP ===
while True:
    try:
        # Read accelerometer data (ADXL345 handles all error cases internally)
        try:
            acceleration = mpu.read_accel_data()
            movement_force = mpu.read_accel_abs() / 100  # Scale down
            
            # Show live IMU data in debug mode
            if SET_DEBUG:
                print(f"📊 IMU: accel={acceleration}, force={movement_force:.1f}")
                
        except Exception as e:
            if SET_DEBUG:
                print(f"❌ Accelerometer error: {type(e).__name__}: {e}")
            acceleration = (0, 0, 1000)
            movement_force = 10
        
        # Touch sensor reading with error handling
        try:
            if touch_sensor is not None:
                touch_value = touch_sensor.read() * 100
            else:
                touch_value = 50000  # High value = no touch detected
        except Exception as e:
            if SET_DEBUG:
                print(f"❌ Touch sensor error: {e}")
            touch_value = 50000

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

        # Movement logic
        if movement_force <= GENTLE_MOVEMENT:
            movement_count = 0

        if movement_force >= ROUGH_MOVEMENT:
            movement_count += 1
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

        # Touch/headpat reactions
        if touch_value < 12500:
            print("😊 Headpat detected! (っ´ω`)ﾉ(˵•́ ᴗ •̀˵)")
            headpat_sound()
            
            # Safe happiness adjustment
            try:
                happy_level = get_happy("add", happy_level, 0.2)
            except TypeError:
                # Fallback for function signature issues
                happy_level = min(100, happy_level + 5)
                
            headpat_count += 1
            safe_oled_update("headpat")
            sleep_ms(250)
            if headpat_count > HEADPAT_THRESHOLD:
                print("💖 I'm so happy! ( ˶ˆᗜˆ˵ )")
                safe_oled_update("headpat")
                happy_sound()
                sleep_ms(150)
                happy_sound()
                if happy_level >= 75:
                    for _ in range(3):
                        happy_sound()
                        sleep_ms(50)
                headpat_count = 0
                shake_count = 0
                
                # Safe happiness adjustment
                try:
                    happy_level = get_happy("add", happy_level)
                except TypeError:
                    # Fallback for function signature issues
                    happy_level = min(100, happy_level + 15)

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