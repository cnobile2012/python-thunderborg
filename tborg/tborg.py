# -*- coding: utf-8 -*-
#
# tborg/tborg.py
#
"""
The TunderBorg API class


"""
from __future__ import absolute_import

import io
import fcntl
import types
import time
import logging


class ThunderBorg(object):
    """
    .. autoclass: tborg.ThunderBorg
       :members:
    """
    _DEF_LOG_LEVEL = logging.WARNING
    _REVISION = 1
    _DEVICE_PREFIX = '/dev/i2c-{}'
    _DEFAULT_BUS_NUM = 1
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
    short-circuits and under voltage
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
    interrupted
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
    """Set a new I2C address"""
    COMMAND_VALUE_FWD = 1
    """I2C value representing forward"""
    COMMAND_VALUE_REV = 2
    """I2C value representing reverse"""
    COMMAND_VALUE_OFF = 0
    """I2C value representing off"""
    COMMAND_VALUE_ON = 1
    """I2C value representing on"""
    COMMAND_ANALOG_MAX = 0x3FF
    """Maximum value for analog readings"""

    def __init__(self, address=_I2C_ID_THUNDERBORG, bus_num=_DEFAULT_BUS_NUM,
                 logger_name='', log_level=_DEF_LOG_LEVEL):
        """
        Setup logging and initialize the ThunderBorg motor driver board.

        :param address: The I2C address to use, defaults to 0x{0:X}.
        :type address: int
        :param bus_num: The I2C bus number, defaults to {1:d}.
        :type bus_num: int
        :param logger_name: The name of the logger to log to, defaults to
                            the root logger.
        :type logger_name: str
        :param log_level: The lowest log level to log, defaults to {2:s}.
        :type log_level: int
        """
        # Setup logging
        if logger_name == '':
            logging.basicConfig()

        self._log = logging.getLogger(logger_name)
        self._log.setLevel(log_level)
        # Setup I2C connections
        orig_bus_num = bus_num
        found_chip, last_bus_num = self._init_thunder_borg(address, bus_num)

        if not found_chip and orig_bus_num == last_bus_num:
            self._log.error("ThunderBorg not found on bus %s at address %02X",
                            last_bus_num, address)
            self.close_streams()
            def_bus_num = self._DEFAULT_BUS_NUM
            bus_num = 0 if last_bus_num == def_bus_num else def_bus_num
            found_chip, last_bus_num = self._init_thunder_borg(
                address, bus_num)

            if not found_chip:
                self.close_streams()
                self._log.error("ThunderBorg could not be found; is it "
                                "properly attached, the correct address "
                                "used, and the I2C driver module loaded?")
                return

        self._log.info("ThunderBorg loaded on bus %d at address %02X",
                       bus_num, address)
    __init__.__doc__ = __init__.__doc__.format(
        _I2C_ID_THUNDERBORG, _DEFAULT_BUS_NUM,
        logging._levelNames[_DEF_LOG_LEVEL])

    def _init_thunder_borg(self, address, bus_num):
        self._log.debug("Loading ThunderBorg on bus version %d, address %02X",
                        self._REVISION, address)
        device = self._DEVICE_PREFIX.format(bus_num)
        tbfound_chip = False

        try:
            self._i2c_read = io.open(device, 'rb', buffering=0)
            self._i2c_write = io.open(device, 'wb', buffering=0)
        except IOError as e:
            self._log.critical("IO Error, %s", e)
        else:
            fcntl.ioctl(self.i2c_read, self._I2C_SLAVE, address)
            fcntl.ioctl(self.i2c_write, self._I2C_SLAVE, address)

            # Check that the ThunderBorg is connected.
            try:
                data = self._read(self.COMMAND_GET_ID, self._I2C_READ_LEN)
            except KeyboardInterrupt as e:
                self._log.warning("Keyboard interrupt, %s", e)
                raise e
            except Exception as e:
                self._log.error("%s", e)
            else:
                found_chip = self.__check_if_connected(address, bus_num, data)

        return found_chip, bus_num

    def __check_if_connected(self, address, bus_num, data):
        found_chip = False

        if len(data) >= self._I2C_READ_LEN:
            if data[1] == self._I2C_ID_THUNDERBORG:
                found_chip = True
                self._log.info("Found ThunderBorg on bus %d at %02X",
                               bus_num, address)
            else:
                self._log.error("Found a device at %02X, but it is not a "
                                "ThunderBorg (ID %02X instead of %02X)",
                                address, data[1], self._I2C_ID_THUNDERBORG)
        else:
            self._log.error("ThunderBorg not found on bus %d at address %02X",
                            bus_num, address)

        return found_chip

    def close_streams(self):
        """
        Close both streams if the ThunderBorg was not found and when we
        are shutting down. We don't want memory leaks.
        """
        if hasattr(self, '_i2c_read'):
            self._i2c_read.close()
            self._log.debug("_i2c_read is now closed.")

        if hasattr(self, '_i2c_write'):
            self._i2c_write.close()
            self._log.debug("_i2c_write is now closed.")

    def _write(self, command, data):
        """
        Write data to the `ThunderBorg`.

        :param command: Command to send to the `ThunderBorg`.
        :type command: int
        :param data: The data to be sent to the I2C bus.
        :type data: list
        :raises TypeError: If the 'data' argument is the wrong type.
        """
        if not isinstance(data, list):
            msg = "Programming error, the 'data' argument must be of type list"
            self._log.error(msg)
            raise TypeError(msg)

        data.insert(0, command)
        self._i2c_write.write(bytes(data))

    def _read(self, command, length, retry_count=3):
        """
        Reads data from the `ThunderBorg`.

        :param command: Command to send to the `ThunderBorg`.
        :type command: int
        :param length: The number of bytes to read from the `ThunderBorg`.
        :type length: int
        :rtype: A list of bytes returned from the `ThunderBorg`.
        :raises IOError: If reading a command failed.
        """
        for i in range(retry_count-1, -1, -1):
            self._write(command, [])
            reply = self.i2c_read.read(length)
            data = [bt for bt in reply]

            if command == data[0]:
                break

        if len(reply) <= 0:
            msg = "I2C read for command '{}' failed".format(command)
            self._log.error(msg)
            raise IOError(msg)

    def _set_motor(self, level, fwd, rev):
        if level < 0:
            # Reverse
            command = rev
            pwm = -int(self._PWM_MAX * level)
            pwm = self._PWM_MAX if pwm < -self._PWM_MAX else pwm
        else:
            # Forward / stopped
            command = fwd
            pwm = int(self._PWM_MAX * level)
            pwm = self._PWM_MAX if pwm > self._PWM_MAX else pwm

        try:
            self._write(command, [pwm])
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            motor = 1 if fwd == self.COMMAND_SET_A_FWD else 2
            self._log.error("Failed sending motor %d drive level, %s",
                            motor, e)

    def set_motor_one(self, level):
        """
        Set the drive level for motor one.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% foward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_A_FWD, self.COMMAND_SET_A_REV)

    def set_motor_two(self, level):
        """
        Set the drive level for motor two.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% foward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_B_FWD, self.COMMAND_SET_B_REV)

    def set_both_motors(self, level):
        """
        Set the drive level for motor two.

        :param level: Valid levels are from -1.0 to +1.0.
                      A level of 0.0 is full stop.
                      A level of 0.75 is 75% foward.
                      A level of -0.25 is 25% reverse.
                      A level of 1.0 is 100% forward.
        :type level: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_motor(level, self.COMMAND_SET_ALL_FWD,
                        self.COMMAND_SET_ALL_REV)

    def _get_motor(self, command):
        motor = 1 if command == self.COMMAND_GET_A else 2

        try:
            recv = self._read(command, self._I2C_READ_LEN)
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error("Failed reading motor %d drive level, %s",
                            motor, e)
            raise e

        level = float(recv[2]) / PWM_MAX
        direction = recv[1]

        if direction == self.COMMAND_VALUE_REV:
            level = -level
        elif direction != self.COMMAND_VALUE_FWD:
            self._log.error("Invalid command while getting drive level "
                            "for motor %d", motor)

        return level

    def get_motor_one(self):
        """
        Get the drive level of motor one.

        :rtype: The motor drive level.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        return self._get_motor(self.COMMAND_GET_A)

    def get_motor_two(self):
        """
        Get the drive level of motor one.

        :rtype: The motor drive level.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        return self._get_motor(self.COMMAND_GET_B)

    def halt_motors(self):
        """
        Halt both motors. Should be used when ending a program or
        when needing to come to an abrupt halt.

        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        try:
            self._write(self.COMMAND_ALL_OFF, [0])
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error('Failed sending motors halt command, %s', e)
            raise e
        else:
            self._log.debug("Both motors were halted successfully.")

    def _set_led(self, command, r, g, b):
        level_r = max(0, min(self._PWM_MAX, int(r * self._PWM_MAX)))
        level_g = max(0, min(self._PWM_MAX, int(g * self._PWM_MAX)))
        level_b = max(0, min(self._PWM_MAX, int(b * self._PWM_MAX)))

        try:
            self._write(command, [level_r, level_g, level_b])
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error('Failed sending color to the ThunderBorg LED one.')
            raise e

    def set_led_one(self, r, g, b):
        """
        Set the color of the ThunderBorg LED number one.

        .. note::

          (0, 0, 0)       LED off
          (1, 1, 1)       LED full white
          (1.0, 0.5, 0.0) LED bright orange
          (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_led(self.COMMAND_SET_LED1, r, g, b)

    def set_led_two(self, r, g, b):
        """
        Set the color of the ThunderBorg LED number two.

        .. note::

          (0, 0, 0)       LED off
          (1, 1, 1)       LED full white
          (1.0, 0.5, 0.0) LED bright orange
          (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_led(self.COMMAND_SET_LED2, r, g, b)

    def set_both_leds(self, r, g, b):
        """
        Set the color of both of the ThunderBorg LEDs

        .. note::

          (0, 0, 0)       LED off
          (1, 1, 1)       LED full white
          (1.0, 0.5, 0.0) LED bright orange
          (0.2, 0.0, 0.2) LED dull violet

        :param r: Range is between 0.0 and 1.0.
        :type r: float
        :param g: Range is between 0.0 and 1.0.
        :type g: float
        :param b: Range is between 0.0 and 1.0.
        :type b: float
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        self._set_led(self.COMMAND_SET_LEDS, r, g, b)

    def _get_led(self, command):
        try:
            recv = self._read(command, I2C_MAX_LEN)
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            led = 1 if command == self.COMMAND_GET_LED1 else 2
            self._log.error('Failed to read ThunderBorg LED %d color, %s',
                            led, e)
            raise e
        else:
            r = recv[1] / self._PWM_MAX
            g = recv[2] / self._PWM_MAX
            b = recv[3] / self._PWM_MAX
            return r, g, b

    def get_led_one(self):
        """
        Get the current RGB color of the ThunderBorg LED number one.

        .. note::

          (0, 0, 0)       LED off
          (1, 1, 1)       LED full white
          (1.0, 0.5, 0.0) LED bright orange
          (0.2, 0.0, 0.2) LED dull violet

        :rtype: Returns a tuple of the RGB color for LED number one.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        return self._get_led(self.COMMAND_GET_LED1)

    def get_led_two(self):
        """
        Get the current RGB color of the ThunderBorg LED number two.

        .. note::

          (0, 0, 0)       LED off
          (1, 1, 1)       LED full white
          (1.0, 0.5, 0.0) LED bright orange
          (0.2, 0.0, 0.2) LED dull violet

        :rtype: Returns a tuple of the RGB color for LED number two.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        return self._get_led(self.COMMAND_GET_LED2)

    def set_led_state(self, state):
        """
        Set the state of the LEDs from showing the configured state (set
        with `set_led_one` and/or `set_led_two`) to the battery monitoring
        state.

        .. note::

          If in the battery monitoring state the configured state is
          disabled. The battery monitoring state sweeps the full range
          between red (7V) and green (35V) is swept.

        :param state: If `True` (enabled) LEDs will show the current
                      battery level, else if `False` (disabled) the LEDs
                      will be used. `Confused? So am I`
        :type state: bool
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        level = self.COMMAND_VALUE_ON if state else self.COMMAND_VALUE_OFF

        try:
            self._write(self.COMMAND_SET_LED_BATT_MON, [level])
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error(
                "Failed to send LEDs battery monitoring state, %s", e)
            raise e

    def get_led_state(self):
        """
        Get the state of the LEDs between the configured and battery
        monitoring state.

        :rtype: Returns `False` for the configured state and `True` for
                the battery monitoring state.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_LED_BATT_MON,
                              self._I2C_READ_LEN)
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error(
                "Failed reading LED battery monitoring state, %s", e)
            raise e

        return False if recv[1] == self.COMMAND_VALUE_OFF else True

    def set_comms_failsafe(self, state):
        """
        Set the state of the communication failsafe. If the failsafe state
        is on the motors will be turned off unless the board receives a
        command at least once every 1/4th of a second.

        :param state: If set to `True` failsafe is enabled, else if set to
                      `False` failsafe is disabled. Default is disables
                      when powered on.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        level = self.COMMAND_VALUE_ON if state else self.COMMAND_VALUE_OFF

        try:
            self._write(self.COMMAND_SET_FAILSAFE, [level])
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error(
                "Failed sending communications failsafe state, %s", e)
            raise e

    def get_comms_failsafe(self):
        """
        Get the failsafe state.

        :rtype: Returns the failsafe state.
        :raises KeyboardInterrupt: Keyboard interrupt.
        :raises IOError: An error happening on a stream.
        """
        try:
            recv = self._read(self.COMMAND_GET_FAILSAFE, self._I2C_READ_LEN)
        except KeyboardInterrupt as e:
            self._log.warning("Keyboard interrupt, %s", e)
            raise e
        except IOError as e:
            self._log.error(
                "Failed reading communications failsafe state, %s", e)
            raise e

        return False if recv[1] == COMMAND_VALUE_OFF else True


