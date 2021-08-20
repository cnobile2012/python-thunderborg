*******
Testing
*******

First off I'm assuming you have forked this API and want to either
contribute to or derive your own API from it. In either case you will
be building a virtual environment to do your work in.

.. note::

   I usually do most of my work on my laptop and then check it into my
   GitHub account. I'll them check it out on a Raspberry PI to run tests.
   I may do some editing on the RPI and check it in from there, but the
   RPI is a lot slower than my laptop, so I try to keep the work I do on
   the RPI to a minimum. This means you will need to setup a virtual
   environment on all machines that you want to work on. I also make the
   assumption that a Linux system is installed on all of these machines.
   If you use Windows I cannot help you, you can spin up a virtual machine
   on your windows box and install Linux on that if you want.

Creating a Virtual Environment
==============================

From your user account we first need to install a few packages. The below
install assumes a Debian derived OS. I don't generally use Red Hat derived
OSs, but I am sure they have some equivalent packages.

.. code-block:: console

   $ sudo apt install build-essential python3-dev git


Install the Python virtual environment. The ``pip`` utility can be used to
install packages for either ``python2`` or ``python3`` there is no need to
install ``pip`` for both python versions. This is also true for the VE
(virtual environment) package which can create VEs for either version of
Python. The virtualenvwrapper package is a wrapper around virtualenv that
provides easy to use tools for virtualenv and will install virtualenv for
you.

.. code-block:: console

    $ sudo easy_install3 pip
    $ sudo -H pip3 install virtualenvwrapper

Configure ``.bashrc`` to auto load the ``virtualenvwrapper`` package.

.. code-block:: console

    $ nano .bashrc

Then add the following lines to the bottom of the ``.bashrc`` file.

.. code-block:: bash

    # Setup the Python virtual environment.
    VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    source /usr/local/bin/virtualenvwrapper.sh

Download ``python-thunderborg``. First **cd** into the path where you want
to put the package. If you forked the package then change the path
accordingly.

.. code-block:: console

    $ git clone https://github.com/cnobile2012/python-thunderborg.git

Create a VE for ``python-thunderborg``.

.. code-block:: console

    $ cd /path/to/python-thunderborg
    $ mkvirtualenv tborg3 # and/or mkvirtualenv -p python2 tborg2

Next we install the packages required for developing ``python-thunderborg``.

.. code-block:: console

   $ pip install -r requirements/development.txt

After the initial creation of the VE you can use these commands to activate
and deactivate a VE.

.. code-block:: console

    $ workon tborg3 # or workon tborg2
    $ deactivate

Running Tests
=============

The ``Makefile`` in the project's root should be used to run the tests as
it will automatically clean up old coverage reports and HTML documents.

After tests are done running they will dump to the screen a basic coverage
report. You can also point your browser to a more complete HTML report in
``docs/htmlcov/index.html``.

There are three log files in the ``logs`` directory that are created
during the tests one for each test class. They may have minimal use if all
the tests pass, but will be invaluable if any fail.

.. code-block:: console

    $ make tests
    $ make tests TEST_PATH=tborg.tests.test_tborg.TestThunderBorg
    $ make tests TEST_PATH=tborg/tests/test_tborg.py:TestClassMethods.test_set_i2c_address_without_current_address

* The 1st example will run all tests.
* The 2nd example will run tests for a specific class in the
  ``test_tborg.py`` module.
* The 3rd example will run a specific test in the TestClassMethods.

.. note::

   Unittests give software a base line of how it performs under as many
   situations as the author can think of. There are two objectives one
   must keep in mind while writing tests. First is coverage where you want
   to cover as many lines of code as is feasibly possible. However,
   getting 100% coverage does not mean you're done writing tests. The
   second thing you need to write tests for are business rules. Business
   rules are the specific constraints you have decided your software needs
   to follow.
