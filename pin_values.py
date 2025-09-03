# Using a single file to track all the pins used 
# Skipping MPU6050, since that's hardcoded in the MPU6050.py file

touch_pin_value = 9 # GPIO 9, for touch pin. Against a 560k Ohm resistor, you may need to tweak this. 
code_debug_pin_value = 1 # GPIO 1, for debug/modifier pin
buzzer_pin_value = 8 # GPIO 8, for Buzzer
led_pin_value = 1 # GPIO 1, for builtin LED