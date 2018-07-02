#!/usr/bin/env python

import logging
import sys

from tborg.examples.mborg_joy import JoyStickControl

jtc = JoyStickControl(log_level=logging.DEBUG)
jtc.run()
sys.exit()
