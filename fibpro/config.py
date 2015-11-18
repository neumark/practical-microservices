from fibpro.util import load_config, dict_map_string
import os
import sys

APPROOT= os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(APPROOT, "etc", "config.json")

for key, value in dict_map_string(
        load_config(CONFIG_FILE),
        lambda x: x.format(APPROOT=APPROOT)).iteritems():
    setattr(sys.modules[__name__], key, value)
