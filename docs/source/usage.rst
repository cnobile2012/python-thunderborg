*****
Usage
*****

To get started let's use the command line interface ``ipython``. You will
need to import and instantiate the ``ThunderBorg`` class. First we need to
start ``ipython``. You can exit ``ipython`` by pressing ``Ctl d`` then
press the ``Enter`` key.

.. code-block:: console

    $ ipython
    Python 3.5.2 (default, Sep 14 2017, 22:51:06)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 6.4.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]:

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

We'll do the import again, but this time with the ``ConfigLogger`` class,
but first we need to create a directory to put the log files in then
restart ``ipython``.

.. code-block:: console

    $ mkdir logs
    $ ipython
    Python 3.5.2 (default, Sep 14 2017, 22:51:06)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 6.4.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]:

.. code-block:: ipython

    In [1]: import logging

    In [2]: from tborg import ThunderBorg, ConfigLogger

    In [3]: cl = ConfigLogger(log_path='logs')

    In [4]: cl.config(logger_name='thunder-borg',
                      filename='thunderborg.log',
                      level=logging.DEBUG)

    In [5]: tb = ThunderBorg(logger_name='thunder-borg',
                             log_level=logging.DEBUG)

Okay, so that seemed to work, let's look at the log file.

.. code-block:: console

    $ cat logs/thunderborg.log

    2018-06-01 01:26:05,073 DEBUG thunder-borg _is_thunder_borg_board [line:220] Loading ThunderBorg on bus number 1, address 0x15
    2018-06-01 01:26:05,076 INFO thunder-borg _check_board_chip [line:277] Found ThunderBorg on bus '1' at address 0x15.

That looks better.

Now lets get the motors turning. Start up ``ipython`` again then reenter
the commands above, then add the command below and both motors should be
running. When they run for as long as you would like execute the final
command to halt the motors.

.. code-block:: ipython

    In [6]: tb.set_both_motors(0.5)

    In [7]: tb.halt_motors()

And that's it. Look through the API documentation for all the commands
available.
