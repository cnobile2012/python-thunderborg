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


class ThunderBorg(objects):
    """
    .. autoclass: ThunderBorg
       :members:
    """
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
    """Set the colour of the ThunderBorg LED"""
    COMMAND_GET_LED1 = 2
    """Get the colour of the ThunderBorg LED"""
    COMMAND_SET_LED2 = 3
    """Set the colour of the ThunderBorg Lid LED"""
    COMMAND_GET_LED2 = 4
    """Get the colour of the ThunderBorg Lid LED"""
    COMMAND_SET_LEDS = 5
    """Set the colour of both the LEDs"""
    COMMAND_SET_LED_BATT_MON = 6
    """Set the colour of both LEDs to show the current battery level"""
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
    COMMAND_VALUE_ON = 1
    """I2C value representing on"""
    COMMAND_VALUE_OFF = 0
    """I2C value representing off"""
    COMMAND_ANALOG_MAX = 0x3FF
    """Maximum value for analog readings"""

    def __init__(self, address=_I2C_ID_THUNDERBORG, bus_num=_DEFAULT_BUS_NUM,
                 logger_name='', log_level=logging.WARNING):
        """


        """
        # Setup logging
        if logger_name == '':
            logging.basicConfig()

        self._log = logging.getLogger(logger_name)
        self._log.setLevel(level)
        # Setup I2C connections
        self.__orig_bus_num = bus_num
        self._init_thunder_borg(address, bus_num)

    def _init_thunder_borg(self, address, bus_num)
        self._log.debug("Loading ThunderBorg on bus version %d, address %02X",
                        self._REVISION, address)
        device = self._DEVICE_PREFIX.format(bus_num)
        self._i2c_read = io.open(device, 'rb', buffering=0)
        fcntl.ioctl(self.i2c_read, self._I2C_SLAVE, address)
        self._i2c_write = io.open(device, 'wb', buffering=0)
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

            # See if we are missing chips
            if not found_chip:
                self._log.error("ThunderBorg was not found")
                last_bus_num = bus_num

                if bus_num == self._DEFAULT_BUS_NUM:
                    bus_num = 0
                else:
                    bus_num = 1

                # Lets close both streams before we try to open them again. We
                # don't want memory leaks.
                self._i2c_read.close()
                self._i2c_write.close()
                self._log.info("ThunderBorg not found on bus %d, trying "
                               "bus %d", last_bus_num, bus_num)
                self._init_thunder_borg(address, bus_num)

                # Lets not do this ad infinitum.
                if not found_chip and self.__orig_bus_num != bus_num:
                    self._i2c_read.close()
                    self._i2c_write.close()
                    self._log.error("ThunderBorg could not be found, is it "
                                    "properly attached, the correct address "
                                    "used, and the I2C driver module is "
                                    "active?")
            else:
                self._log.info("ThunderBorg loaded on bus %d at address %02X",
                               bus_num, address)

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
