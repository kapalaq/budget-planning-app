"""Multi-language support for the budget planner."""

import json
import os
from pathlib import Path

_LANG_DIR = Path(__file__).parent
_LANGUAGES: dict[str, dict[str, str]] = {}
_DEFAULT_LANG = "en-US"

# Available languages: display name → code
AVAILABLE_LANGUAGES = {
    "en-US": "English (US)",
    "en-UK": "English (UK)",
    "ru-RU": "Русский",
}


def _load_language(code: str) -> dict[str, str]:
    """Load a language file from disk."""
    # en-US -> en_US.json
    filename = code.replace("-", "_") + ".json"
    path = _LANG_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_lang(code: str) -> dict[str, str]:
    """Get language dict, loading from cache or disk."""
    if code not in _LANGUAGES:
        _LANGUAGES[code] = _load_language(code)
    return _LANGUAGES[code]


def t(key: str, lang: str = _DEFAULT_LANG, **kwargs) -> str:
    """Translate a key to the given language.

    Falls back to en-US if key not found in the requested language.
    Falls back to the key itself if not found in any language.

    Supports {placeholder} substitution via kwargs.
    """
    strings = _get_lang(lang)
    text = strings.get(key)
    if text is None:
        # Fallback to default language
        if lang != _DEFAULT_LANG:
            text = _get_lang(_DEFAULT_LANG).get(key)
        if text is None:
            text = key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


# Pre-load default language
_get_lang(_DEFAULT_LANG)
