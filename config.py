import os
import sys
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
try:
    import importlib.util
    base_dir = os.path.dirname(__file__)
    def load_submodule(name, filename):
        path = os.path.join(base_dir, "config", filename)
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location(f"config.{name}", path)
            mod = importlib.util.module_from_spec(spec) # type: ignore
            sys.modules[f"config.{name}"] = mod
            spec.loader.exec_module(mod) # type: ignore
            setattr(sys.modules[__name__], name, mod)
            
    load_submodule("settings", "settings.py")
    load_submodule("logging", "logging.py")
    load_submodule("constants", "constants.py")
except Exception:
    pass