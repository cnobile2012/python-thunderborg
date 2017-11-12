#
# tborg/tests/test_tborg.py
#
from __future__ import absolute_import

import os
import logging
import unittest

from tborg import ConfigLogger, ThunderBorgException, ThunderBorg

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', '..', 'logs'))
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH, 0o0775)


class BaseTest(unittest.TestCase):

    def __init__(self, name, filename=None):
        super(BaseTest, self).__init__(name)
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
        # Set a new address
        orig_addr = ThunderBorg.find_board()
        orig_addr = orig_addr[0] if orig_addr else None
        new_addr = 0x70
        ThunderBorg.set_i2c_address(new_addr)
        found = ThunderBorg.find_board()
        found = found[0] if found else None
        msg = "Found address '{}', should be '{}'.".format()
        self.assertEqual(found, new_addr, msg)
        # Reset the original address
        ThunderBorg.set_i2c_address(orig_addr)
        found = ThunderBorg.find_board()
        found = found[0] if found else None
        msg = "Found address '{}', should be '{}'.".format()
        self.assertEqual(found, orig_addr, msg)


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




