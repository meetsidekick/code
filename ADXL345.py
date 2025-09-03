# ADXL345 I2C Accelerometer Driver for MicroPython
# Optimized for FAST shake detection
# Interface similar to MPU6050 class

from machine import I2C
from time import sleep_ms

class ADXL345:
    ADDRESS = 0x53
    REG_DATA_FORMAT = 0x31
    REG_POWER_CTL = 0x2D
    REG_BW_RATE = 0x2C
    REG_DATAX0 = 0x32

    def __init__(self, i2c, debug_mode=False):
        self.i2c = i2c
        self.debug_mode = debug_mode
        self.available = False
        try:
            self._init_device()
            self.available = True
            if debug_mode:
                print("✅ ADXL345 initialized successfully")
        except OSError as e:
            if debug_mode:
                print(f"⚠️ ADXL345 initialization failed: {e}")
                print("🔧 Debug mode: Continuing without accelerometer...")
                self.available = False
            else:
                raise e

    def _init_device(self):
        # Set device to measurement mode
        self.i2c.writeto_mem(self.ADDRESS, self.REG_POWER_CTL, b'\x08')
        # Set data format: ±8g range for better shake detection (0x0B = ±8g, full resolution)
        self.i2c.writeto_mem(self.ADDRESS, self.REG_DATA_FORMAT, b'\x0B')
        # Set data rate to 800Hz for fast shake detection (0x0D = 800Hz) rather than full resolution
        # Options: 0x0A=100Hz, 0x0B=200Hz, 0x0C=400Hz, 0x0D=800Hz, 0x0E=1600Hz, 0x0F=3200Hz
        self.i2c.writeto_mem(self.ADDRESS, self.REG_BW_RATE, b'\x0D')
        sleep_ms(10)

    def read_accel_data(self):
        # Returns (x, y, z) in raw units (fast single I2C read)
        if not self.available:
            if self.debug_mode:
                return (0, 0, 1000)  # Return fake "still" values
            else:
                raise OSError("ADXL345 not available")
        
        data = self.i2c.readfrom_mem(self.ADDRESS, self.REG_DATAX0, 6)
        x = int.from_bytes(data[0:2], 'little', signed=True)
        y = int.from_bytes(data[2:4], 'little', signed=True)
        z = int.from_bytes(data[4:6], 'little', signed=True)
        return (x, y, z)

    def read_accel_abs(self):
        # Returns absolute acceleration - OPTIMIZED for shake detection
        # Simplified version without parameters to avoid compatibility issues
        if not self.available:
            if self.debug_mode:
                return 1000.0  # Return fake "still" value
            else:
                raise OSError("ADXL345 not available")
                
        x, y, z = self.read_accel_data()
        abs_val = (x**2 + y**2 + z**2) ** 0.5
        return abs_val
    
    def is_shaking(self):
        # Quick shake detection - returns True if shaking detected
        # Fixed threshold=8000 works well for ±8g range
        if not self.available:
            return False  # No shaking if sensor unavailable
        return self.read_accel_abs() > 8000

"""
OPTIMIZATION SUMMARY for Shake Detection:

1. I2C Speed: Use 400kHz (4x faster than 100kHz)
   i2c_bus = I2C(0, scl=Pin(0), sda=Pin(1), freq=400_000)

2. ADXL345 Config:
   - Data Rate: 800Hz (0x0D) - very fast sampling
   - Range: ±8g (0x0B) - better for shake detection than ±2g
   - Single I2C read gets all 3 axes (6 bytes)

3. Recommended thresholds for raw values (±8g range):
   - Light movement: < 2000
   - Shake detection: > 8000
   - Aggressive shaking: > 15000

4. Loop timing: 50ms or faster for responsive shake detection
   
5. Quick check: Use is_shaking() method for fast boolean detection
"""
