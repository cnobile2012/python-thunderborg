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
    _TBORG_LOGGER_NAME = 'examples.tborg'
    _PIDFILE = os.path.join(RUN_PATH, 'mborg_approxeng.pid')
    _VOLTAGE_IN = 12 # 1.2 volt cells * 10
    _VOLTAGE_OUT = 12.0 * 0.95
    _MAX_VOLTAGE_MULT = 1.145
    _ROTATE_TURN_SPEED = 0.5
    _SLOW_SPEED = 0.5

    def __init__(self, bus_num=ThunderBorg.DEFAULT_BUS_NUM,
                 address=ThunderBorg.DEFAULT_I2C_ADDRESS, borg=True,
                 log_level=logging.INFO, voltage_in=_VOLTAGE_IN, debug=False):
        self._borg = borg
        self.voltage_in = float(voltage_in)
        log_level = logging.DEBUG if debug else log_level
        cl = ConfigLogger()
        cl.config(logger_name=self._BASE_LOGGER_NAME,
                  file_path=self._LOG_PATH,
                  level=log_level)
        self._log = logging.getLogger(self._LOGGER_NAME)
        super(JoyStickControl, self).__init__(
            self._PIDFILE, logger_name=self._LOGGER_NAME)
        self._log.info("Initial arguments: bus_num: %s, address: %s, "
                       "borg: %s, log_level: %s, voltage_in: %s, debug: %s",
                       bus_num, address, borg, log_level, voltage_in, debug)

        if self._borg:
            self._tb = ThunderBorg(bus_num=bus_num,
                                   address=address,
                                   logger_name=self._TBORG_LOGGER_NAME,
                                   log_level=log_level)

            if math.isclose(self.voltage_in, 0.0):
                self.voltage_in = self._tb.get_battery_voltage()

            self._log.info("Voltage in: %s, max power: %s",
                           self.voltage_in, self.max_power)
            self.set_battery_limits()

        # Set defaults
        self.__quit = False
        self.fwd_rev_invert = False
        self.turn_invert = False
        # Longer than 10 secs will never be recognized because the
        # controller itself will disconnect before that.
        self.quit_hold_time = 9.0

    @property
    def max_power(self):
        return (1.0 if self._VOLTAGE_OUT > self.voltage_in
                else self._VOLTAGE_OUT / self.voltage_in)

    def set_battery_limits(self):
        max_level = self.voltage_in * self._MAX_VOLTAGE_MULT

        if 7.0 <= self.voltage_in < 12: # 9 volt battery
            min_level = 7.5
        elif 12 <= self.voltage_in < 13.6: # 10 NIMH 1.2 volt batteries
            min_level = 9.5
        elif 13.6 <= self.voltage_in < 17.6: # 4 LiIon 3.6 volt batteries
            min_level = 12.0
        else:
            min_level = self.voltage_in
            self._log.error("Could not determine battery type.")

        self._tb.set_battery_monitoring_limits(min_level, max_level)

    def run(self):
        """
        Start the controller listening process.
        """
        if self._borg:
            # Turn on failsafe.
            self._tb.set_comms_failsafe(True)

            if self._tb.get_comms_failsafe():
                # Log and init
                self.log_battery_monitoring()
                self.init_mborg()
            else:
                self._log.error("The failsafe mode could not be turned on.")
                self.quit = True

        try:
            self.listen()
        except (KeyboardInterrupt, ThunderBorgException) as e:
            self._log.warn("Exiting event processing, %s", e)
        finally:
            self._tb.halt_motors()
            self._tb.set_comms_failsafe(False)
            self._tb.set_led_battery_state(False)
            self._tb.set_both_leds(0, 0, 0) # Set LEDs off
            self._log.info("Exiting")

            if self.quit: # Only shutdown if asked.
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
        self._tb.set_led_battery_state(False)
        self._tb.set_both_leds(0, 0, 1) # No joystick yet.
        self._log.debug("Battery LED state: %s, LED color one: %s, two: %s ",
                        self._tb.get_led_battery_state(),
                        self._tb.get_led_one(), self._tb.get_led_two())

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
    def fwd_rev_invert(self):
        return self.__fwd_rev_invert

    @fwd_rev_invert.setter
    def fwd_rev_invert(self, value):
        self.__fwd_rev_invert = value

    @property
    def turn_invert(self):
        return self.__turn_invert

    @turn_invert.setter
    def turn_invert(self, value):
        self.__turn_invert = value

    def listen(self):
        _mode = 0 # For now just set to 0
        motor_one = motor_two = 0

        while not self.quit:
            try:
                with ControllerResource() as joystick:
                    while joystick.connected and not self.quit:
                        if not self._tb.get_led_battery_state():
                            self._tb.set_led_battery_state(True)

                        ## Set key presses
                        kp_map = self._check_presses(joystick)
                        # Set the mode.
                        _mode = kp_map['mode']


                        # Set the quit hold time.
                        quit_hold_time = kp_map['quit_hold_time']

                        if (not self.quit and self.quit_hold_time != 0
                            and self.quit_hold_time <= math.floor(
                                quit_hold_time)):
                            self.quit = True

                        # Set turning mode
                        turning_mode = kp_map['turning_mode']
                        # Set slow speed
                        slow_speed = kp_map['slow_speed']

                        ## Set ly and rx axes
                        motor_one, motor_two, x = self._process_motion(
                            joystick, 'ly', 'rx')

                        # Set the drive slow speed.
                        x *= turning_mode

                        if x > 0.05:
                            motor_one *= 1.0 - (2.0 * x)
                        elif x < -0.05:
                            motor_two *= 1.0 + (2.0 * x)

                        motor_one *= slow_speed
                        motor_two *= slow_speed

                        if self._borg:
                            self._tb.set_motor_one(motor_one * self.max_power)
                            self._tb.set_motor_two(motor_two * self.max_power)

                            # Set LEDs to purple to indicate motor faults.
                            if ((self._tb.get_drive_fault_one()
                                 or self._tb.get_drive_fault_two())
                                and self._tb.get_led_battery_state()):
                                self._tb.set_led_battery_state(False)
                                self._tb.set_both_leds(1, 0, 1) # purple
                        else:
                            time.sleep(0.25)
            except IOError:
                self._tb.set_both_leds(0, 0, 1) # Set to blue
                self._log.debug("Waiting for controller")
                time.sleep(2.0)

    def _process_motion(self, joystick, fr, tn):
        ## Set forward/reverse and turning axes
        axis_map = self._check_axes(joystick)
        # Set left Y or pitch axis
        fwd_rev = axis_map[fr]
        # Set right X axis or roll
        turn = axis_map[tn]

        # Invert the forward/reverse axis to match motor.
        if self.fwd_rev_invert:
            motor_one = motor_two = -fwd_rev
        else:
            motor_one = motor_two = fwd_rev

        # Invert the turning axis to match motor.
        if self.turn_invert:
            x = -turn
        else:
            x = turn

        return motor_one, motor_two, x

    def _check_presses(self, joystick):
        kp_map = {
            'mode': False,
            'quit_hold_time': 0.0,
            'slow_speed': 1,
            'turning_mode': 1,
            }
        joystick.check_presses()

        for button_name in joystick.buttons.names:
            hold_time = joystick[button_name]

            if hold_time is not None:
                if button_name == 'home':
                    # Hold time for quit
                    kp_map['quit_hold_time'] = hold_time

                if button_name == 'start':
                    # Change mode switch
                    kp_map['mode'] = True

                if button_name == 'r1':
                    # Two wheel turning
                    kp_map['turning_mode'] = self._ROTATE_TURN_SPEED

                if button_name == 'l1':
                    # Drive slow button press
                    kp_map['slow_speed'] = self._SLOW_SPEED

        return kp_map

    def _check_axes(self, joystick):
        axis_map = {
            'ly': 0.0,
            'rx': 0.0,
            'pitch': 0.0,
            'roll': 0.0
            }

        for axis_name in joystick.axes.names:
            axis_value = joystick[axis_name]
            self._log.debug("%s: %s", axis_name, axis_value)

            if axis_name == 'ly':
                axis_map[axis_name] = float(axis_value)
            elif axis_name == 'rx':
                axis_map[axis_name] = float(axis_value)
            elif axis_name == 'pitch':
                axis_map[axis_name] = float(axis_value)
            elif axis_name == 'roll':
                axis_map[axis_name] = float(axis_value)

        return axis_map


if __name__ == '__main__': # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description=("JoyStick Control Using Approxeng"))
    parser.add_argument(
        '-b', '--borg', action='store_false', default=True, dest='borg',
        help="If present the ThunderBorg code is not run.")
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, dest='debug',
        help="Run in debug mode (no thunderborg code is run).")
    parser.add_argument(
        '-v', '--voltage-in', default=12, dest='voltage_in',
        help="The total voltage from the battery source, defaults to 12.")
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

    jsc = JoyStickControl(voltage_in=options.voltage_in,
                          borg=options.borg,
                          debug=options.debug)
    getattr(jsc, arg)()
