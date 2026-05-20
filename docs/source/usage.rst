.. -*-coding: utf-8-*-

*****
Usage
*****

Using the API
-------------

To get started let's use the command line interface ``ipython``. You will
need to import and instantiate the ``ThunderBorg`` class. First we need to
start ``ipython``. You can exit ``ipython`` by pressing ``Ctl d`` then
press the ``Enter`` key.

.. code-block:: console

    $ ipython
    Python 3.13.13 (main, Apr  8 2026, 09:49:30) [GCC 13.3.0]
    Type 'copyright', 'credits' or 'license' for more information
    IPython 9.13.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]:

.. code-block:: ipython

    In [1]: from tborg import ThunderBorg

    In [2]: tb = ThunderBorg()
    ERROR:root:ThunderBorg not found on bus 1 at address 0x15
    ERROR:root:ThunderBorg not found on bus 0 at address 0x15
    ERROR:root:ThunderBorg could not be found; is it properly attached, the correct address used, and the I2C driver module loaded?

Opps, what happened? Well there are two issues here. The first one is easy
to fix. You run this on your computer or a Raspberry Pi with no ThunderBorg
board attached, duh. The second issue is a bit more subtle. Log messages are
going to the screen. How do we get them in a file for later use.

We'll do the import again, but this time with the ``ConfigLogger`` class,
but first we need to create a directory to put the log files in then
restart ``ipython``.

.. code-block:: console

    $ mkdir logs
    $ ipython
    Python 3.13.13 (main, Apr  8 2026, 09:49:30) [GCC 13.3.0]
    Type 'copyright', 'credits' or 'license' for more information
    IPython 9.13.0 -- An enhanced Interactive Python. Type '?' for help.

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

Okay, so that seemed to work, let's look at the log file. By-the-way the
``ConfigLogger`` sets up a logger for the API to use. It can set up
multiple loggers. The only connection between the logger and the API is
the ``logger_name``. So the API needs to know which logger to use. That's
why you see it in both the ``ConfigLogger.config()`` and the
``ThunderBorg.__init__``.

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

And that's it. Look through the `API documentation <tborg.html>`_ for all
the commands available.

Using the Examples
------------------

There are currently three examples.

1. Controlling the motors with the approxeng package. This is a third party
   package designed specifically for robotics. It's light weight and has lots
   of features. This is the
   `approxeng.input <https://github.com/ApproxEng/approxeng.input>`_ GitHub
   repository.

2. Controlling the motors with the pygame package. This is a big bulky API
   really meant for developing games, but has code for controllers. This is
   their `documentation <https://www.pygame.org/docs/>`_. I have not done a lot
   of testing with pygame, so you may find more bug in it. If you do please let
   me know so I can fix them.

3. Controlling the motors through a web interface using the camera. This has
   similar functionality to the original example code written by the developers
   of the MomnsterBorg robot. It is completely rewritten and updated and can be
   run as the user instead of root since it uses port 9000 not 80. This can be
   changed in the code. If the hostname is MonsterBorg you would assess the
   service with: ``http:MonsterBorg.local:9000`` which would give you the
   `index.html`. With this page you need to start the motors with one button
   then stop them with another button. Another method to assess the service is
   with: ``http:MonsterBorg.local:9000/hold``. The second method allows you to
   hold the buttons down to move or turn, when the button is released the
   motors automatically stop.

All of these examples have bash startup scripts which can be put into a cron
job. You would never want to run the one for approxeng and pygame packages
together, but you can run either one of those with the web example making it
easy to switch between a controller and the web interface.

.. code-block:: console

   @reboot /home/<your user name>/<path to project>/tborg/scripts/start_mborg_approxeng.sh

The <path to project> can either be in your virtual environment or if you have
a GitHub clone it will be in there. You could also copy the scrips you want to
your user's bin directory. All three files will write a log file to `/tmp`
which will have nothing in them if the crontab worked correctly.

The above line would be put into your user's crontab file using the command
below.

.. code-block:: console

   $ crontab -e
