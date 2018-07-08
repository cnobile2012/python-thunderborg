#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mborg/mborg_joy.py
#
"""
Joystick Control of MonsterBorg
-------------------------------

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
import sys
import time
import logging
import pygame
import six

from tborg import ConfigLogger, ThunderBorg, ThunderBorgException

from .controller import PYGameController


class JoyStickControl(PYGameController):
    """
    This class allows control of the MonsterBorg by a PS3/4 controller.
    """
    _LOG_PATH = 'logs'
    _LOG_FILE = 'mborg_joy.log'
    _BASE_LOGGER_NAME = 'examples'
    _LOGGER_NAME = 'examples.mborg-joy'
    _CTRL_LOGGER_NAME = 'examples.controller'
    _TBORG_LOGGER_NAME = 'examples.tborg'
    _VOLTAGE_IN = 1.2 * 10
    _VOLTAGE_OUT = 12.0 * 0.95
    _PROCESS_INTERVAL = 0.00
    _MAX_POWER = (1.0 if _VOLTAGE_OUT > _VOLTAGE_IN
                  else _VOLTAGE_OUT / float(_VOLTAGE_IN))
    _ROTATE_TURN_SPEED = 0.5

    def __init__(self,
                 bus_num=ThunderBorg.DEFAULT_BUS_NUM,
                 address=ThunderBorg.DEFAULT_I2C_ADDRESS,
                 log_level=logging.INFO):
        cl = ConfigLogger(log_path=self._LOG_PATH)
        cl.config(logger_name=self._BASE_LOGGER_NAME,
                  filename=self._LOG_FILE,
                  level=logging.DEBUG)
        self._tb = ThunderBorg(bus_num=bus_num,
                               address=address,
                               logger_name=self._TBORG_LOGGER_NAME,
                               log_level=log_level)
        self._log = logging.getLogger(self._LOGGER_NAME)
        super(JoyStickControl, self).__init__(
            logger_name=self._CTRL_LOGGER_NAME, log_level=logging.DEBUG)

    def run(self):
        # Turn on failsafe.
        ## self._tb.set_comms_failsafe(True)
        ## assert self._tb.get_comms_failsafe() == True, (
        ##     "The failsafe mode could not be turned on."
        ##     )
        self._tb.set_comms_failsafe(False)

        # Log and init
        self.log_battery_monitoring()
        self.init_mborg()
        self.listen()

    def log_battery_monitoring(self):
        level_min, level_max = self._tb.get_battery_monitoring_limits()
        current_level = self._tb.get_battery_voltage()
        mid_level = (level_min + level_max) / 2
        buf = six.StringIO()
        buf.write("\nBattery Monitoring Settings\n")
        buf.write("---------------------------\n")
        buf.write("Minimum (red)    {:02.2f} V\n".format(level_min))
        buf.write("Middle  (yellow) {:02.2f} V\n".format(mid_level))
        buf.write("Maximum (green)  {:02.2f} V\n".format(level_max))
        buf.write("Current Voltage  {:02.2f} V\n".format(current_level))
        self._log.info(buf.getvalue())
        buf.close()

    def init_mborg(self):
        self._tb.halt_motors()
        self._tb.set_led_battery_state(False)
        self._tb.set_both_leds(0, 0, 1) # Set to blue
        self.init_controller()
        self.event_wait_time = self._PROCESS_INTERVAL

        if not self.is_ctrl_init:
            selg._log.warn("Could not initialize ")
            self._tb.set_comms_failsafe(False)
            self._tb.set_both_leds(0, 0, 0) # Set LEDs off
            sys.exit()

        self.set_misc()
        self._tb.set_led_battery_state(True)
        self._led_battery_mode = True
        self._both = 0.0
        self._up_down = 0.0
        self._log.debug("Finished mborg_joy initialization.")

    def process_event(self):
        """
        Process the current events (overrides the base class method).
        """
        if self.axis_up_down_invert:
            self._up_down = -self.axis_data.get(self.LF_UD)
        else:
            self._up_down = self.axis_data.get(self.LF_UD)

        if self.axis_left_right_invert:
            self._left_right = -self.axis_data.get(self.RT_LR)
        else:
            self._left_right = self.axis_data.get(self.RT_LR)

        # Steering speeds
        if self.button_data.get(self.rotate_turn_button):
            self._left_right *= self.rotate_turn_speed

        motor_one = -self._up_down
        motor_two = -self._up_down

        if self._left_right > 0.05:
            motor_one *= 1.0 - (2.0 * self._left_right)
        elif self._left_right < -0.05:
            motor_two *= 1.0 + (2.0 * self._left_right)

        # Drive slow button press
        if self.button_data.get(self.drive_slow_button):
            motor_one *= self.drive_slow_speed
            motor_two *= self.drive_slow_speed

        try:
            self._tb.set_motor_one(motor_one * self._MAX_POWER)
            self._tb.set_motor_two(motor_two * self._MAX_POWER)

            # Set LEDs to purple to indicate motor faults.
            if (self._tb.get_drive_fault_one()
                or self._tb.get_drive_fault_two()):
                if self._led_battery_mode:
                    self._tb.set_led_battery_state(False)
                    self._tb.set_both_leds(1, 0, 1) # Set to purple
                    self._led_battery_mode = False
                elif not self._led_battery_mode:
                    self._tb.set_led_battery_state(True)
                    self._led_battery_mode = True
        except (KeyboardInterrupt, ThunderBorgException) as e:
            self._log.warn("Exiting event processing, %s", e)
            raise e

    def set_misc(self, **kwargs):
        """
        Set some miscellaneous value.

        :param axis_invert_ud: If set to `True` the up/down control is
                               inverted. Default is `False`. Can be used
                               if the robot flips over.
        :type axis_invert_ud: bool
        :param axis_invert_lr: If set to `True` the left/right control is
                               inverted. Default is `False`. Can be used
                               if the robot flips over.
        :type axis_invert_lr: bool
        :param rotate_turn_but: Choose the button for rotation. The
                                default is R1 (5).
        :type rotate_turn_but: int
        :param rotate_turn_spd: Choose the speed for rotation. The
                                default is 0.5.
        :type rotate_turn_spd: float
        :param slow_but: Choose the button for driving slow. The default
                         is R2 (6).
        :type slow_but: int
        :param slow_spd: Choose the speed to decrease to when the
                         drive-slow button is held.
        :type slow_spd: bool
        """
        tmp_kwargs = kwargs.copy()
        axis_invert_ud = tmp_kwargs.pop('axis_invert_ud', False)
        axis_invert_lr = tmp_kwargs.pop('axis_invert_lr', False)
        rotate_turn_but = tmp_kwargs.pop('rotate_turn_but', self.R1)
        rotate_turn_spd = tmp_kwargs.pop('rotate_turn_spd',
                                         self._ROTATE_TURN_SPEED)
        slow_but = tmp_kwargs.pop('slow_but', self.R2)
        slow_spd = tmp_kwargs.pop('slow_spd', self._ROTATE_TURN_SPEED)
        assert not kwargs, "Invalid arguments found: {}".format(kwargs)
        # If the robot flips over. These are set on the base controller
        # class.
        self.axis_up_down_invert = axis_invert_ud
        self.axis_left_right_invert = axis_invert_lr
        # Change the rotate button and speed.
        self.rotate_turn_button = rotate_turn_but
        self.rotate_turn_speed = rotate_turn_spd
        self.drive_slow_button = slow_but
        self.drive_slow_speed = slow_spd


#if __name__ == '__main__':
#    JoyStickControl().run()
#    sys.exit()
