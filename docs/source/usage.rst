*****
Usage
*****

To get started lets use the command line interface ``ipython``. You will
need to import and instantiate the ``ThunderBorg`` class.

.. code-block:: ipython

    In [1]: from tborg import ThunderBorg

    In [2]: tb = ThunderBorg()
    ERROR:root:ThunderBorg not found on bus 1 at address 0x15
    ERROR:root:ThunderBorg not found on bus 0 at address 0x15
    ERROR:root:ThunderBorg could not be found; is it properly attached, the correct address used, and the I2C driver module loaded?

Opps, what happend? Well there are two issues here. The first one is easy
to fix. Don't run this on your computer or a Reaspberry Pi with no
ThunderBorg board attached, duh. The second issue is a bit more subtle.
Log messages are going to the screen. How do we get them in a file for
later use.

Well do the import again, but this time with the ``ConfigLogger`` class.

.. code-block:: ipython

    In [1]: import logging

    In [2]: from tborg import ThunderBorg, ConfigLogger

    In [3]: cl = ConfigLogger(log_path='logs')

    In [4]: cl.config(logger_name='thunder-borg',
                      filename='thunderborg.log',
                      level=logging.DEBUG)

    In [5]: tb = ThunderBorg(logger_name='thunder-borg',
                             log_level=logging.DEBUG)

Okay, so that seemed to work, let's see.

.. code-block:: console

    $ cat logs/thunderborg.log

    2018-05-30 21:46:40,598 DEBUG thunderborg _is_thunder_borg_board [line:220] Loading ThunderBorg on bus number 1, address 0x15
    2018-05-30 21:46:40,606 ERROR thunderborg _initialize_board [line:189] ThunderBorg not found on bus 1 at address 0x15
    2018-05-30 21:46:40,607 DEBUG thunderborg _is_thunder_borg_board [line:220] Loading ThunderBorg on bus number 1, address 0x15
    2018-05-30 21:46:40,615 ERROR thunderborg _initialize_board [line:198] ThunderBorg not found on bus 0 at address 0x15
    2018-05-30 21:46:40,615 ERROR thunderborg _initialize_board [line:208] ThunderBorg could not be found; is it properly attached, the correct address used, and the I2C driver module loaded?



