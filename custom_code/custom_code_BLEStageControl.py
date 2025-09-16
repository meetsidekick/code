from time import sleep_ms, ticks_ms, ticks_diff
from machine import Pin
import ubluetooth as bluetooth
import struct

from pin_values import code_ok_pin_value, code_debug_pin_value
import settings_store
import oled_functions

# --- Key Codes for Presentation Remote ----------------------------------------
# These are standard HID usage codes for keyboard keys.
KEY_LEFT_ARROW = 0x50
KEY_RIGHT_ARROW = 0x4F
KEY_UP_ARROW = 0x52
KEY_DOWN_ARROW = 0x51
KEY_PAGE_UP = 0x4B
KEY_PAGE_DOWN = 0x4E

# Modifier keys (not used for simple arrow/page keys, but good to have)
MOD_NONE = 0x00

# --- HID Service and Report Descriptor (Standard Keyboard) --------------------
_HID_SERVICE_UUID = bluetooth.UUID(0x1812)
_REPORT_CHAR_UUID = bluetooth.UUID(0x2A4D)
_REPORT_MAP_CHAR_UUID = bluetooth.UUID(0x2A4B)

# HID Report Descriptor for a standard keyboard (8-byte report)
_HID_REPORT_DESCRIPTOR = bytearray([
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x06,        # Usage (Keyboard)
    0xA1, 0x01,        # Collection (Application)
    0x05, 0x07,        #   Usage Page (Key Codes)
    0x19, 0xE0,        #   Usage Minimum (224) - Left Control
    0x29, 0xE7,        #   Usage Maximum (231) - Right GUI
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x08,        #   Report Count (8) - 8 modifier bits
    0x81, 0x02,        #   Input (Data, Variable, Absolute) - Modifier byte
    0x95, 0x01,        #   Report Count (1)
    0x75, 0x08,        #   Report Size (8)
    0x81, 0x01,        #   Input (Constant) - Reserved byte
    0x95, 0x06,        #   Report Count (6) - 6 key codes
    0x75, 0x08,        #   Report Size (8)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x65,        #   Logical Maximum (101)
    0x05, 0x07,        #   Usage Page (Key Codes)
    0x19, 0x00,        #   Usage Minimum (0)
    0x29, 0x65,        #   Usage Maximum (101)
    0x81, 0x00,        #   Input (Data, Array, Absolute) - Key array
    0xC0               # End Collection
])

# --- Main Run Function --------------------------------------------------------
def run(env):
    oled = env.get('oled')
    upside_down = env.get('upside_down', False)
    ok_button = Pin(code_ok_pin_value, Pin.IN, Pin.PULL_UP)
    menu_button = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)

    sidekick_id = settings_store.get_sidekick_id()
    device_name = f"Sidekick_{sidekick_id}"

    ble = None
    print("Trying to start bluetooth.")
    try:
        # Initialize BLE
        ble = bluetooth.BLE()
        print("Bluetooth created, trying to activate it.")
        ble.active(True)
        print("Successfully initialized Bluetooth.")

        # Start advertising
        adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(device_name) + 1, 0x09)) + device_name.encode()
        ble.gap_advertise(100000, adv_data=adv_data)
        print("Advertising...")

        # Main loop
        while True:
            if menu_button.value() == 0:
                break
            sleep_ms(50)

    except Exception as e:
        print(f"Error during Bluetooth test: {e}")
    finally:
        if ble:
            ble.gap_advertise(None)
            ble.active(False)
            print("Successfully de-initialized Bluetooth.")
