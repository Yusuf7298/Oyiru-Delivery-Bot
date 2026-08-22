import os
import json
import logging
from typing import Dict, Any

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")
_translations: Dict[str, Dict[str, str]] = {}

def load_translations() -> None:
    global _translations
    _translations = {}
    for lang in ["en", "am", "om"]:
        file_path = os.path.join(TRANSLATIONS_DIR, f"{lang}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    _translations[lang] = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load translation file {file_path}: {e}")
                _translations[lang] = {}
        else:
            _translations[lang] = {}

load_translations()

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    lang = (lang or "en").lower()
    if lang not in _translations:
        lang = "en"
    
    val = _translations.get(lang, {}).get(key)
    if val is None:
        val = _translations.get("en", {}).get(key, key)
    
    if kwargs and isinstance(val, str):
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val

