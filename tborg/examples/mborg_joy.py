# -*- coding: utf-8 -*-
#
# mborg/mborg_joy.py
#
"""
Joy Stick Control of MonsterBorg

by Carl J. Nobile

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import absolute_import

__docformat__ = "restructuredtext en"

import os
#import sys
import time
import logging
import pygame

from tborg import ConfigLogger, ThunderBorg

from .controller import Controller


class JoyStickControl(Controller):
    """
    This class allows control of the MonsterBorg by a PS4 controller.
    """
    _LOG_PATH = 'logs'
    _LOG_FILE = 'mborg_joy.log'
    _LOGGER_NAME = 'mborg-joy'

    def __init__(self,
                 bus_num=ThunderBorg.DEFAULT_BUS_NUM,
                 address=ThunderBorg.DEFAULT_I2C_ADDRESS,
                 log_level=logging.INFO):
        super(JoyStickControl, self).__init__()
        cl = ConfigLogger(log_path=self._LOG_PATH)
        cl.config(logger_name=self._LOGGER_NAME,
                  filename=self._LOG_FILE,
                  level=logging.DEBUG)
        self._tb = ThunderBorg(bus_num=bus_num,
                               address=address,
                               logger_name=self._LOGGER_NAME,
                               log_level=log_level)
        # Turn on failsafe.
        self._tb.set_comms_failsafe(True)
        assert self._tb.get_comms_failsafe() == True, (
            "The failsafe mode could not be turned on."
            )

    def process_event(self, done):
        """
        Process the current events.
        """
        print(self.button_data)
        print(self.axis_data)
        print(self.hat_data)



