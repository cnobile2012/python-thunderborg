********************************
ThunderBorg Motor Controller API
********************************

.. image:: https://img.shields.io/pypi/pyversions/thunderborg.svg
   :target: https://pypi.python.org/pypi/thunderborg
   :alt: PyPi Versions

.. image:: http://img.shields.io/travis/cnobile2012/thunderborg/master.svg
   :target: http://travis-ci.org/cnobile2012/thunderborg
   :alt: Build Status

The MIT License (MIT)

Overview
========

This API for the `ThunderBorg <https://shop.piborg.org/collections/our-boards/products/thunderborg>`_
board has additional features that the original API does not have.

1. Python 2.7.x and 3.4 and greater are supported in the same code base.

2. Built in logging to a log file of your choice--**no print statements**.

3. Auto **voltage in** settings.

4. API initialization is done during class instantiation.

5. Flag to initialize the first board that is found if default is not present.


.. warning::

   This version of the **ThunderBorg API** is a complete rewrite of the
   version provided by `PiBorg <https://www.piborg.org/monsterborg/install>`_
   It is functionally compatible, but not signature compatible. In other
   words the class and method calls are completely different.

Provides
========

1. An API (Application Programming Interface) for the ThunderBorg motor
   controller boards.

2. TBD

3. TBD


`Installation Guide <INSTALL.rst>`_

`Testing Guide <tborg/tests/README.rst>`_

Feel free to contact me at: carl dot nobile at gmail.com

Complete Documentation can be found on
`Read the Docs <https://readthedocs.org/>`_ at:
`Thunder Borg <http://python-thunderborg.readthedocs.io/en/latest/>`_
