# -*- coding: utf-8 -*-
#
# mborg/examples/mborg_approxeng.py
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

import logging
import math
import os
import six
import sys
import time

from approxeng.input.selectbinder import ControllerResource

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from tborg import (
    create_working_dir, ConfigLogger, ThunderBorg, ThunderBorgException)
from tborg.utils.daemon import Daemon

create_working_dir()

from tborg import BORG_CUBE, LOG_PATH, RUN_PATH


class JoyStickControl(Daemon):
    """
    The ApproxEng.input library is used to control the Thunder Borg.
    """
    _LOG_PATH = os.path.join(LOG_PATH, 'mborg_approxeng.log')
    _BASE_LOGGER_NAME = 'examples'
    _LOGGER_NAME = 'examples.mborg-approxeng'
    _CTRL_LOGGER_NAME = 'examples.controller'
    _TBORG_LOGGER_NAME = 'examples.tborg'
    _PIDFILE = os.path.join(RUN_PATH, 'mborg_approxeng.pid')
    _VOLTAGE_IN = 1.2 * 10
    _VOLTAGE_OUT = 12.0 * 0.95
    _MAX_POWER = (1.0 if _VOLTAGE_OUT > _VOLTAGE_IN
                  else _VOLTAGE_OUT / float(_VOLTAGE_IN))
    _ROTATE_TURN_SPEED = 0.5
    _SLOW_SPEED = 0.5

    def __init__(self, bus_num=ThunderBorg.DEFAULT_BUS_NUM,
                 address=ThunderBorg.DEFAULT_I2C_ADDRESS,
                 log_level=logging.INFO, debug=False):
        self._debug = debug
        cl = ConfigLogger()
        cl.config(logger_name=self._BASE_LOGGER_NAME,
                  file_path=self._LOG_PATH,
                  level=log_level)
        super(JoyStickControl, self).__init__(
            self._PIDFILE, logger_name=self._LOGGER_NAME)

        if not self._debug:
            self._tb = ThunderBorg(bus_num=bus_num,
                                   address=address,
                                   logger_name=self._TBORG_LOGGER_NAME,
                                   log_level=log_level)

        self._log = logging.getLogger(self._LOGGER_NAME)
        # Set defaults
        self.__quit = False
        self.__axis_x_invert = False
        self.__axis_y_invert = False
        # Longer than 10 secs will never be recognized because the
        # controller itself will disconnect before that.
        self.__quit_hold_time = 9.0

    def run(self):
        """
        Start the controller listening process.
        """
        if not self._debug:
            # Turn on failsafe.
            self._tb.set_comms_failsafe(True)
            assert self._tb.get_comms_failsafe() == True, (
                "The failsafe mode could not be turned on."
                )
            # Log and init
            self.log_battery_monitoring()
            self.init_mborg()

        try:
            self.listen()
        except (KeyboardInterrupt, ThunderBorgException) as e:
            self._log.warn("Exiting event processing, %s", e)
            raise e
        finally:
            self._tb.set_comms_failsafe(False)
            self._tb.set_both_leds(0, 0, 0) # Set LEDs off

            if self._quit: # Only shutdown if asked.
                self._log.warn("Shutting down the Raspberry PI.")
                os.system("sudo poweroff")

            sys.exit()

    def log_battery_monitoring(self):
        """
        Dump to the log the initial battery values.
        """
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
        """
        Initialize motor controller.
        """
        self._tb.halt_motors()
        #self._tb.set_led_battery_state(False)
        self._tb.set_both_leds(0, 0, 1) # Set to blue
        self._tb.set_led_battery_state(True)
        self._led_battery_mode = True

    @property
    def quit(self):
        return self.__quit

    @quit.setter
    def quit(self, value):
        self.__quit = value

    @property
    def quit_hold_time(self):
        return self.__quit_hold_time

    @quit_hold_time.setter
    def quit_hold_time(self, value):
        self.__quit_hold_time = value

    @property
    def axis_x_invert(self):
        return self.__axis_x_invert

    @axis_x_invert.setter
    def axis_x_invert(self, value):
        self.__axis_x_invert = value

    @property
    def axis_y_invert(self):
        return self.__axis_y_invert

    @axis_y_invert.setter
    def axis_y_invert(self, value):
        self.__axis_y_invert = value

    def listen(self):
        _mode = 0 # For now just set to 0
        _quit = False
        motor_one = motor_two = 0

        while not self.quit:
            try:
                with ControllerResource() as joystick:
                    while joystick.connected and not self.quit:
                        ## Set key presses
                        kp_map = self._check_presses(joystick)
                        # Set mode (Does nothing now).
                        _mode = kp_map['mode']
                        # Set the quit hold time.
                        quit_hold_time = kp_map['quit_hold_time']

                        if (not self.quit and self.quit_hold_time != 0
                            and self.quit_hold_time <= math.floor(
                                quit_hold_time)):
                            self.quit = True

                        # Set fast rotate
                        fast_rotate = kp_map['fast_rotate']
                        # Set slow speed
                        slow_speed = kp_map['slow_speed']

                        ## Set the axes
                        axis_map = self._check_axes(joystick)
                        # Set left Y axis
                        left_y = axis_map['left_y']

                        # Invert the controller Y axis to match the motor
                        # fwd/rev.
                        if self.axis_y_invert:
                            motor_one = motor_two = -left_y
                        else:
                            motor_one = motor_two = left_y

                        # Set right X axis
                        right_x = axis_map['right_x']

                        if self.axis_x_invert:
                            x = -right_x
                        else:
                            x = right_x

                        # Set the drive slow speed.
                        x *= fast_rotate

                        if x > 0.05:
                            motor_one *= 1.0 - (2.0 * x)
                        elif x < -0.05:
                            motor_two *= 1.0 + (2.0 * x)

                        motor_one *= slow_speed
                        motor_two *= slow_speed

                        if not self._debug:
                            self._tb.set_motor_one(motor_one * self._MAX_POWER)
                            self._tb.set_motor_two(motor_two * self._MAX_POWER)

                            # Set LEDs to purple to indicate motor faults.
                            if (self._tb.get_drive_fault_one()
                                or self._tb.get_drive_fault_two()):
                                if self._led_battery_mode:
                                    self._tb.set_led_battery_state(False)
                                    self._tb.set_both_leds(1, 0, 1) # purple
                                    self._led_battery_mode = False
                                else:
                                    self._tb.set_led_battery_state(True)
                                    self._led_battery_mode = True
                        else:
                            #print(("motor_one: {}, motor_two: {}, "
                            #       "quit_hold_time: {}").format(
                            #          motor_one, motor_two, quit_hold_time))
                            #print("quit: {}".format(self.quit))
                            time.sleep(0.25)
            except IOError:
                #self._log.warning("Waiting for controller")
                time.sleep(1.0)

    def _check_presses(self, joystick):
        kp_map = {
            'mode': False,
            'quit_hold_time': 0.0,
            'slow_speed': 1,
            'fast_rotate': 1,
            }
        joystick.check_presses()

        if joystick.has_presses:
            last_presses = joystick.presses

            if last_presses is not None:
                for button_name in last_presses:
                    if button_name == 'start':
                        # Change mode switch
                        kp_map['mode'] = True
                    elif button_name == 'r1':
                        # Fast rotate press
                        kp_map['fast_rotate'] = self._ROTATE_TURN_SPEED
                    elif button_name == 'l1':
                        # Drive slow button press
                        kp_map['slow_speed'] = self._SLOW_SPEED

        for button_name in joystick.buttons.names:
            if button_name == 'home':
                # Hold time for quit
                hold_time = joystick[button_name]

                if hold_time is not None:
                    kp_map['quit_hold_time'] = hold_time

        return kp_map

    def _check_axes(self, joystick):
        axis_map = {
            'left_y': 0.0,
            'right_x': 0.0,
            }

        for axis_name in joystick.axes.names:
            axis_value = joystick[axis_name]

            if axis_name == 'ly':
                axis_map['left_y'] = float(axis_value)
            elif axis_name == 'rx':
                axis_map['right_x'] = float(axis_value)

        return axis_map


if __name__ == '__main__': # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description=("JoyStick Control Using Approxeng"))
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, dest='debug',
        help="Run in debug mode (no thunderborg code is run).")
    parser.add_argument(
        '-s', '--start', action='store_true', default=False, dest='start',
        help="Start the daemon.")
    parser.add_argument(
        '-r', '--restart', action='store_true', default=False, dest='restart',
        help="Restart the daemon.")
    parser.add_argument(
        '-S', '--stop', action='store_true', default=False, dest='stop',
        help="Stop the daemon.")
    options = parser.parse_args()
    arg_value = (options.start ^ options.restart ^ options.stop)

    if not arg_value and arg_value is not False:
        print("Can only set one of 'start', 'restart' or 'stop'.")
        sys.exit(-1)

    if options.start:
        arg = 'start'
    elif options.restart:
        arg = 'restart'
    elif options.stop:
        arg = 'stop'
    else:
        arg = 'start'

    jsc = JoyStickControl(debug=options.debug)
    getattr(jsc, arg)()
