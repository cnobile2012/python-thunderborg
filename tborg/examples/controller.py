# -*- coding: utf-8 -*-
#
# mborg/controller.py
#
"""
Joystick Controllers
--------------------

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
import time

import pygame

from tborg import ConfigLogger


class PYGameController(object):
    """
    Initializes the attached controller.
    """
    _LOG_PATH = 'logs'
    _LOG_FILE = 'controller.log'
    _LOGGER_NAME = 'controller'
    _SLEEP_TIME = 0.1

    def __init__(self, log_level=logging.INFO):
        """
        Initialize logging 
        """
        cl = ConfigLogger(log_path=self._LOG_PATH)
        cl.config(logger_name=self._LOGGER_NAME,
                  filename=self._LOG_FILE,
                  level=logging.DEBUG)
        self._log = logging(self._LOGGER_NAME)
        self.__controller_initialized = False

    @property
    def is_ctrl_init(self):
        return self.__controller_initialized

    def init_ctrl(self):
        """
        Wait until the controller is connected then initialize pygame.
        """
        pygame.init()

        while True:
            try:
                pygame.joystick.init()
            except pygame.error as e:
                pygame.joystick.quit()
                self._log.error("PYGame error: %s", e)
                time.sleep(self._SLEEP_TIME)
            except KeyboardInterrupt:
                self._log.warn("User aborted with CTRL C.")
            else:
                if pygame.joystick.get_count() < 1:
                    pygame.joystick.quit()
                    time.sleep(self._SLEEP_TIME)
                else:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self._initialize_variables()
                    self._log.info("Found joystick.")
                    self.__controller_initialized = True
                    break

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
        self.rotate_turn_button = 
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
        self.LF_UP = 1
        self.RT_LR = 2
        self.RT_UD = 5 if self.is_ps4() else 3

        # Create HAT variables. Hat Event Types (HAT0, HAT1, ...)
        for i in range(len(self.hat_data)):
            exec('self.HAT{0} = {0}'.format(i))

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
                    self.process_event(done)
            except KeyboardInterrupt:
                self.set_quit()

    def process_event(self):
        """
        Process the current events.
        """
        raise NotImplementedError(
            "Programming error: must implement {}".format(
                process_event.__name__))

    def is_ps4(self):
        """
        Is a PS4 controller attached?

        .. note::
            The current way this is determined may not be reliable, but
            as of now, it's the best way I can find.
        """
        return len(self.axis_data) == 6
