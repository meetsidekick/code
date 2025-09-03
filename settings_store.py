# Simple persistent settings store for MicroPython
# Stores settings in a small JSON file on the device filesystem.

import ujson as json
import os  # added for file deletion

_SETTINGS_FILE = "settings.json"
_default_settings = {
    "mute": False,
    "core_type": "Custom",  # Default highlight Custom; fallback to Default if not present
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


def get_core_type():
    return _settings.get("core_type", "Default")


def toggle_core_type():
    current = get_core_type()
    _settings["core_type"] = "Custom" if current == "Default" else "Default"
    _save()
    return _settings["core_type"]


def reset_settings():
    """Delete settings file and restore defaults in memory and on disk."""
    global _settings
    try:
        if _SETTINGS_FILE in os.listdir():
            os.remove(_SETTINGS_FILE)
    except Exception:
        pass
    _settings = _default_settings.copy()
    _save()
    return _settings.copy()

# Initialize on import
_load()
