# -*- coding: utf-8 -*-
#
# tborg/__init__.py
#
"""
The ConfigLogger class is used to configure loggers.

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

import os
import logging

from .tborg import ThunderBorg, ThunderBorgException

__all__ = ['create_working_dir', 'ConfigLogger', 'ThunderBorg',
           'ThunderBorgException']

# Some file locations, but can only be imported after create_working_dir()
# is run.
BORG_CUBE = None
LOG_PATH = None
RUN_PATH = None


def create_working_dir():
    """
    This function creates a `borg_cube` directory containing a `logs`
    and `run` directories.

    1. The `logs` directory contains all logs.
    2. The `run` directory contains all daemon pid/lock files.
    """
    global BORG_CUBE
    global LOG_PATH
    global RUN_PATH
    home = os.path.expanduser('~')
    borg_cube = os.path.join(home, 'borg_cube')
    logs = os.path.join(borg_cube, 'logs')
    run = os.path.join(borg_cube, 'run')

    try:
        os.makedirs(logs, mode=0o777)
        os.makedirs(run, mode=0o777)
    except OSError:
        pass

    BORG_CUBE = borg_cube
    LOG_PATH = logs
    RUN_PATH = run


class ConfigLogger(object):
    """
    Setup some basic logging.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                       "[line:%(lineno)d] %(message)s")

    def __init__(self, format_str=None):
        self._format = format_str if format_str else self._DEFAULT_FORMAT

    def config(self, logger_name=None, file_path=None, level=logging.WARNING):
        """
        Config the logger.
        """
        if logger_name and file_path:
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            handler = logging.FileHandler(file_path)
            formatter = logging.Formatter(self._format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            logging.basicConfig(filename=file_path, format=self._format,
                                level=level)
