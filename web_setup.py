import network
import socket
import time
import binascii
import os
import ujson as json
import settings_store
from machine import reset

# (QR Code and mDNS would be implemented here)

def qrcode_gen(text, oled, upside_down):
    from oled_functions import update_oled
    oled.fill(0)
    ssid = text.split('WIFI:S:')[1].split(';')[0]
    update_oled(oled, "text", "Scan or connect:", upside_down, line=1)
    update_oled(oled, "text", "192.168.4.1", upside_down, line=3)
    update_oled(oled, "text", f"AP: {ssid}", upside_down, line=5)
    oled.show()

def get_random_hex():
    return binascii.hexlify(os.urandom(3)).decode('utf-8')

def handle_request(cl, addr):
    print('Client connected from', addr)
    try:
        # Read the entire request (up to a certain size)
        # This is a compromise for MicroPython's limited socket features.
        # A real HTTP server would read in chunks until headers are parsed.
        request = cl.recv(2048).decode('utf-8') # Increased buffer size to 2048
        print(f"Received Request:\n{request}") # Debugging: print raw request
        
        try:
            request_line = request.split('\r\n')[0]
            method, path, _ = request_line.split(' ')
            print(f"Parsed: Method={method}, Path={path}") # Debugging: parsed request
        except ValueError:
            print("Error: Could not parse request line.") # Debugging
            cl.close()
            return False, None, None

        # Parse headers
        headers = {}
        headers_end = request.find('\r\n\r\n')
        if headers_end != -1:
            headers_str = request[:headers_end]
            for line in headers_str.split('\r\n')[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

        if method == 'POST' and path == '/save':
            print("Handling POST /save") # Debugging
            content_length = int(headers.get('content-length', 0))
            body = request[headers_end+4:] # Get body from initial request

            # Read remaining body if not fully received in initial recv
            # This loop is crucial if the body is larger than the initial recv buffer
            while len(body) < content_length:
                body += cl.recv(content_length - len(body)).decode('utf-8')

            # Parse URL-encoded body
            data = {}
            for pair in body.split('&'):
                if '=' in pair: # Ensure pair has an '='
                    key, value = pair.split('=', 1)
                    data[key] = value # No unquoting needed for simple values
                else: # Handle cases like just a key with no value
                    data[pair] = ''

            settings = settings_store._settings
            settings['user_name'] = data.get('user_name', 'User')
            settings['sidekick_name'] = data.get('sidekick_name', 'Sidekick')
            settings['setup_completed'] = True
            settings_store._save()

            cl.send(b'HTTP/1.1 200 OK\r\n')
            cl.send(b'Content-Type: application/json\r\n')
            cl.send(b'Access-Control-Allow-Origin: *\n')
            cl.send(b'\r\n')
            cl.send(json.dumps({'status': 'success'}))
            cl.close()
            return True, data.get('user_name', 'User'), data.get('sidekick_name', 'Sidekick')

        elif method == 'GET' and path == '/':
            print("Handling GET /") # Debugging
            with open("www/index.html", "r") as f:
                response = f.read()
            cl.send(b'HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response.encode('utf-8'))
            print("Served index.html") # Debugging
        
        elif method == 'GET' and path == '/style.css':
            print("Handling GET /style.css") # Debugging
            with open("www/style.css", "r") as f:
                response = f.read()
            cl.send(b'HTTP/1.1 200 OK\r\nContent-type: text/css\r\n\r\n')
            cl.send(response.encode('utf-8'))
            print("Served style.css") # Debugging

        elif method == 'GET' and path == '/script.js':
            print("Handling GET /script.js") # Debugging
            with open("www/script.js", "r") as f:
                response = f.read()
            cl.send(b'HTTP/1.1 200 OK\r\nContent-type: application/javascript\r\n\r\n')
            cl.send(response.encode('utf-8'))
            print("Served script.js") # Debugging

        else:
            print(f"Error: 404 Not Found for path: {path}") # Debugging
            cl.send(b'HTTP/1.1 404 Not Found\r\n\r\nFile not found')

    except Exception as e:
        print(f"General Request Handling Error: {e}") # Debugging
        cl.close()
    
    return False, None, None

def start_web_setup(oled, upside_down):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
    ssid = f"Sidekick-{get_random_hex()[:6]}"
    ap.config(essid=ssid, password="sidekick")

    while not ap.active():
        time.sleep(0.1)

    print(f"AP created with SSID: {ssid}, IP: {ap.ifconfig()[0]}")
    # (mDNS would be started here)

    qr_text = f"WIFI:S:{ssid};T:WPA;P:sidekick;H:;"
    qrcode_gen(qr_text, oled, upside_down)

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print('Listening on', addr)

    # Listen for a few connections, then timeout
    # This is a simple server, a real one would be more robust
    for _ in range(100): # Handle up to 100 requests before restarting
        cl, addr = s.accept()
        success, user_name, sidekick_name = handle_request(cl, addr)
        if success:
            ap.active(False)
            return True, user_name, sidekick_name

    ap.active(False)
    return False, "User", "Sidekick" # Fallback if setup isn't completed