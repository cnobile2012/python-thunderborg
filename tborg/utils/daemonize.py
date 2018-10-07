#
# tborg/utils/daemonize.py
#
"""
Daemonization code.

by Carl J. Nobile

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
__docformat__ = "restructuredtext en"

import fcntl
import logging
import os
import pwd
import resource
import stat

from subprocess import check_output

__all__ = ['Daemonize']


class Daemonize(object):
    """
    This class provides utility functionality for daemon processes.
    """
    def __init__(self, lock_file, logger_name=''):
        """
        Constructor

        :param lock_file: The The file to use as the lock file.
        :type lock_file: str
        :param logger_name: The logger name. If none given the root
                            logger is used.
        :type logger_name: str
        """
        self._lock_file = lock_file
        self._fd = None
        self._log = logging.getLogger(logger_name)

    @property
    def is_file_locked(self):
        """
        This method creates a lock file containing the PID if no lock file
        is present and returns False. If the OS has no lock on the file
        False is also returned. True is returned if the OS has a lock on
        the file.

        :rtype: `True` if the daemon is already running or the lock file
                could not be created else `False` if the daemon started.
        :raises IOError: Another process has a lock on this file.
        :raises OSError: Lock file path could not be created.
        """
        result = False
        user = pwd.getpwuid(os.getuid()).pw_name
        #prog_name = os.path.basename(__file__)

        try:
            self._fd = open(self._lock_file, 'w')
            pid = check_output(['pidof', self._lock_file])
            self._fd.write(pid.strip())
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._log.info("Successfully created/locked lock file [%s] "
                           "with file descriptor %s",
                           self._lock_file, self._fd)
        except IOError as e:
            self._log.error("Another process has a lock on this file [%s], %s",
                            self._lock_file, e)
            result = True
        except OSError as e:
            msg = "User [%s] could not create path: %s, %s"
            self._log.error(msg, user, self._lock_file, e)
            result = True

        return result

    def unlock(self):
        """
        Unlock the lock file.
        """
        if self._fd:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except IOError as e:
                self._fd.close()
                self._log.error("The lock file [%s] could not be unlocked, %s",
                                self._lock_file, str(e))
            else:
                self._fd.close()
                self._log.info("Successfully unlocked lock file [%s].",
                                self._lock_file)

    def set_uid_gid(self, files=None):
        """
        Set the effective user and group to the configured value. If the
        configured values are not valid user and group IDs do nothing for
        that ID.

        @keyword files: Can be a list, tuple, or a string of files to
        re-permission.
        """
        user = None
        work_path = os.getcwd()

        try:
            user = pwd.getpwuid(os.getuid()).pw_name

            if user != 'root':
                msg = ("The current user is '%s', it must be 'root'"
                       " to change the effective user and group.")
                self._log.info(msg, user)
            else:
                # Get the user and group IDs of the parent directory
                fileStat = os.stat(work_path)
                uid, gid = fileStat[stat.ST_UID], fileStat[stat.ST_GID]

                # Fix any files.
                if files is not None:
                    if isinstance(files, str): files = files.split(',')

                    for f in files:
                        f = os.path.join(work_path, f)
                        os.chown(f, uid, gid)

                # Now change our group 1st and user 2nd.
                os.setgid(gid)
                os.setuid(uid)
                self._log.info("Set user to [%i] and group to [%i].",
                                uid, gid)
        except (KeyError, OSError) as e:
            msg = "User [%s] could not set the user and/or group ID, %s"
            self._log.warning(msg, user, str(e))

    def daemonize(self):
        """
        Make a daemon by forking twice then clean up the used file
        descriptors, stdin, stdout, and stderr.
        """

        try:
            pid = os.fork()  # Fork a child process so the parent can exit.

            if pid == 0:
                os.setsid()
                pid = os.fork()  # Fork a second child.

                if pid == 0:
                    self.set_uid_gid()
                else:
                    # Exit parent (the first child) of the second child.
                    os._exit(0)
            else:
                # Exit parent of the first child.
                os._exit(0)
        except OSError as e:
            raise TemplateBaseException("%s [%d]" % e.strerror, e.errno)

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]

        if maxfd == resource.RLIM_INFINITY:
            maxfd = 1024

        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:
                # ERROR, fd wasn't open to begin with (ignored)
                pass

        # The standard I/O file descriptors are redirected to /dev/null
        # by default.
        if hasattr(os, "devnull"):
            REDIRECT_TO = os.devnull
        else:
            REDIRECT_TO = "/dev/null"

        os.open(REDIRECT_TO, os.O_RDWR) # standard input (0)
        os.dup2(0, 1)                   # standard output (1)
        os.dup2(0, 2)                   # standard error (2)


if __name__ == '__main__':
    import sys
    import time
    work_path = os.getcwd()
    sys.path.insert(0, work_path)
    from tborg import ConfigLogger

    base_dir = os.path.dirname(os.path.dirname(__file__))
    log_path = os.path.join(base_dir, '..', 'logs')
    not os.path.isdir(log_path) and os.mkdir(log_path, 0o0775)
    lock_file = os.path.abspath(os.path.join(log_path, 'daemonize.lock'))
    #print(lock_file)
    logger_name = 'daemonize'
    d = None

    try:
        logger = ConfigLogger()
        logger.config(logger_name=logger_name, level=logging.DEBUG)
        d = Daemonize(lock_file, logger_name=logger_name)

        if not d.is_file_locked:
            print("Not locked")
            #d.daemonize()

            while True:
                time.sleep(1.0)
        else:
            print("Locked")
            sys.exit(1)
    except Exception as e:
        if d: d.unlock()
        print(e)
    else:
        sys.exit(0)
