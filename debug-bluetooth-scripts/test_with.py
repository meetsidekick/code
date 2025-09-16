import ubluetooth as bluetooth
import gc
import time
import network
import uasyncio as asyncio

# --- Web Server Code (adapted from web_setup.py) ---

async def handle_request(reader, writer):
    try:
        request_line = await reader.readline()
        if not request_line or request_line == b'\r\n': return

        method, path, _ = request_line.decode().split()
        headers = {}
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n': break
            key, value = line.decode().split(':', 1)
            headers[key.strip().lower()] = value.strip()

        if path == '/':
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nCache-Control: no-cache\r\n\r\n')
            with open('www/sidekick-setup.html', 'rb') as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    await writer.awrite(chunk)
        elif path == '/codejar.min.js':
            with open('www/codejar.min.js', 'rb') as f:
                await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n')
                await writer.awrite(f.read())
        else:
            await writer.awrite(b'HTTP/1.1 404 Not Found\r\n\r\n')
    except Exception as e:
        print(f"Request Error: {e}")
    finally:
        await writer.aclose()

async def run_web_server():
    print("Starting web server...")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="test-ap", password="password")
    while not ap.active():
        time.sleep(0.1)
    print("Web server started.")

    server = await asyncio.start_server(handle_request, '0.0.0.0', 80)

    # Run the server for 5 seconds
    await asyncio.sleep(5)

    server.close()
    await server.wait_closed()
    ap.active(False)
    print("Web server stopped.")


# --- Test Code ---

print("--- Starting test (with conflicting stuff) ---")
print("Importing first_boot.py...")
try:
    import first_boot
    print("Successfully imported first_boot.py")
except Exception as e:
    print(f"Error importing first_boot.py: {e}")

# Run the web server
try:
    asyncio.run(run_web_server())
except Exception as e:
    print(f"Error running web server: {e}")


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