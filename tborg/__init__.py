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

from .tborg import ThunderBorg

__all__ = ['ConfigLogger', 'ThunderBorg']


class ConfigLogger(object):
    """
    Setup some basic logging.
    """
    _DEFAULT_FORMAT = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                       "[line:%(lineno)d] %(message)s")

    def __init__(self, log_path=None, format_str=None):
        if log_path:
            self._log_path = log_path.rstrip('/')

        if format_str:
            self._format = format_str
        else:
            self._format = self._DEFAULT_FORMAT

    def config(self, loggerName=None, filename=None, level=logging.WARNING):
        """
        Config the logger.
        """
        if filename is not None:
            file_path = os.path.join(self._log_path, filename)
        else:
            file_path = None

        if logger_name and file_path:
            logger = logging.getLogger(loggerName)
            logger.setLevel(level)
            handler = logging.FileHandler(file_path)
            formatter = logging.Formatter(self._format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            logging.basicConfig(filename=file_path, format=self._format,
                                level=level)
