#!/usr/bin/env python

import logging
import sys

from tborg.examples.mborg_approxeng import JoyStickControl
#from tborg.examples.mborg_joy import JoyStickControl

jsc = JoyStickControl(log_level=logging.DEBUG)
jsc.run()
sys.exit()
