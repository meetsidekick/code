from time import ticks_ms, ticks_diff
import framebuf
import random

# Small text helper that respects upside_down
def _text(oled, text, x, y, upside_down=False):
    if not upside_down:
        oled.text(text, x, y)
        return
    w = len(text) * 8
    h = 8
    buf = bytearray(w * h // 8)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_VLSB)
    fb.text(text, 0, 0, 1)
    for i in range(w):
        for j in range(h):
            if fb.pixel(i, j):
                fx = 128 - (x + (i + 1))
                fy = 64 - (y + (j + 1))
                if 0 <= fx < 128 and 0 <= fy < 64:
                    oled.pixel(fx, fy, 1)

# --- Animation state ---
_last_blink_time = 0
_blinking = False
_next_blink_interval = None
_shake_start = None
_headpat_start = None

# --- Timing constants (ms) ---
BLINK_DURATION = 140
SHAKE_DURATION = 2000
HEADPAT_DURATION = 1200
SWAY_PERIOD = 1800

# --- ASCII-only, single-line, horizontal faces ---
FACES = {
    "happy": [
        '(^_^)', '(^_^)', "('-')",  # (^_^) → (^-^)
        "('-')", "('-')", '(^_^)',  # (^-^) → (^_^)
    ],
    "really_happy": [
        '(^o^)', '(^o^)', '(*^_^*)',  # (^o^) → (*^_^*)
        '(*^_^*)', '(*^_^*)', '(^o^)',  # (*^_^*) → (^o^)
    ],
    "curious": [
        '(o_o)', '(o_o)', '(-_-?)',  # (o_o) → (-_-?)
        '(-_-?)', '(-_-?)', '(._.)', # (-_-?) → (._.)
        '(._.)', '(._.)', '(-_-?)',  # (._.) → (-_-?)
        '(-_-?)', '(-_-?)', '(o_o)', # (-_-?) → (o_o)
    ],
    "concerned": [
        '(>_<)', '(>_<)', '(._.)',   # (>_<) → (._.)
        '(._.)', '(._.)', '(>_<)',   # (._.) → (>_<)
    ],
    "sad": [
        '(T_T)', '(T_T)', "(;_;)",   # (T_T) → (;_;)
    ],
    "sleepy": [
        '(-_-)', '(-_-)', '(u_u)',   # (-_- ) → (u_u)
    ],
    "mischief": [
        '(¬‿¬)', '(¬‿¬)', '(^_~)',  # (¬‿¬) → (^_~)
    ],
    "surprised": [
        '(O_O)', '(O_O)', '(o_O)',   # (O_O) → (o_O)
    ],
    "angry": [
        '(>_<)', '(>_<)', '(>:[)',   # (>_<) → (>: [)
    ],
    "cool": [
        '(-_-)', '(-_-)', '(B-)',    # (-_- ) → (B-)
    ],
    "love": [
        '(^3^)', '(^3^)', '(^.^)',   # (^3^) → (^.^)
    ],
    "headpat": [
        '(^_^)', '(^_^)', '(^_^*)',  # (^_^ ) → (^_^*)
    ],
    "shake": [
        '(@_@)', '(@_@)', '(x_x)',   # (@_@) → (x_x)
        '(x_x)', '(x_x)', '(O_o)',   # (x_x) → (O_o)
    ],
}

def _get_blink_interval():
    return random.randint(3000, 6000)

def _translate_emoji_blink(face):
    return (face
            .replace('^', '-')
            .replace('o', '-')
            .replace('O', '-')
            .replace('x', '-')
            .replace('_', '-'))

def _draw_ascii(oled, text, x, y, scale=2, upside_down=False):
    """Draw scaled ASCII text on oled"""
    char_width = 8 * len(text)
    char_height = 8
    temp_buf = bytearray(char_width * char_height // 8)
    temp_fb = framebuf.FrameBuffer(temp_buf, char_width, char_height, framebuf.MONO_VLSB)
    temp_fb.text(text, 0, 0, 1)
    for i in range(char_width):
        for j in range(char_height):
            if temp_fb.pixel(i, j):
                if upside_down:
                    # Flip both x and y coordinates for 180 degree rotation
                    flip_x = 128 - (x + (i + 1) * scale)
                    flip_y = 64 - (y + (j + 1) * scale)
                    oled.fill_rect(flip_x, flip_y, scale, scale, 1)
                else:
                    oled.fill_rect(x + i*scale, y + j*scale, scale, scale, 1)

def _centered_x(face, scale=2):
    w = len(face) * 8 * scale
    return max((128 - w) // 2, 0)

def get_face_and_x(mood, now, anim_state):
    if mood == "happy":
        idx = (now // 2000) % len(FACES["happy"])
        face = FACES["happy"][idx]
    elif mood == "really_happy":
        idx = (now // 1700) % len(FACES["really_happy"])
        face = FACES["really_happy"][idx]
    elif mood == "shake":
        phase_len = 210
        frame = ((ticks_diff(now, anim_state["start"]) // phase_len) % 3)
        face = FACES["shake"][frame]
        offset_seq = [-11, 0, 10]
        x = _centered_x(face) + offset_seq[frame]
        return face, x
    elif mood == "headpat":
        elapsed = ticks_diff(now, anim_state["start"])
        phase = (elapsed // 400) % 2
        face = FACES["headpat"][phase]
        x = _centered_x(face) + (2 if phase else -3)
        if phase == 1:
            face = face.replace(')', '*)', 1)
        return face, x
    else:
        period = SWAY_PERIOD
        try:
            from math import sin, pi
            t = (now % period) / period
            swing = int(7 * sin(2 * pi * t))
        except Exception:
            swing = 0
        key = FACES.get(mood, FACES["curious"])
        idx = (now // 2600) % len(key)
        face = key[idx]
        x = _centered_x(face) + swing
        return face, x

    x = _centered_x(face)
    return face, x

def update_oled(oled, mood="happy", value=50, upside_down=False, debug_mode=False):
    global _last_blink_time, _blinking, _next_blink_interval, _shake_start, _headpat_start
    now = ticks_ms()
    anim_state = {}

    if mood == "shake":
        if _shake_start is None:
            _shake_start = now
        anim_state["start"] = _shake_start
        if ticks_diff(now, _shake_start) > SHAKE_DURATION:
            _shake_start = None
            mood = "happy"
    else:
        _shake_start = None
    if mood == "headpat":
        if _headpat_start is None:
            _headpat_start = now
        anim_state["start"] = _headpat_start
        if ticks_diff(now, _headpat_start) > HEADPAT_DURATION:
            _headpat_start = None
            mood = "happy"
    else:
        _headpat_start = None

    blinkable = mood not in ("shake", "headpat")
    if _next_blink_interval is None:
        _next_blink_interval = _get_blink_interval()
    if blinkable:
        if ticks_diff(now, _last_blink_time) > _next_blink_interval:
            _blinking = True
            _last_blink_time = now
            _next_blink_interval = _get_blink_interval()
        if _blinking and ticks_diff(now, _last_blink_time) > BLINK_DURATION:
            _blinking = False

    face, x = get_face_and_x(mood, now, anim_state)

    if blinkable and _blinking:
        face = _translate_emoji_blink(face)

    oled.fill(0)
    _draw_ascii(oled, face, x, 20, 2, upside_down)
    
    # Draw debug indicator in corner if debug mode is active
    if debug_mode:
        debug_text = "DBG"
        if upside_down:
            # Bottom left corner when upside down
            _text(oled, debug_text, 2, 56, True)
        else:
            # Top right corner when normal
            _text(oled, debug_text, 128 - len(debug_text) * 8, 0, False)
    
    oled.show()

def demo_emotions(oled):
    from time import sleep_ms
    loop = [
        "happy", "curious", "mischief",
        "surprised", "cool", "sad", "shake", "headpat"
    ]
    for mood in loop:
        frames = 26 if mood in ("shake", "headpat") else 18
        for _ in range(frames):
            update_oled(oled, mood)
            sleep_ms(68)
