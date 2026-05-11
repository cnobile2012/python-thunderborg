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
MEDIA_PATH = None


def create_working_dir():  # pragma: no cover
    """
    This function creates a `borg_cube` directory containing a `logs`
    and `run` directories.

    1. The `logs` directory contains all logs.
    2. The `run` directory contains all daemon pid/lock files.
    """
    global BORG_CUBE
    global LOG_PATH
    global RUN_PATH
    global MEDIA_PATH
    home = os.path.expanduser('~')
    borg_cube = os.path.join(home, 'borg_cube')
    logs = os.path.join(borg_cube, 'logs')
    run = os.path.join(borg_cube, 'run')
    media = os.path.join(borg_cube, 'media')

    if not os.path.exists(logs):
        os.makedirs(logs, mode=0o777)

    if not os.path.exists(run):
        os.makedirs(run, mode=0o777)

    if not os.path.exists(media):
        os.makedirs(media, mode=0o777)

    BORG_CUBE = borg_cube
    LOG_PATH = logs
    RUN_PATH = run
    MEDIA_PATH = media


class ConfigLogger(object):
    """
    Setup some basic logging.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                       "[line:%(lineno)d] %(message)s")

    def __init__(self, format=None):
        self._format = format if format else self._DEFAULT_FORMAT

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
        else:  # pragma: no cover
            logging.basicConfig(filename=file_path, format=self._format,
                                level=level)
