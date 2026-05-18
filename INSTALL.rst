.. -*-coding: utf-8-*-

*******************************************************
Installing a Virtual Environment and python-thunderborg
*******************************************************

Installing a Virtual Python Environment
=======================================

Why a Virtual Environment
-------------------------

Python virtual environments are used regularly by seasoned Python
programmers however, beginners may not know about this feature rich
tool. Virtualenv is a tool which allows the creation of isolated python
environments. So what do we get from isolated environments? Lets say you
are developing a project that needs version 1 of some library. You install
it globally on the RPI. A while later you start work on another project
that requires the same library, but version 2. If you install version 2
globally, as you did before, it will invalidate the first project you were
working on. This is where virtual environments comes to the rescue, every
project is in it's own isolated environment and you no longer need to install
python packages as sudo (root) user. Which means the other advantage of
virtual environments is that it's installed in your user account not in the
root of the system.

Building a Development Environment for your Projects
----------------------------------------------------

First you will need to log into your Raspberry Pi with ssh. There are many
good tutorials online that explain how to do this.

Log into your user account on your Raspberry Pi then you will need to install a
few system packages.

If you will be using pygame instead of approxeng you'll also need to install
the following packages.

.. code-block:: console

    $ sudo apt install python3-dev python3-setuptools python3-numpy \
                       python3-opengl ffmpeg libsdl2-image-2.0-0 \
                       libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libsdl2-dev \
                       libsdl2-mixer-dev libsmpeg-dev libportmidi-dev \
                       libswscale-dev libportmidi-dev libswscale-dev \
                       libavformat-dev libavcodec-dev libtiff5-dev libx11-6 \
                       libx11-dev fluid-soundfont-gm timgm6mb-soundfont \
                       xfonts-base xfonts-100dpi xfonts-75dpi xfonts-cyrillic \
                       fontconfig fonts-freefont-ttf

If you want to use ``tborg/examples/monster_web.py`` you will need to install
the following package. This will install lots of packages so be sure to use
the ``--no-install-recommends`` so you don't get things that are not needed.
There is a problem with this however, in that picamera2 cannot be accessed
within a virtual environment.

.. code-block:: console

    $ sudo apt install python3-picamera2 --no-install-recommends

Some bluetooth packages.

.. code-block:: console

    $ sudo apt install bluez-tools joystick

Install the Python virtual environment. The ``virtualenvwrapper`` package is
a wrapper around ``virtualenv`` that provides easy to use tools for
``virtualenv`` and will install ``virtualenv`` for you.

.. note::

   A directory is created in the user's home directory named ``.virtualenvs``.
   In there you'll be able to find all your project requirements and the
   packages you have installed for each of them.

.. code-block:: console

    $ sudo easy_install3 pip
    # Newer systems no longer have ``easy_install`` for Python 3
    # installed, however, I have found the command below to work.
    $ sudo python3 /usr/lib/python3/dist-packages/setuptools/command/easy_install.py pip
    $ sudo -H pip3 install virtualenvwrapper

Configure ``.bashrc`` in the ``pi`` user directory to auto load the
``virtualenvwrapper`` package.

.. code-block:: console

    $ nano .bashrc

Then add the following lines to the bottom of the ``.bashrc`` file.

.. code-block:: bash

    # Setup the Python virtual environment.
    VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    source /usr/local/bin/virtualenvwrapper.sh

    $ . .bashrc

Create a VE (Virtual Environment) for your project. The VE name can be
whatever you want and does not need to match the actual project's name, but
it might be a good idea to keep it short so that you can remember it. Some of
my scripts expect `tborg3` as the VE name, so if you use a different name you
will need to change the name in the scripts. Also, you can use other versions
of python besides 3.13. The `--system-site-packages` argument below is only
needed if you intend to use the camera.

.. code-block:: console

    $ cd /path/to/your_project
    $ mkvirtualenv -p python3.13 --system-site-packages your_project

After the initial creation of the VE you can use these commands to activate
and deactivate a VE.

.. code-block:: console

    $ workon tborg3  # <your name>
    $ deactivate

Next you will need to install all the Python packages that your project
depends on. Many of them will be in the pip repository at
`PyPi Repository <https://pypi.org/>`_.

Installing python-thunderborg
=============================

To install ``python-thunderborg`` in your virtual environment enter the
following on the command line.

.. code-block:: console

    $ workon tborg3  # <your name>

    $ pip install python-thunderborg
    or
    $ pip install git+https://github.com/cnobile2012/python-thunderborg.git

If you are working on ``python-thunderborg`` itself, then
``python-thunderborg`` is the project you are working on and you'll need to
install the ``development.txt`` file mentioned below. You may want to fork my
version first. This is advanced usage you and will need to have your own git
account for this to work properly.

.. code-block:: console

    $ cd /path/to/where/your/project/will/be/rooted
    $ git clone git@github.com:cnobile2012/python-thunderborg.git

If all the correct system packages have been installed you can now setup the
virtual environment that ``python-thunderborg`` requires.

There are four pip files that can be used ``approxeng.txt``, ``pygame.txt``,
``monsterweb.txt`` or ``development.txt``. Unless you will be mofiying the
``python-thunderborg`` code itself you will not need the ``development.txt``
file. I recommend installing ``ipython``, it has a much better command line
interface than the one you get from ``Python`` itself. The ``development.txt``
installs the other three requierments files and ipython.

.. code-block:: console

    $ workon tborg3  # <your name>
    $ pip install -r requirements/approxeng.txt
    $ pip install ipython # If needed, it's included in development.txt.

That should be it. If you have any issues please check all the instructions
before contacting me.

Example of Setting up an App to Run at Boot
===========================================

This is just an example of how to start an app on reboot my actual code below
will probably not work on your system.

Setup a Cron Job
----------------

Run the ``crontab`` app.

.. code-block:: console

    $ crontab -e

Then add the line below to your user cron file. Remember to change the
<username> to your username.

.. code-block:: bash

    @reboot /home/<username>/bin/start_mborg_approxeng.sh

Copy the ``start_mborg_approxeng.sh`` script.

.. code-block:: console

    $ cd # Make sure you're in your home directory.
    $ mkdir bin
    $ cd /path/to/python-thunderborg
    $ cp scripts/start_mborg_approxeng.sh ~/bin/
