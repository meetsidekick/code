# Super simple test to isolate the keyword argument issue
from ADXL345 import ADXL345
from machine import Pin, I2C

# Simple I2C setup
i2c_bus = I2C(0, Pin(5), Pin(4))  # No freq= keyword

try:
    # Simple ADXL345 setup with no keyword arguments
    mpu = ADXL345(i2c_bus, True)  # positional arguments only
    print("✅ ADXL345 initialized")
    
    # Simple loop to test
    for i in range(10):
        data = mpu.read_accel_data()
        force = mpu.read_accel_abs()
        print("Data:", data, "Force:", force)
        
except Exception as e:
    print("❌ Error:", type(e).__name__, str(e))
    
print("Done!")
