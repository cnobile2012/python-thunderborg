#
# tborg/tests/test_tborg.py
#
from __future__ import absolute_import

import os
import unittest

from tborg import ConfigLogger, ThunderBorgException, ThunderBorg

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', '..', 'logs'))
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH, 0o0775)


class BaseTest(unittest.TestCase):

    def __init__(self, name, filename):
        super(TestClassMethods, self).__init__(name)
        cl = ConfigLogger(log_path=LOG_PATH)
        cl.config(logger_name='thunder-borg', filename=filename,
                  level=logging.DEBUG)


class TestClassMethods(BaseTest):
    _LOG_FILENAME = 'tb-class_method.log'

    def __init__(self, name):
        super(TestClassMethods, self).__init__(
            name, filename=self._LOG_FILENAME)

    def test_find_board(self):
        """
        Test that the ThunderBorg.find_board() method finds a board.
        """
        found = ThunderBorg.find_board()
        found = found[0] if found else None
        msg = "Found address '{}', should be address '{}'.".format(
            found, ThunderBorg._I2C_ID_THUNDERBORG)
        self.assertEqual(found, ThunderBorg._I2C_ID_THUNDERBORG, msg)

    def test_set_i2c_address(self):
        """
        Test that the ThunderBorg.set_i2c_address() can set a different
        address.
        """
        new_address = 0x70
        ThunderBorg.set_i2c_address(new_address)
        tb = ThunderBorg(log_level=logging.DEBUG)
        orig_led_state = tb.get_led_state()
        new_led_state = True if not orig_led_state else False
        tb.set_led_state(new_led_state)
        found_led_state = tb.get_led_state()
        msg = "Found LED state '{}', should be '{}'.".format(
            found_led_state, new_led_state)
        self.assertEqual(found_led_state, new_led_state, msg)
        tb.set_led_state(orig_led_state)
        found_led_state = tb.get_led_state()
        msg = "Found LED state '{}', should be '{}'.".format(
            found_led_state, orig_led_state)
        self.assertEqual(found_led_state, orig_led_state, msg)


class TestThunderBorg(BaseTest):
    _LOG_FILENAME = 'tb-instance.log'

    def __init__(self, name):
        super(TestThunderBorg, self).__init__(
            name, filename=self._LOG_FILENAME)

    def setUp(self):
        self._log.debug("Processing")
        self._tb = ThunderBorg()

    def tearDown(self):
        self._tb.halt_motors()
        self.close_streams()




