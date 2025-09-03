from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from pin_values import code_debug_pin_value, buzzer_pin_value, led_pin_value, code_ok_pin_value
import settings_store
import framebuf

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
    # Build menu items dynamically based on context
    if called_from_main:
        menu_items = [
            {"name": "Mute", "key": "mute", "type": "toggle"},
            {"name": "Go Back", "key": "exit", "type": "action"},
        ]
    else:
        menu_items = [
            {"name": "Mute", "key": "mute", "type": "toggle"},
            {"name": "Go Back", "key": "back", "type": "action"},
            {"name": "Exit to Main", "key": "exit", "type": "action"},
        ]

    selected = 0

    while True:
        _render_menu(oled, menu_items, selected, debug_mode, upside_down)
        # Navigation: MENU button cycles down, OK selects
        if code_debug_pin.value() == 0:  # Down
            sleep_ms(20)
            if code_debug_pin.value() == 0:
                selected = (selected + 1) % len(menu_items)
                sleep_ms(250)  # Debounce / simple repeat delay
        if code_ok_pin.value() == 0:  # Select / activate
            sleep_ms(20)
            if code_ok_pin.value() == 0:
                item = menu_items[selected]
                if item["type"] == "toggle":
                    new_state = settings_store.toggle_mute()
                    print(f"Mute toggled -> {new_state}")
                elif item["key"] == "exit":
                    print("Exiting to Main" if not called_from_main else "Going Back")
                    return "exit"
                elif item["key"] == "back":
                    print("Going Back")
                    return "back"
                sleep_ms(300)
        sleep_ms(30)


