#
# tborg/tests/test_tborg.py
#
from __future__ import absolute_import

import os
import logging
import unittest
import time

try:
    from unittest.mock import patch
except:
    from mock import patch

from tborg import ConfigLogger, ThunderBorgException, ThunderBorg

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', '..', 'logs'))
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH, 0o0775)


#def isclose(a, b, rel_tol, abs_tol):
#    return abs(a-b) <= max( rel_tol * max(abs(a), abs(b)), abs_tol)


class BaseTest(unittest.TestCase):
    LOGGER_NAME = 'thunder-borg'

    def __init__(self, name, filename=None):
        super(BaseTest, self).__init__(name)
        cl = ConfigLogger(log_path=LOG_PATH)
        cl.config(logger_name=self.LOGGER_NAME, filename=filename,
                  level=logging.DEBUG)


class TestNoSetUp(BaseTest):
    _LOG_FILENAME = 'tb-no-setup-method.log'

    def __init__(self, name):
        super(TestNoSetUp, self).__init__(
            name, filename=self._LOG_FILENAME)

    @patch.object(ThunderBorg, '_DEFAULT_I2C_ADDRESS', 0x20)
    #@unittest.skip("Temporarily skipped")
    def test_find_address_with_invalid_default_address(self):
        """
        Test that an invalid default address will cause a board to be
        initialized if the `auto_set_addr` argument is `True`.
        """
        default_address = 0x15
        tb = ThunderBorg(logger_name=self.LOGGER_NAME,
                         log_level=logging.DEBUG,
                         auto_set_addr=True)
        boards = ThunderBorg.find_board()
        msg = "Boards found: {}".format(boards)
        self.assertEquals(tb._DEFAULT_I2C_ADDRESS, 0x20, msg)
        self.assertTrue(len(boards) > 0, msg)
        self.assertEqual(boards[0], default_address, msg)


class TestClassMethods(BaseTest):
    _LOG_FILENAME = 'tb-class-method.log'

    def __init__(self, name):
        super(TestClassMethods, self).__init__(
            name, filename=self._LOG_FILENAME)

    def tearDown(self):
        ThunderBorg.set_i2c_address(ThunderBorg._DEFAULT_I2C_ADDRESS)

    #@unittest.skip("Temporarily skipped")
    def test_find_board(self):
        """
        Test that the ThunderBorg.find_board() method finds a board.
        """
        found = ThunderBorg.find_board()
        found = found[0] if found else 0
        msg = "Found address '0x{:02X}', should be '0x{:02X}'.".format(
            found, ThunderBorg._DEFAULT_I2C_ADDRESS)
        self.assertEqual(found, ThunderBorg._DEFAULT_I2C_ADDRESS, msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_i2c_address_without_current_address(self):
        """
        Test that the ThunderBorg.set_i2c_address() can set a different
        address. Scans address range to find current address.
        """
        # Set a new address
        new_addr = 0x70
        ThunderBorg.set_i2c_address(new_addr)
        found = ThunderBorg.find_board()
        found = found[0] if found else 0
        msg = "Found address '0x{:02X}', should be '0x{:02X}'.".format(
            found, new_addr)
        self.assertEqual(found, new_addr, msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_i2c_address_with_current_address(self):
        """
        Test that the ThunderBorg.set_i2c_address() can set a different
        address. The current address is provided.
        """
        # Set a new address
        new_addr = 0x70
        cur_addr = ThunderBorg._DEFAULT_I2C_ADDRESS
        ThunderBorg.set_i2c_address(new_addr, cur_addr=cur_addr)
        found = ThunderBorg.find_board()
        found = found[0] if found else 0
        msg = "Found address '0x{:02X}', should be '0x{:02X}'.".format(
            found, new_addr)
        self.assertEqual(found, new_addr, msg)


class TestThunderBorg(BaseTest):
    _LOG_FILENAME = 'tb-instance.log'

    def __init__(self, name):
        super(TestThunderBorg, self).__init__(
            name, filename=self._LOG_FILENAME)

    def setUp(self):
        self._tb = ThunderBorg()

    def tearDown(self):
        self._tb.halt_motors()
        self._tb.set_comms_failsafe(False)
        self._tb.set_led_state(False)
        self._tb.set_led_one(0.0, 0.0, 0.0)
        self._tb.set_led_two(0.0, 0.0, 0.0)
        self._tb.close_streams()

    def validate_tuples(self, t0, t1):
        msg = "rgb0: {}, rgb1: {}"

        for x, y in zip(t0, t1):
            self.assertAlmostEqual(x, y, delta=0.01, msg=msg.format(x, y))

    #@unittest.skip("Temporarily skipped")
    def test_set_and_get_motor_one(self):
        """
        Test that motor one responds to commands.
        """
        # Test forward
        speed = 0.5
        self._tb.set_motor_one(speed)
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        # Test reverse
        speed = -0.5
        self._tb.set_motor_one(speed)
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_and_get_motor_two(self):
        """
        Test that motor two responds to commands.
        """
        # Test forward
        speed = 0.5
        self._tb.set_motor_two(speed)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        # Test reverse
        speed = -0.5
        self._tb.set_motor_two(speed)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_both_motors(self):
        """
        Test that motors one and two responds to commands.
        """
        # Test forward
        speed = 0.5
        self._tb.set_both_motors(speed)
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        # Test reverse
        speed = -0.5
        self._tb.set_both_motors(speed)
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)

    #@unittest.skip("Temporarily skipped")
    def test_halt_motors(self):
        """
        Test that halting the motors works properly.
        """
        # Start motors and check that the board says they are moving.
        speed = 0.5
        self._tb.set_both_motors(speed)
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        # Halt the motors.
        self._tb.halt_motors()
        # Check that the board says they are not moving.
        speed = 0.0
        rcvd_speed = self._tb.get_motor_one()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)
        rcvd_speed = self._tb.get_motor_two()
        msg = "Speed sent: {}, speed received: {}".format(speed, rcvd_speed)
        self.assertAlmostEqual(speed, rcvd_speed, delta=0.01, msg=msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_led_one(self):
        """
        Test that the RBG colors set are the same as the one's returned.
        """
        state = self._tb.get_led_state()
        msg = "Default state should be False: {}".format(state)
        self.assertFalse(state, msg)
        rgb_list = [(0, 0, 0), (1, 1, 1), (1.0, 0.5, 0.0), (0.2, 0.0, 0.2)]
        msg = "rgb: {}, ret_rgb: {}"

        for rgb in rgb_list:
            self._tb.set_led_one(*rgb)
            ret_rgb = self._tb.get_led_one()
            self.validate_tuples(ret_rgb, rgb)

    #@unittest.skip("Temporarily skipped")
    def test_set_led_two(self):
        """
        Test that the RBG colors set are the same as the one's returned.
        """
        state = self._tb.get_led_state()
        msg = "Default state should be False: {}".format(state)
        self.assertFalse(state, msg)
        rgb_list = [(0, 0, 0), (1, 1, 1), (1.0, 0.5, 0.0), (0.2, 0.0, 0.2)]
        msg = "rgb: {}, ret_rgb: {}"

        for rgb in rgb_list:
            self._tb.set_led_two(*rgb)
            ret_rgb = self._tb.get_led_two()
            self.validate_tuples(ret_rgb, rgb)

    #@unittest.skip("Temporarily skipped")
    def test_set_both_leds(self):
        """
        Test that the RBG colors set are the same as the one's returned.
        """
        state = self._tb.get_led_state()
        msg = "Default state should be False: {}".format(state)
        self.assertFalse(state, msg)
        rgb_list = [(0, 0, 0), (1, 1, 1), (1.0, 0.5, 0.0), (0.2, 0.0, 0.2)]
        msg = "rgb: {}, ret_rgb: {}"

        for rgb in rgb_list:
            self._tb.set_both_leds(*rgb)
            ret_rgb = self._tb.get_led_one()
            self.validate_tuples(ret_rgb, rgb)
            ret_rgb = self._tb.get_led_two()
            self.validate_tuples(ret_rgb, rgb)

    #@unittest.skip("Temporarily skipped")
    def test_set_and_get_led_state(self):
        """
        Test that the LED state changes.
        """
        state = self._tb.get_led_state()
        msg = "Default state should be False: {}".format(state)
        self.assertFalse(state, msg)
        # Change the state of the LEDs to monitor the batteries.
        self._tb.set_led_state(True)
        state = self._tb.get_led_state()
        msg = "Battery monitoring state should be True".format(state)
        self.assertTrue(state, msg)

    #@unittest.skip("Temporarily skipped")
    def test_set_and_get_comms_failsafe(self):
        """
        Test that the failsafe changes states.
        """
        failsafe = self._tb.get_comms_failsafe()
        msg = "Default failsafe should be False: {}".format(failsafe)
        self.assertFalse(failsafe, msg)
        # Test that motors run continuously.
        speed = 0.2
        self._tb.set_both_motors(speed)
        sleep = 1 # Seconds
        time.sleep(sleep)
        msg = "Motors should run for {} second.".format(sleep)
        m0_speed = self._tb.get_motor_one()
        m1_speed = self._tb.get_motor_two()
        self.assertEqual(m0_speed, speed, msg)
        self.assertEqual(m1_speed, speed, msg)
        # Turn on failsafe
        self._tb.set_comms_failsafe(True)
        failsafe = self._tb.get_comms_failsafe()
        msg = "Failsafe should be True: {}".format(failsafe)
        self.assertTrue(failsafe, msg)
        # Start up motors
        self._tb.set_both_motors(speed)
        time.sleep(sleep)
        msg = ("Motors should run for 1/4 of a second with sleep of {} "
               "second(s).").format(sleep)
        m0_speed = self._tb.get_motor_one()
        m1_speed = self._tb.get_motor_two()
        self.assertNotEqual(m0_speed, speed, msg)
        self.assertNotEqual(m1_speed, speed, msg)




