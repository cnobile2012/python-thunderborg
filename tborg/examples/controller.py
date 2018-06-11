# -*- coding: utf-8 -*-
#
# mborg/controller.py
#
"""
Joystick Controllers

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

import pygame

"""
https://gist.github.com/claymcleod/028386b860b75e4f5472
https://github.com/hthiery/python-ps4
https://approxeng.github.io/approxeng.input/index.html
https://stackoverflow.com/questions/46557583/how-to-identify-which-button-is-being-pressed-on-ps4-controller-using-pygame
http://blog.mclemon.io/python-using-a-dualshock-4-with-pygame
"""

class Controller(object):

    def __init__(self):
        """
        Initialize the JoyStick.
        """
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        self.axis_data = {
            axis: 0.0 for axis in range(self.controller.get_numaxes())
            }
        self.ball_data = {
            ball: 0.0 for ball in range(self.controller.get_numballs())
            }
        self.button_data = {
            but: False for but in range(self.controller.get_numbuttons())
            }
        self.hat_data = {
            hat: (0, 0) for hat in range(self.controller.get_numhats())
            }
        # Buttons
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

        # Axis
        self.LF_LR = 0
        self.LF_UP = 1
        self.RT_LR = 2
        self.RT_UD = 3 if not self.is_ps4() else 5

        # Create HAT variables.
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

    __METHODS = {
        pygame.JOYAXISMOTION: __set_axis,
        pygame.JOYBALLMOTION: __set_ball,
        pygame.JOYBUTTONDOWN: __set_button_down,
        pygame.JOYBUTTONUP: __set_button_up,
        pygame.JOYHATMOTION: __set_hat
        }

    def listen(self, done=False):
        """
        Listen to the controller events.
        """
        while not done:
            try:
                for event in pygame.event.get():
                    #print(event.joy) # We only use joystick 0 (zero).
                    self.__METHODS[event.type](self, event)
                    self.process_event(done)
            except KeyboardInterrupt:
                break

    def process_event(self, done):
        """
        Process the current events.
        """
        raise NotImplementedError(
            "Programming error: must implement {}".format(
                process_event.__name__))

    def is_ps4(self):
        return len(self.axis_data) == 6
