***************************************
Installing a Virtual Python Environment
***************************************

Why a Virtual Environment
=========================

Python virtual environments are used regularly by seasoned Python
programmers however, beginners may not know about this feature rich
tool. Virtualenv is a tool which allows the creation of isolated python
environments. So what do we get from isolated environments? Lets say you
are developing a project that needs virsion 1 or some library. You install
it globally on the RPI. A while later you start work on another project
that requires the same library, but version 2. If you install this
globally it will invalidate the first project you were working on. This is
where virtual environments comes to the rescue.


Building a Development Environment
==================================

As the `pi` user on your Raspberry Pi you will need to install a few
system packages. I'm assuming you have installed Raspian Stretch. There
will be a few system packages that may need to be installed first. Change
to Python version 2.x where appropriate if needed.

Although this API will work with Python version 2.7.x I strongly recommend
writing any new code using Python 3.4 or higher. The Python 2.x versions
are quickly coming to their end of life as you can see here at the
`Python Clock <https://pythonclock.org/>`_.

```bash
$ sudo apt install build-essential python3-dev
```

Install the Python virtual environment. The `pip` utility can be used to
install packages for either `python2` or `python3` there is no need to
install `pip` for both python versions. This is also true for the virtual
environment package which can create virtual environments for either
version of Python. The virtualenvwrapper package is a wrapper around
virtualenv that provides easy to use tools for virtualenv and will install
virtualenv for you.

```bash
$ sudo easy_install3 pip
$ sudo -H pip3 install virtualenvwrapper
```

Configure `.bashrc` to auto load the `virtualenvwrapper` package.

```bash
$ nano .bashrc
```

Then add the following line to the botton of the `.bashrc` file.

```bash
# Setup the Python virtual environment.
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
```

Create a virtual environment for your project.

```bash
$ cd /path/to/your/project
$ mkvirtualenv -p python3 your_project
```

After the initial creation of the VE you can use these commands to activate
and deactivate a VE.

```bash
$ workon your_project
$ deactivate
```

Next you will need to install all the Python packages that your project
depends on. Many of them will be in the pip repository at
`PyPi Repository <https://pypi.org/>`_.

To install `python-thunderborg` enter the following on the command line.
Be sure your virtual environment is activated before doing this.

```bash
$ pip install git+https://github.com/cnobile2012/python-thunderborg.git
```

Eventually you will be able to install `python-thunderborg` from PyPi
also.

`README <README.rst>`_
