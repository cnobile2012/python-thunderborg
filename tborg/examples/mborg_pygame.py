# -*- coding: utf-8 -*-
#
# mborg/examples/mborg_pygame.py
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from tborg import(
    create_working_dir, ConfigLogger, ThunderBorg, ThunderBorgException)
from tborg.utils.daemon import Daemon

create_working_dir()

from tborg import BORG_CUBE, LOG_PATH, RUN_PATH


class PYGameController(object):
    """
    Initializes the attached controller.
    """
    _DEFAULT_CTRL_WAIT = 0.1
    _DEFAULT_EVENT_WAIT = 0.0

    def __init__(self, logger_name=''):
        """
        Initialize logging and sets the two wait times to a reasonable
        default.
        """
        self._log = logging.getLogger(logger_name)
        self.__controller_initialized = False
        self.__ctrl_wait_time = 0
        self.ctrl_wait_time = self._DEFAULT_CTRL_WAIT
        self.event_wait_time = self._DEFAULT_EVENT_WAIT

    @property
    def ctrl_wait_time(self):
        """
        Property that gets or sets the controller wait time. This wait
        time is used when looping during the controller detection period.

        :param sleep: The period of time to sleep between checks. Defaults
                      to 0.1 seconds.
        :type sleep: float
        """
        return self.__ctrl_wait_time

    @ctrl_wait_time.setter
    def ctrl_wait_time(self, sleep):
        self.__ctrl_wait_time = sleep

    @property
    def event_wait_time(self):
        """
        Property that gets or sets the event wait time. This wait time is
        used when looping during the event processing period.

        :param sleep: The period of time to sleep between event
                      processing. Defaults to 0.0 seconds.
        :type sleep: float
        """
        return self.__event_wait_time

    @event_wait_time.setter
    def event_wait_time(self, sleep):
        self.__event_wait_time = sleep

    @property
    def is_ctrl_init(self):
        """
        A property that returns `True` or `False` if the controller is
        initialized.
        """
        return self.__controller_initialized

    def init_controller(self):
        """
        Wait until the controller is connected then initialize pygame.
        """
        pygame.init()

        while True:
            try:
                pygame.joystick.init()
            except pygame.error as e:
                self._log.error("PYGame error: %s", e)
                if self._quit_sleep(): break
            except KeyboardInterrupt:
                self._log.warn("User aborted with CTRL C.")
                break
            else:
                if pygame.joystick.get_count() < 1:
                    if self._quit_sleep(): break
                else:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self._initialize_variables()
                    self._log.info("Found controller.")
                    self.__controller_initialized = True
                    break

    def _quit_sleep(self):
        error = False

        try:
            pygame.joystick.quit()
            time.sleep(self.ctrl_wait_time)
        except KeyboardInterrupt:
            self._log.warn("User aborted with CTRL C.")
            error = True

        return error

    def _initialize_variables(self):
        self.axis_data = {
            axis: 0.0 for axis in range(self.joystick.get_numaxes())
            }
        self.ball_data = {
            ball: 0.0 for ball in range(self.joystick.get_numballs())
            }
        self.button_data = {
            but: False for but in range(self.joystick.get_numbuttons())
            }
        self.hat_data = {
            hat: (0, 0) for hat in range(self.joystick.get_numhats())
            }
        self.__quit = False
        # Buttons Event Types
        self.SQUARE = 0
        self.CROSS = 1
        self.CIRCLE = 2
        self.TRIANGLE = 3
        self.L1 = 4
        self.R1 = 5
        self.L2 = 6
        self.R2 = 7
        self.SHARE = 8
        self.OPTIONS = 9
        self.LJB = 10
        self.RJB = 11
        self.PSB = 12
        self.PADB = 13

        # Axis Event Types
        self.LF_LR = 0
        self.LF_UD = 1
        self.L2_VR = 2
        self.RT_LR = 3
        self.RT_UD = 4 # if self.is_ps4() else 3
        self.R2_VR = 5

        # Create HAT variables. Hat Event Types (HAT0, HAT1, ...)
        for i in range(len(self.hat_data)):
            setattr(self, 'HAT' + i, i)

    def __set_axis(self, event):
        self.axis_data[event.axis] = round(event.value, 3)

    def __set_ball(self, event):
        self.ball_data[event.ball] = event.rel

    def __set_button_down(self, event):
        self.button_data[event.button] = True

    def __set_button_up(self, event):
        self.button_data[event.button] = False

    def __set_hat(self, event):
        self.hat_data[event.hat] = event.value

    def set_quit(self, event=None):
        self.__quit = True

    __METHODS = {
        pygame.JOYAXISMOTION: __set_axis,
        pygame.JOYBALLMOTION: __set_ball,
        pygame.JOYBUTTONDOWN: __set_button_down,
        pygame.JOYBUTTONUP: __set_button_up,
        pygame.JOYHATMOTION: __set_hat,
        pygame.QUIT: set_quit
        }

    def listen(self):
        """
        Listen to controller events.
        """
        assert self.is_ctrl_init, ("The init_ctrl method must be called "
                                   "before the listen method.")

        while not self.__quit:
            try:
                for event in pygame.event.get():
                    #print(event.joy) # We only use joystick 0 (zero).
                    self.__METHODS[event.type](self, event)
                    self.process_event()
            except (KeyboardInterrupt, ThunderBorgException) as e:
                self._log.warn("Exiting pygame event loop, %s", e)
                self.set_quit()
            else:
                time.sleep(self.event_wait_time)

    def process_event(self):
        """
        Process the current events. This method needs to be overridden.
        """
        #print(self.axis_data)
        #print(self.ball_data)
        #print(self.button_data)
        #print(self.hat_data)

        raise NotImplementedError(
            "Programming error: must implement {}".format(
                process_event.__name__))

    def is_ps4(self):
        """
        Is a PS4 controller attached?

        .. note::
            The current way this is determined may not be reliable, but
            as of now, it's the best way I have find.
        """
        return len(self.axis_data) == 6


class JoyStickControl(PYGameController, Daemon):
    """
    This class allows control of the MonsterBorg by a PS3/4 controller.
    """
    _LOG_PATH = os.path.join(LOG_PATH, 'mborg_pygame.log')
    _BASE_LOGGER_NAME = 'examples'
    _LOGGER_NAME = 'examples.mborg-pygame'
    _CTRL_LOGGER_NAME = 'examples.controller'
    _TBORG_LOGGER_NAME = 'examples.tborg'
    _PIDFILE = os.path.join(RUN_PATH, 'mborg_approxeng.pid')
    _VOLTAGE_IN = 1.2 * 10
    _VOLTAGE_OUT = 12.0 * 0.95
    _PROCESS_INTERVAL = 0.00
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
                  file_path=self._LOG_FILE,
                  level=logging.DEBUG)

        if not self._debug:
            self._tb = ThunderBorg(bus_num=bus_num,
                                   address=address,
                                   logger_name=self._TBORG_LOGGER_NAME,
                                   log_level=log_level)

        self._log = logging.getLogger(self._LOGGER_NAME)
        PYGameController.__init__(self, logger_name=self._CTRL_LOGGER_NAME)
        Daemon.__init__(self, self._PIDFILE, logger_name=self._LOGGER_NAME)

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

        self.listen()

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
        Initialize the MonsterBorg joystick controller.
        """
        self._tb.halt_motors()
        self._tb.set_led_battery_state(False)
        self._tb.set_both_leds(0, 0, 1) # Set to blue
        self.init_controller()
        self.event_wait_time = self._PROCESS_INTERVAL

        if not self.is_ctrl_init:
            self._log.warn("Could not initialize ")
            self._tb.set_comms_failsafe(False)
            self._tb.set_both_leds(0, 0, 0) # Set LEDs off
            sys.exit()

        self.set_defaults()
        self._tb.set_led_battery_state(True)
        self._led_battery_mode = True
        self._log.debug("Finished mborg_joy initialization.")

    def process_event(self):
        """
        Process the current events (overrides the base class method).
        """
        # Invert the controller Y axis to match the motor fwd/rev.
        # If the Y axis needs to be inverted do that also.
        if self.axis_y_invert:
            motor_one = motor_two = self.axis_data.get(self.LF_Y)
        else:
            motor_one = motor_two = -self.axis_data.get(self.LF_Y)

        if self.axis_x_invert:
            x = -self.axis_data.get(self.RT_X)
        else:
            x = self.axis_data.get(self.RT_X)

        # Rotate turn button press
        if not self.button_data.get(self.rotate_turn_button):
            x *= self.rotate_turn_speed

        if x > 0.05:
            motor_one *= 1.0 - (2.0 * x)
        elif x < -0.05:
            motor_two *= 1.0 + (2.0 * x)

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

    def set_defaults(self, **kwargs):
        """
        Set some default values. This method can be set while running. For
        example if the robot flips over which could be determined with a
        sensor the axis invert values can be changed.

        :param axis_y_invert: If set to `True` the up/down control is
                              inverted. Default is `False`. Can be used
                              if the robot flips over.
        :type axis_y_invert: bool
        :param axis_x_invert: If set to `True` the left/right control is
                              inverted. Default is `False`. Can be used
                              if the robot flips over.
        :type axis_x_invert: bool
        :param rotate_turn_button: Choose the button for rotation. The
                                   default is R1 (5).
        :type rotate_turn_button: int
        :param rotate_turn_speed: Choose the speed for rotation. The
                                  default is 0.5.
        :type rotate_turn_speed: float
        :param drive_slow_button: Choose the button for driving slow. The
                                  default is R2 (6).
        :type drive_slow_but: int
        :param drive_slow_speed: Choose the speed to decrease to when the
                                 drive-slow button is held.
        :type drive_slow_speed: bool
        """
        tmp_kwargs = kwargs.copy()
        self.axis_y_invert = tmp_kwargs.pop('axis_y_invert', False)
        self.axis_x_invert = tmp_kwargs.pop('axis_x_invert', False)
        self.rotate_turn_button = tmp_kwargs.pop(
            'rotate_turn_button', self.R1)
        self.rotate_turn_speed = tmp_kwargs.pop(
            'rotate_turn_speed', self._ROTATE_TURN_SPEED)
        self.drive_slow_button = tmp_kwargs.pop(
            'drive_slow_button', self.L1)
        self.drive_slow_speed = tmp_kwargs.pop(
            'drive_slow_speed', self._SLOW_SPEED)
        assert not kwargs, "Invalid arguments found: {}".format(kwargs)


if __name__ == '__main__': # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description=("JoyStick Control Using PYGame"))
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
