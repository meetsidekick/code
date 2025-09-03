from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from pin_values import code_debug_pin_value, buzzer_pin_value, led_pin_value, code_ok_pin_value
import settings_store
import framebuf
import ujson as json
import os

# Helper to detect custom core availability
def _custom_core_available():
    try:
        with open('custom_core.json','r') as f:
            data = json.load(f)
        return isinstance(data, dict) and ('faces' in data or 'sounds' in data)
    except Exception:
        return False

# Helper to render text respecting upside_down
def _text(oled, s, x, y, upside_down=False):
    if not upside_down:
        oled.text(s, x, y)
        return
    w = len(s) * 8
    h = 8
    buf = bytearray(w * h // 8)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_VLSB)
    fb.text(s, 0, 0, 1)
    for i in range(w):
        for j in range(h):
            if fb.pixel(i, j):
                fx = 128 - (x + (i + 1))
                fy = 64 - (y + (j + 1))
                if 0 <= fx < 128 and 0 <= fy < 64:
                    oled.pixel(fx, fy, 1)

code_debug_pin = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)
code_ok_pin = Pin(code_ok_pin_value, Pin.IN, Pin.PULL_UP)
led = Pin(led_pin_value, Pin.OUT)

# (Remove fixed MENU_ITEMS; build dynamically in open_menu)
MENU_FOOTER = "MENU=Down,OK=Yes"


def _render_menu(oled, items, idx, debug=False, upside_down=False):
    if oled is None:
        print("--- MENU ---")
        for i, item in enumerate(items):
            prefix = ">" if i == idx else " "
            if item["type"] == "toggle":
                state = "ON" if settings_store.is_muted() else "OFF"
                print(f"{prefix} {item['name']}: {state}")
            else:
                print(f"{prefix} {item['name']}")
        return
    try:
        oled.fill(0)
        lines = []
        for i, item in enumerate(items):
            marker = ">" if i == idx else " "
            if item["type"] == "toggle":
                state = "ON" if settings_store.is_muted() else "OFF"
                line = f"{marker}{item['name']}:{state}"
            else:
                line = f"{marker}{item['name']}"
            lines.append(line[:16])
        footer = MENU_FOOTER
        if upside_down:
            _text(oled, footer, 0, 54, True)
            base_y = 44
            for line in reversed(lines):
                _text(oled, line, 0, base_y, True)
                base_y -= 10
            _text(oled, "Menu", 0, 0, True)
        else:
            _text(oled, "Menu", 0, 0, False)
            for i, line in enumerate(lines):
                _text(oled, line, 0, 12 + i * 10, False)
            _text(oled, footer, 0, 54, False)
        if debug:
            _text(oled, "DBG", 100, 0, upside_down)
        oled.show()
    except Exception:
        pass


def open_menu(oled=None, debug_mode=False, upside_down=False, called_from_main=True):
    print("Now in menu mode")
    has_custom = _custom_core_available()
    # If custom not present, force core_type to Default for display only (do not flip stored if already Default/Custom)
    if not has_custom and settings_store.get_core_type() != 'Default':
        # Do not toggle automatically; just show Default label (user cannot toggle)
        pass
    core_label = settings_store.get_core_type() if has_custom else 'Default'
    # Build menu items dynamically based on context
    base_items = [
        {"name": f"Mute", "key": "mute", "type": "toggle"},
        {"name": f"Core: {core_label}", "key": "core", "type": "action"},
        {"name": "Reset Settings", "key": "reset", "type": "action"},
    ]
    if called_from_main:
        base_items.append({"name": "Go Back", "key": "exit", "type": "action"})
    else:
        base_items.extend([
            {"name": "Go Back", "key": "back", "type": "action"},
            {"name": "Exit to Main", "key": "exit", "type": "action"},
        ])
    menu_items = base_items
    selected = 0
    # Highlight Core by default (index 1) if present
    if len(menu_items) > 1:
        selected = 1
    while True:
        # Refresh core label each render
        display_core = settings_store.get_core_type() if has_custom else 'Default'
        for it in menu_items:
            if it.get('key') == 'core':
                it['name'] = f"Core: {display_core}"
        _render_menu(oled, menu_items, selected, debug_mode, upside_down)
        # Navigation: MENU button cycles down, OK selects
        if code_debug_pin.value() == 0:  # Down
            sleep_ms(20)
            if code_debug_pin.value() == 0:
                selected = (selected + 1) % len(menu_items)
                while code_debug_pin.value()==0:
                    sleep_ms(15)
        if code_ok_pin.value() == 0:  # Select / activate
            sleep_ms(20)
            if code_ok_pin.value() == 0:
                item = menu_items[selected]
                if item['key'] == 'mute':
                    settings_store.toggle_mute()
                elif item['key'] == 'core':
                    if has_custom:  # only toggle if custom exists
                        settings_store.toggle_core_type()
                elif item['key'] == 'reset':
                    settings_store.reset_settings()
                elif item['key'] in ('exit','back'):
                    while code_ok_pin.value()==0:
                        sleep_ms(15)
                    return item['key']
                while code_ok_pin.value()==0:
                    sleep_ms(15)
        sleep_ms(30)


