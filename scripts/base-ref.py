#!/usr/bin/env python3
import sys
from image_lib import load_base

config = load_base(sys.argv[1])
print(config["image"] + "@" + config["digest"])
