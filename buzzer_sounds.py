from machine import Pin, PWM
import time
import random

from pin_values import buzzer_pin_value#, led_pin_value
import settings_store
import ujson as json

# Initialize PWM for the buzzer and digital output for the LED
buzzer = PWM(Pin(buzzer_pin_value))
buzzer.duty_u16(0)  # Ensure buzzer is silent at startup

#led = Pin(led_pin_value, Pin.OUT)
#led.value(0)        # Ensure LED is off at startup

# Core data cache
_core_cache = None

def _load_core():
    global _core_cache
    if _core_cache is not None:
        return _core_cache
    # Decide file: custom_core.json preferred if valid
    for fname in ("custom_core.json", "default_core.json"):
        try:
            with open(fname, "r") as f:
                data = json.load(f)
            # minimal validation
            if "sounds" in data:
                _core_cache = data
                return _core_cache
        except Exception:
            continue
    _core_cache = {"sounds": {}}
    return _core_cache

_core = _load_core()

# Provide default sequences if core missing
_DEFAULT_SEQUENCES = {
    "happy_sound": [[1319,18],[1568,18],[1760,18],[2093,18],[2349,18],[2637,40]],
    "angry_sound": [[1760,15],[2093,15],[1568,15],[2349,15],[1760,15],[2637,15],[1397,15],[2093,15]],
    "headpat_sound": [[1175,15],[1397,15],[1760,15],[2093,15],[2637,80]],
    "click_sound": [[3000,20],[4000,20]],
    "startup_sequence": [[2000,15],[2500,15],[3000,15],[3500,15]],
    "curious_scared_sound": [[1319,18],[1568,18],[1760,18]],
    "eepy_sound": [[2093,30],[1760,35],[1568,40],[1397,45],[1568,50],[1319,140]],
    "shook_sound": [[1568,12],[1245,12],[1568,12],[1319,12],[1568,12],[1175,12],[1568,12],[1319,12]],
    "buzzer_beeping": [[1000, 100], [0, 50], [1000, 100], [0, 50], [1000, 100]],
}

# --- Low-level helpers ---
def startup_shush():
    """Ensure the buzzer is silent at startup."""
    buzzer.duty_u16(0)


def play_tone(freq, duration):
    if settings_store.is_muted():
        time.sleep_ms(duration)
        return
    if freq > 0:
        #led.value(1)
        buzzer.freq(freq)
        buzzer.duty_u16(32768)  # 50% duty cycle
    time.sleep_ms(duration)
    buzzer.duty_u16(0)
    #led.value(0)


def _play_sequence(name):
    sounds = _core.get("sounds", {})
    snd = sounds.get(name)
    if not snd:
        seq = _DEFAULT_SEQUENCES.get(name, [])
        for freq, dur in seq:
            play_tone(freq, dur)
        return
    seq = snd.get("sequence", [])
    if not seq:
        seq = _DEFAULT_SEQUENCES.get(name, [])
    for pair in seq:
        try:
            freq, dur = pair
            play_tone(int(freq), int(dur))
        except Exception:
            pass
    follow = snd.get("follow")
    if follow:
        _play_sequence(follow)

# Public wrappers preserve existing API

def happy_sound():
    _play_sequence("happy_sound")


def angry_sound():
    _play_sequence("angry_sound")


def shook_sound():
    # Optionally randomize by slight pitch jitter if defined
    snd = _core.get("sounds", {}).get("shook_sound")
    if snd and snd.get("sequence"):
        for pair in snd["sequence"]:
            try:
                freq, dur = pair
                if freq > 0:
                    freq += random.randint(-20, 20)
                play_tone(int(freq), int(dur))
            except Exception:
                pass
    else:
        _play_sequence("shook_sound")


def headpat_sound():
    _play_sequence("headpat_sound")


def click_sound():
    _play_sequence("click_sound")


def startup_sequence():
    _play_sequence("startup_sequence")


def curious_scared_sound():
    _play_sequence("curious_scared_sound")


def eepy_sound():
    _play_sequence("eepy_sound")

def buzzer_beeping():
    _play_sequence("buzzer_beeping")

# Run test sequence if the script is executed directly
if __name__ == "__main__":
    startup_shush()
    startup_sequence()
    time.sleep_ms(500)
    happy_sound()
    time.sleep_ms(500)
    angry_sound()
    time.sleep_ms(500)
    shook_sound()
    time.sleep_ms(500)
    curious_scared_sound()
    time.sleep_ms(500)
    eepy_sound()

