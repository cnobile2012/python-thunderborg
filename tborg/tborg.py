# -*- coding: utf-8 -*-
#
# tborg/tborg.py
#
"""
The TunderBorg API

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

import io
import fcntl
import types
import time
import logging
import six

_LEVEL_TO_NAME = logging._levelNames if six.PY2 else logging._levelToName

class ThunderBorgException(Exception):
    pass


class ThunderBorg(object):
    """
    This module is designed to communicate with the ThunderBorg motor
    controller board.
    """
    #.. autoclass: tborg.ThunderBorg
    #   :members:
    #
    # sudo i2cdetect -y 1
    _DEF_LOG_LEVEL = logging.WARNING
    _DEVICE_PREFIX = '/dev/i2c-{}'
    DEFAULT_BUS_NUM = 1 # Rev. 2 boards
    """Default I²C bus number."""
    DEFAULT_I2C_ADDRESS = 0x15
    """Default I²C address of the ThunderBorg board."""
    _POSSIBLE_BUSS = [0, 1]
    _I2C_ID_THUNDERBORG = 0x15
    _I2C_SLAVE = 0x0703
    _I2C_READ_LEN = 6
    _PWM_MAX = 255
    _VOLTAGE_PIN_MAX = 36.3
    """Maximum voltage from the analog voltage monitoring pin"""
    _VOLTAGE_PIN_CORRECTION = 0.0
    """Correction value for the analog voltage monitoring pin"""
    _BATTERY_MIN_DEFAULT = 7.0
    """Default minimum battery monitoring voltage"""
    _BATTERY_MAX_DEFAULT = 35.0
    """Default maximum battery monitoring voltage"""
    # Commands
    COMMAND_SET_LED1 = 1
    """Set the color of the ThunderBorg LED"""
    COMMAND_GET_LED1 = 2
    """Get the color of the ThunderBorg LED"""
    COMMAND_SET_LED2 = 3
    """Set the color of the ThunderBorg Lid LED"""
    COMMAND_GET_LED2 = 4
    """Get the color of the ThunderBorg Lid LED"""
    COMMAND_SET_LEDS = 5
    """Set the color of both the LEDs"""
    COMMAND_SET_LED_BATT_MON = 6
    """Set the color of both LEDs to show the current battery level"""
    COMMAND_GET_LED_BATT_MON = 7
    """Get the state of showing the current battery level via the LEDs"""
    COMMAND_SET_A_FWD = 8
    """Set motor A PWM rate in a forwards direction"""
    COMMAND_SET_A_REV = 9
    """Set motor A PWM rate in a reverse direction"""
    COMMAND_GET_A = 10
    """Get motor A direction and PWM rate"""
    COMMAND_SET_B_FWD = 11
    """Set motor B PWM rate in a forwards direction"""
    COMMAND_SET_B_REV = 12
    """Set motor B PWM rate in a reverse direction"""
    COMMAND_GET_B = 13
    """Get motor B direction and PWM rate"""
    COMMAND_ALL_OFF = 14
    """Switch everything off"""
    COMMAND_GET_DRIVE_A_FAULT = 15
    """
    Get the drive fault flag for motor A, indicates faults such as
    short-circuits and under voltage.
    """
    COMMAND_GET_DRIVE_B_FAULT = 16
    """
    Get the drive fault flag for motor B, indicates faults such as
    short-circuits and under voltage
    """
    COMMAND_SET_ALL_FWD = 17
    """Set all motors PWM rate in a forwards direction"""
    COMMAND_SET_ALL_REV = 18
    """Set all motors PWM rate in a reverse direction"""
    COMMAND_SET_FAILSAFE = 19
    """
    Set the failsafe flag, turns the motors off if communication is
    interrupted.
    """
    COMMAND_GET_FAILSAFE = 20
    """Get the failsafe flag"""
    COMMAND_GET_BATT_VOLT = 21
    """Get the battery voltage reading"""
    COMMAND_SET_BATT_LIMITS = 22
    """Set the battery monitoring limits"""
    COMMAND_GET_BATT_LIMITS = 23
    """Get the battery monitoring limits"""
    COMMAND_WRITE_EXTERNAL_LED = 24
    """Write a 32bit pattern out to SK9822 / APA102C"""
    COMMAND_GET_ID = 0x99
    """Get the board identifier"""
    COMMAND_SET_I2C_ADD = 0xAA
    """Set a new I²C address"""
    COMMAND_VALUE_FWD = 1
    """I²C value representing forward"""
    COMMAND_VALUE_REV = 2
    """I²C value representing reverse"""
    COMMAND_VALUE_OFF = 0
    """I²C value representing off"""
    COMMAND_VALUE_ON = 1
    """I²C value representing on"""
    COMMAND_ANALOG_MAX = 0x3FF
    """Maximum value for analog readings"""

    def __init__(self,
                 bus_num=DEFAULT_BUS_NUM,
                 address=DEFAULT_I2C_ADDRESS,
                 logger_name='',
                 log_level=_DEF_LOG_LEVEL,
                 auto_set_addr=False,
                 static_init=False):
        """
        Setup logging and initialize the ThunderBorg motor driver board.

        :param bus_num: The I²C bus number, defaults to {1:d}.
        :type bus_num: int
        :param address: The I²C address to use, defaults to 0x{0:02X}.
        :type address: int
        :param logger_name: The name of the logger to log to, defaults to
                            the root logger.
        :type logger_name: str
        :param log_level: The lowest log level to log, defaults to {2:s}.
        :type log_level: int
        :param auto_set_addr: If set to `True` will use the first board
                              that is found. Default is `False`.
        :type auto_set_addr: bool
        :param static_init: If called by a public class method.
        :type static_init: bool
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream or an
                                      invalid address or bus was provided.
        """
        # Setup logging
        if logger_name == '':
            logging.basicConfig()

        self._log = logging.getLogger(logger_name)
        self._log.setLevel(log_level)

        if not static_init:
            self._initialize_board(bus_num, address, auto_set_addr)

    __init__.__doc__ = __init__.__doc__.format(
        _I2C_ID_THUNDERBORG, DEFAULT_BUS_NUM, _LEVEL_TO_NAME[_DEF_LOG_LEVEL])

    def _initialize_board(self, bus_num, address, auto_set_addr):
        """
        Setup the I²C connections and file streams for read and write. If
        the default board cannot be found search for a board and if
        ``auto_set_addr`` is ``True`` configure the found board.
        """
        if not self._is_thunder_borg_board(bus_num, address, self):
            err_msg = "ThunderBorg not found on bus %s at address 0x%02X"
            self._log.error(err_msg, bus_num, address)
            buss = [bus for bus in self._POSSIBLE_BUSS
                    if not auto_set_addr and bus != bus_num]
            found_chip = False

            for bus in buss:
                found_chip = self._is_thunder_borg_board(bus, address, self)

                if not found_chip:
                    self._log.error(err_msg, bus, address)

            if (not found_chip
                and (not auto_set_addr or
                     (auto_set_addr
                      and not self._auto_set_address(bus_num, self)))):
                msg = ("ThunderBorg could not be found; is it properly "
                       "attached, the correct address used, and the I2C "
                       "driver module loaded?")
                self._log.critical(msg)
                raise ThunderBorgException(msg)

    #
    # Class Methods
    #

    @classmethod
    def _is_thunder_borg_board(cls, bus_num, address, tb):
        """
        Try to initialize a board on a given bus and address.
        """
        tb._log.debug("Loading ThunderBorg on bus number %d, address 0x%02X",
                      cls.DEFAULT_BUS_NUM, address)
        found_chip = False

        if cls._init_bus(bus_num, address, tb):
            try:
                recv = tb._read(cls.COMMAND_GET_ID, cls._I2C_READ_LEN)
            except KeyboardInterrupt as e: # pragma: no cover
                tb.close_streams()
                tb._log.warning("Keyboard interrupt, %s", e)
                raise e
            except IOError as e:
                pass
            else:
                found_chip = cls._check_board_chip(recv, bus_num, address, tb)

        return found_chip

    @classmethod
    def _init_bus(cls, bus_num, address, tb):
        """
        Check that the bus exists then initialize the board on the given
        address.
        """
        device_found = False
        device = cls._DEVICE_PREFIX.format(bus_num)

        try:
            tb._i2c_read = io.open(device, mode='rb', buffering=0)
            tb._i2c_write = io.open(device, mode='wb', buffering=0)
        except (IOError, OSError) as e: # pragma: no cover
            tb.close_streams()
            msg = ("Could not open read or write stream on bus {:d} at "
                   "address 0x{:02X}, {}").format(bus_num, address, e)
            tb._log.critical(msg)
        else:
            try:
                fcntl.ioctl(tb._i2c_read, cls._I2C_SLAVE, address)
                fcntl.ioctl(tb._i2c_write, cls._I2C_SLAVE, address)
            except (IOError, OSError) as e: # pragma: no cover
                tb.close_streams()
                msg = ("Failed to initialize ThunderBorg on bus number {:d}, "
                       "address 0x{:02X}, {}").format(bus_num, address, e)
                tb._log.critical(msg)
            else:
                device_found = True

        return device_found

    @classmethod
    def _check_board_chip(cls, recv, bus_num, address, tb):
        found_chip = False
        length = len(recv)

        if length == cls._I2C_READ_LEN:
            if recv[1] == cls._I2C_ID_THUNDERBORG:
                found_chip = True
                msg = "Found ThunderBorg on bus '%d' at address 0x%02X."
                tb._log.info(msg, bus_num, address)
            else:
                msg = ("Found a device at 0x%02X on bus number %d, but it is "
                       "not a ThunderBorg (ID 0x%02X instead of 0x%02X).")
                tb._log.info(msg, address, bus_num, recv[1],
                             cls._I2C_ID_THUNDERBORG)
        else: # pragma: no cover
            msg = ("Wrong number of bytes received, found '%d', should be "
                   "'%d' at address 0x%02X.")
            tb._log.error(msg, length, cls._I2C_READ_LEN, address)

        return found_chip

    @classmethod
    def _auto_set_address(cls, bus_num, tb):
        found_chip = False
        boards = cls.find_board(tb=tb, close=False)
        msg = "Found ThunderBorg(s) on bus '%d' at address %s."
        hex_boards = ', '.join(['0x%02X' % b for b in boards])
        tb._log.warning(msg, bus_num, hex_boards)

        if boards:
            found_chip = cls._is_thunder_borg_board(bus_num, boards[0], tb)

        return found_chip

    @classmethod
    def find_board(cls, bus_num=DEFAULT_BUS_NUM, tb=None, close=True,
                   logger_name=''):
        """
        Scans the I²C bus for ThunderBorg boards and returns a list of
        all usable addresses.

        .. note::

           Rev 1 boards use bus number 0 and rev 2 boards use bus number 1.

        :param bus_num: The bus number where the address will be scanned.
                        Default bus number is 1.
        :type bus_num: int
        :param tb: Use a pre-existing ThunderBorg instance. Default is `None`.
        :type tb: ThunderBorg instance
        :param close: Default is `True` to close the stream before exiting.
        :type close: bool
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        found = []
        if not tb: tb = ThunderBorg(logger_name=logger_name,
                                    log_level=logging.INFO,
                                    static_init=True)
        tb._log.info("Scanning I2C bus number %d.", bus_num)

        for address in range(0x03, 0x77, 1):
            if cls._is_thunder_borg_board(bus_num, address, tb):
                found.append(address)

        if close: tb.close_streams()

        if len(found) == 0: # pragma: no cover
            msg = ("No ThunderBorg boards found, is the bus number '%d' "
                   "correct? (should be 0 for Rev 1 and 1 for Rev 2)")
            tb._log.error(msg, bus_num)

        return found

    @classmethod
    def set_i2c_address(cls, new_addr, cur_addr=-1, bus_num=DEFAULT_BUS_NUM,
                        logger_name=''):
        """
        Scans the I²C bus for the first ThunderBorg and sets it to a
        new I²C address. If cur_addr is supplied it will change the
        address of the board at that address rather than scanning the bus.
        The bus_num if supplied determines which I²C bus to scan using
        0 for Rev 1 or 1 for Rev 2 boards. If bum_bus is not supplied it
        defaults to 1.
        Warning, this new I²C address will still be used after
        resetting the power on the device.

        :param new_addr: New address to set a ThunderBorg board to.
        :type new_addr: int
        :param cur_addr: The current address of a ThunderBorg board. The
                         default of `-1` will scan the entire range.
        :type cur_addr: int
        :param bun_num: The bus number where the address range will be
                        found. Default is set to 1.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream or
                                      failed to set the new address.
        """
        tb = ThunderBorg(log_level=logging.INFO, logger_name=logger_name,
                         static_init=True)

        if not (0x03 <= new_addr <= 0x77):
            msg = ("Error, I2C addresses must be in the range "
                   "of 0x03 to 0x77")
            tb._log.error(msg)
            raise ThunderBorgException(msg)

        if cur_addr < 0x00:
            found = cls.find_board(bus_num=bus_num, tb=tb)

            if len(found) < 1: # pragma: no cover
                msg = ("No ThunderBorg boards found, cannot set a new "
                       "I2C address!")
                tb._log.info(msg)
                raise ThunderBorgException(msg)

            cur_addr = found[0]

        msg = "Changing I2C address from 0x%02X to 0x%02X on bus number %d."
        tb._log.info(msg, cur_addr, new_addr, bus_num)

        if cls._init_bus(bus_num, cur_addr, tb):
            try:
                recv = tb._read(cls.COMMAND_GET_ID, cls._I2C_READ_LEN)
            except KeyboardInterrupt as e: # pragma: no cover
                tb.close_streams()
                tb._log.warning("Keyboard interrupt, %s", e)
                raise e
            except IOError as e: # pragma: no cover
                tb.close_streams()
                msg = "Missing ThunderBorg at address 0x%02X."
                tb._log.error(msg, cur_addr)
                raise ThunderBorgException(msg)
            else:
                if cls._check_board_chip(recv, bus_num, cur_addr, tb):
                    tb._write(cls.COMMAND_SET_I2C_ADD, [new_addr])
                    time.sleep(0.1)
                    msg = ("Address changed to 0x%02X, attempting to talk "
                           "with the new address.")
                    tb._log.info(msg, new_addr)

                    if cls._init_bus(bus_num, new_addr, tb):
                        try:
                            recv = tb._read(cls.COMMAND_GET_ID,
                                            cls._I2C_READ_LEN)
                        except KeyboardInterrupt as e: # pragma: no cover
                            tb.close_streams()
                            tb._log.warning("Keyboard interrupt, %s", e)
                            raise e
                        except IOError as e: # pragma: no cover
                            tb.close_streams()
                            msg = ("Missing ThunderBorg at address 0x{:02X}."
                                   ).format(new_addr)
                            tb._log.error(msg)
                            raise ThunderBorgException(msg)
                        else:
                            if cls._check_board_chip(recv, bus_num,
                                                     new_addr, tb):
                                msg = ("New I2C address of 0x{:02X} set "
                                       "successfully.").format(new_addr)
                                tb._log.info(msg)
                            else: # pragma: no cover
                                msg = ("Failed to set address to 0x{:02X}"
                                       ).format(new_addr)
                                tb._log.error(msg)
                                raise ThunderBorgException(msg)

                tb.close_streams()

    #
    # Instance Methods
    #

    def close_streams(self):
        """
        Close both streams if the ThunderBorg was not found and when we
        are shutting down. We don't want memory leaks.
        """
        if hasattr(self, '_i2c_read'):
            self._i2c_read.close()
            self._log.debug("I2C read stream is now closed.")

        if hasattr(self, '_i2c_write'):
            self._i2c_write.close()
            self._log.debug("I2C write stream is now closed.")

    def _write(self, command, data):
        """
        Write data to the `ThunderBorg`.

        :param command: Command to send to the `ThunderBorg`.
        :type command: int
        :param data: The data to be sent to the I²C bus.
        :type data: list
        :raises ThunderBorgException: If the 'data' argument is the wrong
                                      type.
        """
        assert isinstance(data, list), (
            "Programming error, the 'data' argument must be of type list.")
        assert hasattr(self, '_i2c_write'), (
            "Programming error, the write stream has not been initialized")
        assert hasattr(self._i2c_write, 'write'), (
            "Programming error, the write stream object is not a stream.")

        data.insert(0, command)

        if six.PY2: # pragma: no cover
            #  Either PY2 or PY3 can be tested at a given time.
            data = ''.join([chr(byte) for byte in data])
        else:
            data = bytes(data)

        try:
            self._i2c_write.write(data)
        except ValueError as e: # pragma: no cover
            msg = "{}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def _read(self, command, length, retry_count=3):
        """
        Reads data from the `ThunderBorg`.

        :param command: Command to send to the `ThunderBorg`.
        :type command: int
        :param length: The number of bytes to read from the `ThunderBorg`.
        :type length: int
        :param retry_count: Number of times to retry the read. Default is 3.
        :type retry_count: int
        :rtype: A list of bytes returned from the `ThunderBorg`.
        :raises ThunderBorgException: If reading a command failed.
        """
        assert hasattr(self, '_i2c_read'), (
            "Programming error, the read stream has not been initialized")
        assert hasattr(self._i2c_read, 'read'), (
            "Programming error, the read stream object is not a stream.")

        for i in range(retry_count):
            self._write(command, [])
            recv = self._i2c_read.read(length)

            # Split string/bytes
            # b'\x99\x15\x00\x00\x00\x00' [153, 21, 0, 0, 0, 0]
            if six.PY2: # pragma: no cover
                # Either PY2 or PY3 can be tested at a given time.
                data = [ord(bt) for bt in recv]
            else:
                data = [bt for bt in recv]

            if command == data[0]:
                break

        if len(data) <= 0: # pragma: no cover
            msg = "I2C read for command '{}' failed.".format(command)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        return data

    def _set_motor(self, level, fwd, rev):
        if level < 0:
            # Reverse
            command = rev
            pwm = -int(self._PWM_MAX * level)
            pwm = self._PWM_MAX if pwm > self._PWM_MAX else pwm
        else:
            # Forward / stopped
            command = fwd
            pwm = int(self._PWM_MAX * level)
            pwm = self._PWM_MAX if pwm > self._PWM_MAX else pwm

        try:
            self._write(command, [pwm])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            motor = 1 if fwd == self.COMMAND_SET_A_FWD else 2
            msg = "Failed sending motor {} drive level {}, {}".format(
                motor, level, e)
            self._log.error(msg)
            raise ThunderBorgException(msg)
        except ValueError as e:
            motor = 1 if fwd == self.COMMAND_SET_A_FWD else 2
            msg = "Failed sending motor {} drive level {}, pwm: {}, {}".format(
                motor, level, pwm, e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def set_motor_one(self, level):
        """
        Set the drive level for motor one.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% forward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_A_FWD, self.COMMAND_SET_A_REV)

    def set_motor_two(self, level):
        """
        Set the drive level for motor two.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% forward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_B_FWD, self.COMMAND_SET_B_REV)

    def set_both_motors(self, level):
        """
        Set the drive level for motor two.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% forward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_ALL_FWD,
                        self.COMMAND_SET_ALL_REV)

    def _get_motor(self, command):
        """
        Base motor speed retrival method.

        :param command: 
        """
        motor = 1 if command == self.COMMAND_GET_A else 2

        try:
            recv = self._read(command, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed reading motor %d drive level, {}".format(motor, e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        level = float(recv[2]) / self._PWM_MAX
        direction = recv[1]

        if direction == self.COMMAND_VALUE_REV:
            level = -level
        elif direction != self.COMMAND_VALUE_FWD: # pragma: no cover
            msg = ("Invalid command '{:02d}' while getting drive level "
                   "for motor {:d}.").format(direction, motor)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        return level

    def get_motor_one(self):
        """
        Get the drive level of motor one.

        :rtype: The motor drive level.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_motor(self.COMMAND_GET_A)

    def get_motor_two(self):
        """
        Get the drive level of motor two.

        :rtype: The motor drive level.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_motor(self.COMMAND_GET_B)

    def halt_motors(self):
        """
        Halt both motors. Should be used when ending a program or
        when needing to come to an abrupt halt. Executing
        ``set_both_motors(0)`` essentially does the same thing.

        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        try:
            self._write(self.COMMAND_ALL_OFF, [0])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed sending motors halt command, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)
        else:
            self._log.debug("Both motors were halted successfully.")

    def _set_led(self, command, r, g, b):
        level_r = max(0, min(self._PWM_MAX, int(r * self._PWM_MAX)))
        level_g = max(0, min(self._PWM_MAX, int(g * self._PWM_MAX)))
        level_b = max(0, min(self._PWM_MAX, int(b * self._PWM_MAX)))

        try:
            self._write(command, [level_r, level_g, level_b])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed sending color to the ThunderBorg LED one."
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def set_led_one(self, r, g, b):
        """
        Set the color of the ThunderBorg LED number one.

        .. note::

           1. (0, 0, 0)       LED off
           2. (1, 1, 1)       LED full white
           3. (1.0, 0.5, 0.0) LED bright orange
           4. (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_led(self.COMMAND_SET_LED1, r, g, b)

    def set_led_two(self, r, g, b):
        """
        Set the color of the ThunderBorg LED number two.

        .. note::

           1. (0, 0, 0)       LED off
           2. (1, 1, 1)       LED full white
           3. (1.0, 0.5, 0.0) LED bright orange
           4. (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_led(self.COMMAND_SET_LED2, r, g, b)

    def set_both_leds(self, r, g, b):
        """
        Set the color of both of the ThunderBorg LEDs

        .. note::

           1. (0, 0, 0)       LED off
           2. (1, 1, 1)       LED full white
           3. (1.0, 0.5, 0.0) LED bright orange
           4. (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        self._set_led(self.COMMAND_SET_LEDS, r, g, b)

    def _get_led(self, command):
        try:
            recv = self._read(command, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            led = 1 if command == self.COMMAND_GET_LED1 else 2
            msg = "Failed to read ThunderBorg LED {} color, {}".format(led, e)
            self._log.error(msg)
            raise ThunderBorgException(msg)
        else:
            r = recv[1] / float(self._PWM_MAX)
            g = recv[2] / float(self._PWM_MAX)
            b = recv[3] / float(self._PWM_MAX)
            return r, g, b

    def get_led_one(self):
        """
        Get the current RGB color of the ThunderBorg LED number one.

        .. note::

           1. (0, 0, 0)       LED off
           2. (1, 1, 1)       LED full white
           3. (1.0, 0.5, 0.0) LED bright orange
           4. (0.2, 0.0, 0.2) LED dull violet

        :rtype: Return a tuple of the RGB color for LED number one.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_led(self.COMMAND_GET_LED1)

    def get_led_two(self):
        """
        Get the current RGB color of the ThunderBorg LED number two.

        .. note::

           1. (0, 0, 0)       LED off
           2. (1, 1, 1)       LED full white
           3. (1.0, 0.5, 0.0) LED bright orange
           4. (0.2, 0.0, 0.2) LED dull violet

        :rtype: Return a tuple of the RGB color for LED number two.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_led(self.COMMAND_GET_LED2)

    def set_led_battery_state(self, state):
        """
        Change from the default LEDs state (set with `set_led_one` and/or
        `set_led_two`) to the battery monitoring state.

        .. note::

           If in the battery monitoring state the configured state is
           disabled. The battery monitoring state sweeps the full range
           between red (7V) and green (35V).

        :param state: If `True` (enabled) LEDs will show the current
                      battery level, else if `False` (disabled) the LEDs
                      will be controlled with the `set_led_*` and the
                      `set_both_leds` methods.
        :type state: bool
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        level = self.COMMAND_VALUE_ON if state else self.COMMAND_VALUE_OFF

        try:
            self._write(self.COMMAND_SET_LED_BATT_MON, [level])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed to send LEDs state change, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def get_led_battery_state(self):
        """
        Get the state of the LEDs between the default and the battery
        monitoring state.

        :rtype: Return `False` for the default state and `True` for
                the battery monitoring state.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_LED_BATT_MON,
                              self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed reading LED state, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        return False if recv[1] == self.COMMAND_VALUE_OFF else True

    def set_comms_failsafe(self, state):
        """
        Set the state of the motor failsafe. The default failsafe state
        of ``False`` will cause the motors to continuously run without a
        keepalive signal. If set to ``True`` the motors will shutdown
        after 1/4 of a second unless it is sent the speed command every
        1/4 of a second.

        :param state: If set to ``True`` failsafe is enabled, else if set
                      to ``False`` failsafe is disabled. Default is
                      disables when powered on.
        :type state: bool
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        level = self.COMMAND_VALUE_ON if state else self.COMMAND_VALUE_OFF

        try:
            self._write(self.COMMAND_SET_FAILSAFE, [level])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed sending communications failsafe state, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def get_comms_failsafe(self):
        """
        Get the failsafe state.

        :rtype: Return the failsafe state.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_FAILSAFE, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed reading communications failsafe state, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        return False if recv[1] == self.COMMAND_VALUE_OFF else True

    def _get_drive_fault(self, command):
        try:
            recv = self._read(command, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            motor = 1 if command == self.COMMAND_GET_DRIVE_A_FAULT else 2
            msg = ("Failed reading the drive fault state for "
                   "motor {}, {}").format(motor, e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        return False if recv[1] == self.COMMAND_VALUE_OFF else True

    def get_drive_fault_one(self):
        """
        Read the motor drive fault state for motor one.

        .. note::

           1. Faults may indicate power problems, such as under-voltage
              (not enough power), and may be cleared by setting a lower
              drive power.
           2. If a fault is persistent (repeatably occurs when trying to
              control the board) it may indicate a wiring issue such as
              indicated below.

             a. The supply is not powerful enough for the motors. The
                board has a bare minimum requirement of 6V to operate
                correctly. The recommended minimum supply of 7.2V should
                be sufficient for smaller motors.
             b. The + and - connections for the motor are connected to
                each other.
             c. Either + or - is connected to ground (GND, also known as
                0V or earth).
             d. Either + or - is connected to the power supply (V+,
                directly to the battery or power pack).
             e. One of the motors may be damaged.

           3. Faults will self-clear, they do not need to be reset, however
              some faults require both motors to be moving at less than
              100% to clear.
           4. The easiest way to run a check is to put both motors at a low
              power setting that is high enough for them to rotate easily.
              e.g. 30%
           5. Note that the fault state may be true at power up, this is
              normal and should clear when both motors have been driven.

        :rtype: Return a `False` if there are no problems else a `True` if
                a fault has been detected.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_drive_fault(self.COMMAND_GET_DRIVE_A_FAULT)


    def get_drive_fault_two(self):
        """
        Read the motor drive fault state for motor two.

        .. note::

           1. Faults may indicate power problems, such as under-voltage
              (not enough power), and may be cleared by setting a lower
              drive power.
           2. If a fault is persistent (repeatably occurs when trying to
              control the board) it may indicate a wiring issue such as
              indicated below.

             a. The supply is not powerful enough for the motors. The
                board has a bare minimum requirement of 6V to operate
                correctly. The recommended minimum supply of 7.2V should
                be sufficient for smaller motors.
             b. The + and - connections for the motor are connected to
                each other.
             c. Either + or - is connected to ground (GND, also known as
                0V or earth).
             d. Either + or - is connected to the power supply (V+,
                directly to the battery or power pack).
             e. One of the motors may be damaged.

           3. Faults will self-clear, they do not need to be reset, however
              some faults require both motors to be moving at less than
              100% to clear.
           4. The easiest way to run a check is to put both motors at a low
              power setting that is high enough for them to rotate easily.
              e.g. 30%
           5. Note that the fault state may be true at power up, this is
              normal and should clear when both motors have been driven.

        :rtype: Return a `False` if there are no problems else a `True` if
                a fault has been detected.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        return self._get_drive_fault(self.COMMAND_GET_DRIVE_B_FAULT)

    def get_battery_voltage(self):
        """
        Read the current battery level from the main input.

        :rtype: Return a voltage value based on the 3.3 V rail as a
                reference.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_BATT_VOLT, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed reading battery level, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        raw = (recv[1] << 8) + recv[2]
        level = float(raw) / self.COMMAND_ANALOG_MAX
        level *= self._VOLTAGE_PIN_MAX
        return level + self._VOLTAGE_PIN_CORRECTION

    def set_battery_monitoring_limits(self, minimum, maximum):
        """
        Set the battery monitoring limits used for setting the LED color.

        .. note::

           1. The colors shown, range from full red at minimum or below,
              yellow half way, and full green at maximum or higher.
           2. These values are stored in EEPROM and reloaded when the board
              is powered.

        :param minimum: Value between 0.0 and 36.3 Volts.
        :type minimum: float
        :param maximum: Value between 0.0 and 36.3 Volts.
        :type maximum: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        level_min = float(minimum) / self._VOLTAGE_PIN_MAX
        level_max = float(maximum) / self._VOLTAGE_PIN_MAX
        level_min = max(0, min(0xFF, int(level_min * 0xFF)))
        level_max = max(0, min(0xFF, int(level_max * 0xFF)))

        try:
            self._write(self.COMMAND_SET_BATT_LIMITS, [level_min, level_max])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed sending battery monitoring limits, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)
        else:
            time.sleep(0.2) # Wait for EEPROM write to complete

    def get_battery_monitoring_limits(self):
        """
        Read the current battery monitoring limits used for setting the
        LED color.

        .. note::

           The colors shown, range from full red at minimum or below,
           yellow half way, and full green at maximum or higher.

        :rtype: Return a tuple of `(minimum, maximum)`. The values are
                between 0.0 and 36.3 V.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_BATT_LIMITS, self._I2C_READ_LEN)
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = "Failed reading battery monitoring limits, {}".format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

        level_min = float(recv[1]) / 0xFF
        level_max = float(recv[2]) / 0xFF
        level_min *= self._VOLTAGE_PIN_MAX
        level_max *= self._VOLTAGE_PIN_MAX
        return level_min, level_max

    def write_external_led_word(self, b0, b1, b2, b3):
        """
        Write low level serial LED 32 bit word to set multiple LED devices
        like SK9822 and APA102C.

        .. note::

           Bytes are written MSB (Most Significant Byte) first, starting at
           b0. e.g. Executing ``tb.write_external_led_word(255, 64, 1, 0)``
           would send 11111111 01000000 00000001 00000000 to the LEDs.

        :param b0: Byte zero
        :type b0: int
        :param b1: Byte one
        :type b1: int
        :param b2: Byte two
        :type b2: int
        :param b3: Byte three
        :type b3: int
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        b0 = max(0, min(self._PWM_MAX, int(b0)))
        b1 = max(0, min(self._PWM_MAX, int(b1)))
        b2 = max(0, min(self._PWM_MAX, int(b2)))
        b3 = max(0, min(self._PWM_MAX, int(b3)))

        try:
            self._write(self.COMMAND_WRITE_EXTERNAL_LED, [b0, b1, b2, b3])
        except KeyboardInterrupt as e: # pragma: no cover
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e: # pragma: no cover
            msg = ("Failed sending binary word for the external LEDs, {}"
                   ).format(e)
            self._log.error(msg)
            raise ThunderBorgException(msg)

    def set_external_led_colors(self, colors):
        """
        Takes a set of RGB values to set multiple LED devices like
        SK9822 and APA102C.

        .. note::

           1. Each call will set all of the LEDs.

           2. Executing ``tb.set_external_led_colors([[1.0, 1.0, 0.0]])``
              will set a single LED to full yellow.
           3. Executing ``tb.set_external_led_colors([[1.0, 0.0, 0.0], [0.5, 0.0, 0.0], [0.0, 0.0, 0.0]])`` will set LED 1 to full red, LED 2 to half red,
              and LED 3 to off.

        :param colors: The RGB colors for setting the LEDs.
        :type colors: list
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises ThunderBorgException: An error happened on a stream.
        """
        # Send the start marker
        self.write_external_led_word(0, 0, 0, 0)

        # Send each color in turn
        for r, g, b in colors:
            self.write_external_led_word(255, 255 * b, 255 * g, 255 * r)
