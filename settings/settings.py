import os
import sys
import importlib

CACHE_TYPE = "SimpleCache"
CACHE_DEFAULT_TIMEOUT = 300

sys.path.insert(0, os.path.dirname(__file__))
settings_name = f"{os.environ.get('FLASK_ENV')}_settings"
settings_model = importlib.import_module(settings_name)
