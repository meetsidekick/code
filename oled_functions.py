from time import ticks_ms, ticks_diff
import ujson as json
import random
import framebuf
import settings_store

# Default face sets (fallback if core json missing)
DEFAULT_FACES = {
    "happy": ['(^_^)', '(^_^)', "('-')", "('-')", "('-')", '(^_^)'],
    "really_happy": ['(^o^)', '(^o^)', '(*^_^*)', '(*^_^*)', '(*^_^*)', '(^o^)'],
    "curious": ['(o_o)', '(o_o)', '(-_-?)', '(-_-?)', '(-_-?)', '(._.)', '(._.)', '(._.)', '(-_-?)', '(-_-?)', '(-_-?)', '(o_o)'],
    "concerned": ['(>_<)', '(>_<)', '(._.)', '(._.)', '(._.)', '(>_<)'],
    "sad": ['(T_T)', '(T_T)', '(;_;)'],
    "sleepy": ['(-_-)', '(-_-)', '(u_u)'],
    "mischief": ['(¬‿¬)', '(¬‿¬)', '(^_~)'],
    "surprised": ['(O_O)', '(O_O)', '(o_O)'],
    "angry": ['(>_<)', '(>_<)', '(>: [)'],
    "cool": ['(-_-)', '(-_-)', '(B-)'],
    "love": ['(^3^)', '(^3^)', '(^.^)'],
    "headpat": ['(^_^)', '(^_^)', '(^_^*)'],
    "shake": ['(@_@)', '(@_@)', '(x_x)', '(x_x)', '(x_x)', '(O_o)'],
}

# Load core faces
_core_cache = None

def _load_core():
    global _core_cache
    if _core_cache is not None:
        return _core_cache
    for fname in ("custom_core.json", "default_core.json"):
        try:
            with open(fname, 'r') as f:
                data = json.load(f)
            faces = data.get('faces', {}) if isinstance(data, dict) else {}
            merged = dict(DEFAULT_FACES)
            for k, v in faces.items():
                if isinstance(v, list) and v:
                    merged[k] = v
            data['faces'] = merged
            if 'faces' in data:
                _core_cache = data
                return _core_cache
        except Exception:
            continue
    # Fallback purely defaults
    _core_cache = {"faces": dict(DEFAULT_FACES), "display": {"upside_down": False}}
    return _core_cache

_core = _load_core()
DEFAULT_UPSIDE = _core.get('display', {}).get('upside_down', False)
FACES = _core.get('faces', dict(DEFAULT_FACES))

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

def _seq(name):
    return FACES.get(name) or DEFAULT_FACES.get(name) or ['(._.)']

def get_face_and_x(mood, now, anim_state):
    if mood == "happy":
        seq = _seq('happy')
        idx = (now // 2000) % len(seq)
        face = seq[idx]
    elif mood == "really_happy":
        seq = _seq('really_happy')
        idx = (now // 1700) % len(seq)
        face = seq[idx]
    elif mood == "shake":
        seq = _seq('shake')
        phase_len = 210
        frame = ((ticks_diff(now, anim_state.get("start", now)) // phase_len) % min(3, len(seq)))
        face = seq[frame]
        offset_seq = [-11, 0, 10]
        x = _centered_x(face) + offset_seq[frame % len(offset_seq)]
        return face, x
    elif mood == "headpat":
        seq = _seq('headpat')
        elapsed = ticks_diff(now, anim_state.get("start", now))
        if len(seq) < 2:
            face = seq[0]
            x = _centered_x(face)
            return face, x
        phase = (elapsed // 400) % 2
        face = seq[phase]
        x = _centered_x(face) + (2 if phase else -3)
        return face, x
    else:
        seq = _seq(mood if mood in FACES else 'curious')
        period = SWAY_PERIOD
        try:
            from math import sin, pi
            t = (now % period) / period
            swing = int(7 * sin(2 * pi * t))
        except Exception:
            swing = 0
        idx = (now // 2600) % len(seq)
        face = seq[idx]
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

    # --- Status overlay (DBG + mute) ---
    parts = []
    if debug_mode:
        parts.append("DBG")
    if settings_store.is_muted():
        parts.append("M")  # Single letter muted indicator
    if parts:
        status = " ".join(parts)
        if upside_down:
            # Bottom-left when upside down
            _text(oled, status, 0, 56, True)
        else:
            # Top-right when normal orientation
            _text(oled, status, 128 - len(status)*8, 0, False)

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
