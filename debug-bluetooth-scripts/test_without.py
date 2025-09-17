import ubluetooth as bluetooth
import gc
import time

print("--- Starting test (without conflicting stuff) ---")
print("Initializing Bluetooth...")
try:
    gc.collect()
    print(f"Free memory before BLE init: {gc.mem_free()} bytes")
    ble = bluetooth.BLE()
    ble.active(True)
    print("Successfully initialized Bluetooth.")

    print("Starting advertising...")
    ble.gap_advertise(100000, adv_data=b'\x02\x01\x06\x1a\xff\x4c\x00\x02\x15\xe2\xc5\x6d\xb5\xdf\xfb\x48\xd2\xb0\x60\xd0\xf5\xa7\x10\x96\xe0\x00\x00\x00\x00\xc5')
    time.sleep(2)
    print("Stopping advertising...")
    ble.gap_advertise(None)

    ble.active(False)
    print("Successfully de-initialized Bluetooth.")
except Exception as e:
    print(f"Error during Bluetooth test: {e}")
print("--- Test finished ---")