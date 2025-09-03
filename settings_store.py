# Simple persistent settings store for MicroPython
# Stores settings in a small JSON file on the device filesystem.

import ujson as json

_SETTINGS_FILE = "settings.json"
_default_settings = {
    "mute": False,
}

_settings = {}


def _save():
    try:
        with open(_SETTINGS_FILE, "w") as f:
            json.dump(_settings, f)
    except Exception as e:
        # Silent fail is acceptable in constrained environments
        pass


def _load():
    global _settings
    try:
        with open(_SETTINGS_FILE, "r") as f:
            _settings = json.load(f)
    except Exception:
        _settings = _default_settings.copy()
        _save()


def is_muted():
    return _settings.get("mute", False)


def toggle_mute():
    _settings["mute"] = not _settings.get("mute", False)
    _save()
    return _settings["mute"]


# Initialize on import
_load()
