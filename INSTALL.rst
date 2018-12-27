***************************************
Installing a Virtual Python Environment
***************************************

Why a Virtual Environment
=========================

Python virtual environments are used regularly by seasoned Python
programmers however, beginners may not know about this feature rich
tool. Virtualenv is a tool which allows the creation of isolated python
environments. So what do we get from isolated environments? Lets say you
are developing a project that needs version 1 of some library. You install
it globally on the RPI. A while later you start work on another project
that requires the same library, but version 2 this time. If you install
version 2 globally, as you did before, it will invalidate the first
project you were working on. This is where virtual environments comes to
the rescue, every project is in it's own isolated environment and you no
longer need to install python packages as sudo (root) user.

Although this API will work with Python version 2.7.x I strongly recommend
writing any new code using Python 3.4 or higher. The Python 2.x versions
are quickly coming to their end of life as you can see here at
`Python Clock <https://pythonclock.org/>`_.

Building a Development Environment for Your Projects
====================================================

First you will need to log into your Raspberry Pi with ssh. There are many
good tutorials online that explain how to do this.

As the `pi` user on your Raspberry Pi you will need to install a few
system packages. I'm assuming you have installed Raspian Stretch.

Change the below packages to the Python 2.x versions where
appropriate.

.. code-block:: console

   $ sudo apt install build-essential python3-dev python3-setuptools

Install the Python virtual environment. The ``pip`` utility can be used to
install packages for either ``python2`` or ``python3`` there is no need to
install ``pip`` for both python versions. This is also true for the virtual
environment package which can create virtual environments for either
version of Python. The ``virtualenvwrapper`` package is a wrapper around
``virtualenv`` that provides easy to use tools for ``virtualenv`` and will
install ``virtualenv`` for you.

.. note::

   A directory is created in the user's home directory named
   ``.virtualenvs``. In there you'll be able to find all your projects and
   the packages you have installed for each of them.

.. code-block:: console

    $ sudo easy_install3 pip
    # Newer systems no longer have `easy_install` for Python 2 or 3
    # installed, however, I have found command below to work.
    $ sudo python3 /usr/lib/python3/dist-packages/easy_install.py pip
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

Create a VE (Virtual Environment) for your project. The VE name can be
whatever you want and does not need to match the actual project's name,
but it might be a good idea to keep it short so that you can remember it.

.. code-block:: console

    $ cd /path/to/your/project
    $ mkvirtualenv your_project # mkvirtualenv -p python2 your_project

After the initial creation of the VE you can use these commands to activate
and deactivate a VE.

.. code-block:: console

    $ workon your_project
    $ deactivate

Next you will need to install all the Python packages that your project
depends on. Many of them will be in the pip repository at
`PyPi Repository <https://pypi.org/>`_. I recommend installing
``ipython``, it has a much better command line interface than the one you
get from ``Python`` itself.


To install ``python-thunderborg`` enter the following on the command line.
Be sure your virtual environment is activated before doing this.

.. code-block:: console

    $ pip install git+https://github.com/cnobile2012/python-thunderborg.git
    $ pip install ipython

Eventually you will be able to install ``python-thunderborg`` from PyPi
also.
