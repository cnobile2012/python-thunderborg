.. -*-coding: utf-8-*-

********************************
ThunderBorg Motor Controller API
********************************

.. image:: http://img.shields.io/pypi/l/python-thunderborg.svg
   :target: https://pypi.python.org/pypi/python-thunderborg
   :alt: License

.. image:: https://img.shields.io/pypi/v/python-thunderborg.svg
   :target: https://pypi.python.org/project/python-thunderborg
   :alt: PyPi Version

.. image:: http://img.shields.io/pypi/pyversions/python-thunderborg.svg
   :target: https://pypi.python.org/project/python-thunderborg
   :alt: Python Versions

.. image:: http://img.shields.io/pypi/wheel/python-thunderborg.svg
   :target: https://pypi.python.org/project/python-thunderborg
   :alt: PyPI Wheel


Overview
========

This API for the
`ThunderBorg <https://www.piborg.org/motor-control-1135/thunderborg>`_
board has additional features that the original API does not have.

1. Tested with Python 3.13. All Python 2.x code has been removed.

2. Built in logging to a log file of your choice--**no print statements**.

3. Auto **voltage in** settings.

4. API initialization is done during class instantiation.

5. Flag to initialize the first board that is found if default is not present.


.. warning::

   This version of the **ThunderBorg API** is a complete rewrite of the
   version provided on the
   `PiBorg forums <http://forum.piborg.org/thunderborg/examples>`_.
   It is functionally compatible, but not signature compatible. In other
   words the class and method calls are completely different.

The original code and site are below:

`GitHub <https://github.com/piborg>`_

`Store (Closed as of 2026) <https://www.piborg.org/>`_


Provides
========

An API (Application Programming Interface) for the ThunderBorg motor
controller boards.

`Installation Guide <INSTALL.rst>`_

`Testing Guide <tborg/tests/README.rst>`_

`Pair bluetooth Wireless Controller <PAIR-BT.rst>`_

Feel free to contact me at: carl dot nobile at gmail.com

Complete Documentation can be found on
`Read the Docs <https://readthedocs.org/>`_ at:
`Thunder Borg <http://python-thunderborg.readthedocs.io/en/latest/>`_
