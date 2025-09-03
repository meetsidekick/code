# LED Example (custom_code_led.py)
# Minimal user-facing run(): press button to blink LED, long press to exit.
# Orientation (upside_down) respected. This file shows how helpers can hide complexity.

from time import ticks_ms, ticks_diff

# --- Internal helpers (abstracted) -----------------------------------------

def _get_led(Pin):
    try:
        from pin_values import led_pin_value
        return Pin(led_pin_value, Pin.OUT)
    except Exception:
        for guess in (2, 25):
            try:
                return Pin(guess, Pin.OUT)
            except Exception:
                pass
    return None

def _text(oled, s, x, y, upside_down=False):
    if not oled:
        return
    try:
        if not upside_down:
            oled.text(s, x, y)
        else:
            # Simple flipped placement (coarse – fits 8x8 font cells)
            fx = 128 - (x + len(s)*8)
            fy = 64 - (y + 8)
            if fx < 0: fx = 0
            if fy < 0: fy = 0
            oled.text(s, fx, fy)
    except Exception:
        pass

def _draw(oled, count, led_on, upside_down):
    if not oled: return
    try:
        oled.fill(0)
        _text(oled, 'LED Example', 0, 0, upside_down)
        _text(oled, 'Count:'+str(count), 0, 14, upside_down)
        _text(oled, 'LED:' + ('ON' if led_on else 'OFF'), 0, 26, upside_down)
        _text(oled, 'Press=Blink', 0, 38, upside_down)
        _text(oled, 'Hold=Exit', 0, 50, upside_down)
        oled.show()
    except Exception:
        pass

def _loop(env):
    oled = env.get('oled')
    menu_btn = env.get('menu_button')
    ok_btn = env.get('ok_button')
    sleep_ms = env.get('sleep_ms') or (lambda x: None)
    Pin = env.get('Pin')
    upside_down = env.get('upside_down', False)

    print('[LED] Loaded example (upside_down=%s)' % upside_down)
    # Button scheme: OK = action, MENU = exit back immediately
    action_btn = ok_btn if ok_btn else menu_btn

    led = _get_led(Pin) if Pin else None
    blink_count = 0
    last_state = 1  # assume pull-up idle

    _draw(oled, blink_count, False, upside_down)

    while True:
        # MENU button exits immediately (short press)
        if menu_btn and menu_btn.value()==0:
            while menu_btn.value()==0:  # debounce release
                sleep_ms(15)
            print('[LED] Exit via MENU')
            return
        v = action_btn.value() if action_btn else 1
        # OK press edge -> blink
        if action_btn and action_btn is ok_btn and last_state == 1 and v == 0:
            blink_count += 1
            print('[LED] Blink #%d' % blink_count)
            if led:
                try: led.value(1)
                except Exception: pass
            _draw(oled, blink_count, True, upside_down)
            sleep_ms(180)
            if led:
                try: led.value(0)
                except Exception: pass
            _draw(oled, blink_count, False, upside_down)
            # Wait for release to avoid auto-repeat
            while action_btn.value()==0:
                sleep_ms(15)
        last_state = v
        sleep_ms(30)

# --- User entry point (kept intentionally tiny) -----------------------------

def run(env):
    _loop(env)
