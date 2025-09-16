import network
import uasyncio as asyncio
import time
import binascii
import os
import ujson as json
import sys
import io

import settings_store
from machine import Pin, reset
from pin_values import code_debug_pin_value, code_ok_pin_value
from menu import get_preserved_files

# --- Globals --- #
_server_mode = 'setup'
_app_runner = None
setup_complete_event = asyncio.Event()

def get_random_hex():
    return binascii.hexlify(os.urandom(3)).decode('utf-8')

# --- App Runner Class --- #
class AppRunner:
    def __init__(self, env):
        self.task = None
        self.logs = io.StringIO()
        self.original_stdout = sys.stdout
        self.env = env

    def is_running(self):
        return self.task is not None and not self.task.done()

    def get_logs(self):
        return self.logs.getvalue()

    def start(self, filename):
        if self.is_running():
            return False
        
        self.logs = io.StringIO()
        sys.stdout = self.logs
        self.task = asyncio.create_task(self._run_app(filename))
        return True

    async def _run_app(self, filename):
        try:
            module_name = filename[:-3]
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            module = __import__(module_name)
            if hasattr(module, 'run'):
                module.run(self.env)
            else:
                print(f"Error: {filename} has no run(env) function.")
        except Exception as e:
            print(f"App Error: {e}")
        finally:
            self.stop()

    def stop(self):
        if self.task:
            self.task.cancel()
            self.task = None
        sys.stdout = self.original_stdout

# --- Web Server Logic --- #
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

        body = None
        if 'content-length' in headers:
            body = await reader.readexactly(int(headers['content-length']))

        # Captive Portal
        host = headers.get('host', '')
        if 'generate_204' in path or 'connecttest.txt' in path or 'hotspot-detect.html' in path or 'connectivitycheck' in host:
            redirect_url = 'http://192.168.4.1' + ('/#dashboard' if _server_mode == 'dashboard' else '')
            await writer.awrite(b'HTTP/1.1 302 Found\r\nLocation: ' + redirect_url.encode() + b'\r\n\r\n')
            return

        # API Routing
        if path == '/':
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nCache-Control: no-cache\r\n\r\n')
            with open('sidekick-setup.html', 'rb') as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    await writer.awrite(chunk)
        elif path == '/api/apps' and method == 'GET':
            preserved = get_preserved_files()
            apps = [{'name': f, 'preserved': f in preserved} for f in os.listdir() if f.startswith('custom_code_') and f.endswith('.py')]
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            await writer.awrite(json.dumps(apps).encode())
        elif path == '/api/apps' and method == 'POST':
            data = json.loads(body)
            filename = data.get('name')
            if filename in get_preserved_files():
                await writer.awrite(b'HTTP/1.1 403 Forbidden\r\n\r\nCannot modify preserved file.')
            elif filename and filename.startswith('custom_code_') and filename.endswith('.py'):
                with open(filename, 'w') as f:
                    f.write(data.get('code', ''))
                await writer.awrite(b'HTTP/1.1 201 Created\r\n\r\n')
            else:
                await writer.awrite(b'HTTP/1.1 400 Bad Request\r\n\r\nInvalid filename.')
        elif path == '/codejar.min.js':
            with open('codejar.min.js', 'rb') as f:
                await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n')
                await writer.awrite(f.read())
        elif path == '/api/status' and method == 'GET':
            status = {
                "setup_completed": settings_store._settings.get('setup_completed', False),
                "user_name": settings_store._settings.get('user_name', 'User'),
                "sidekick_name": settings_store._settings.get('sidekick_name', 'Sidekick'),
            }
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            await writer.awrite(json.dumps(status).encode())
# ...
    # ...
        elif path == '/save' and method == 'POST':
            global user_data
            data = {k: v for k, v in [pair.split('=', 1) for pair in body.decode().split('&') if '=' in pair]}
            user_data = {
                'user_name': data.get('user_name', 'User'),
                'sidekick_name': data.get('sidekick_name', 'Sidekick'),
            }
            setup_complete_event.set()
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            await writer.awrite(json.dumps({'status': 'success'}).encode())
            await asyncio.sleep_ms(10) # Give event loop a chance to switch context
        elif path.startswith('/api/app/'):
            filename = path.split('/')[-1]
            if method == 'GET':
                with open(filename, 'r') as f: content = f.read()
                await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n' + content.encode())
            elif method == 'DELETE':
                if filename in get_preserved_files():
                    await writer.awrite(b'HTTP/1.1 403 Forbidden\r\n\r\nCannot delete preserved file.')
                else:
                    os.remove(filename)
                    await writer.awrite(b'HTTP/1.1 204 No Content\r\n\r\n')
        elif path == '/api/run' and method == 'POST':
            filename = json.loads(body).get('name')
            if not _app_runner.is_running() and filename:
                _app_runner.start(filename)
                await writer.awrite(b'HTTP/1.1 200 OK\r\n\r\n')
            else:
                await writer.awrite(b'HTTP/1.1 409 Conflict\r\n\r\nApp already running.')
        elif path == '/api/stop' and method == 'POST':
            if _app_runner.is_running(): _app_runner.stop()
            await writer.awrite(b'HTTP/1.1 200 OK\r\n\r\n')
        elif path == '/api/logs' and method == 'GET':
            await writer.awrite(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n' + _app_runner.get_logs().encode())
        else:
            await writer.awrite(b'HTTP/1.1 404 Not Found\r\n\r\n')
    except Exception as e:
        print(f"Request Error: {e}")
    finally:
        await writer.aclose()

async def main_server_loop(ap):
    server = await asyncio.start_server(handle_request, '0.0.0.0', 80)
    if _server_mode == 'dashboard':
        menu_button = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)
        while True:
            if menu_button.value() == 0: # Button pressed
                break # Exit immediately on press
            await asyncio.sleep_ms(100)
    else: # setup mode
        print("DEBUG: main_server_loop waiting for setup_complete_event.")
        await setup_complete_event.wait()
        print("DEBUG: main_server_loop setup_complete_event received.") # In setup, run until device is reset
    server.close()
    await server.wait_closed()
    ap.active(False)

def run_server(mode, oled, upside_down):
    global _server_mode, _app_runner, user_data
    _server_mode = mode
    
    # Create full env for app runner
    env = {
        'oled': oled,
        'upside_down': upside_down,
        'settings': settings_store,
        'Pin': Pin,
        'i2c': None, # Placeholder, would need to be passed in from main
        'mpu': None, # Placeholder
    }
    _app_runner = AppRunner(env)

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    password = settings_store.get_ap_password()
    
    if mode == 'dashboard':
        sidekick_id = settings_store.get_sidekick_id()
        ssid = f"Sidekick_{sidekick_id}"
    else: # setup
        sidekick_id = settings_store.get_sidekick_id()
        ssid = f"Sidekick_{sidekick_id}"

    ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active(): time.sleep(0.1)

    from oled_functions import update_oled
    oled.fill(0)
    update_oled(oled, "text", "Dashboard Mode" if mode == 'dashboard' else "Web Setup", upside_down, line=1)
    update_oled(oled, "text", f"AP:{ssid}", upside_down, line=3)
    update_oled(oled, "text", f"Pass: {password}", upside_down, line=4)
    update_oled(oled, "text", f"192.168.4.1", upside_down, line=5)
    if mode == 'dashboard': update_oled(oled, "text", "(Menu to Exit)", upside_down, line=6)
    oled.show()

    # In setup mode, we need to run the asyncio loop until the setup is complete.
    # We must not close the loop, as this will break other asyncio-based scripts.
    if mode == 'setup':
        try:
            # Get the existing event loop.
            loop = asyncio.get_event_loop()

            # Create and run the server task.
            server_task = loop.create_task(main_server_loop(ap))

            # Run the loop until the setup_complete_event is set.
            loop.run_until_complete(setup_complete_event.wait())

            # Once setup is complete, cancel the server task.
            # This is important for cleanup.
            server_task.cancel()

            # We need to run the loop one last time to allow the cancelled task to finish.
            # We use run_until_complete on the cancelled task.
            try:
                loop.run_until_complete(server_task)
            except asyncio.CancelledError:
                pass  # This is expected.

        finally:
            # Deactivate and de-initialize the access point.
            ap.active(False)
            #ap.deinit()
            print("Web setup complete, AP deactivated and de-initialized.")
        return user_data
    else: # dashboard mode
        try:
            loop = asyncio.get_event_loop()
            server_task = loop.create_task(main_server_loop(ap))
            
            # Run the loop until the server_task completes (i.e., dashboard exits via long press)
            loop.run_until_complete(server_task)

        except asyncio.CancelledError:
            pass # Expected if the task is cancelled externally, though not expected here.



def start_web_setup(oled, upside_down):
    return run_server('setup', oled, upside_down)

def start_dashboard_server(oled, upside_down):
    run_server('dashboard', oled, upside_down)
