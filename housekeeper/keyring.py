#!/usr/bin/python
# Copyright (c) 2012 Tuenti Technologies
# See LICENSE for details

import os
import os.path
import signal
import sys
import daemon
try:
    import daemon.pidlockfile as pidlockfile
except:
    import daemon.pidfile as pidlockfile
import threading
import time
import socket

class MissingKeyException(Exception): pass
class InvalidKeyException(Exception): pass
class InvalidCommandException(Exception): pass


class HousekeeperKeyring:
    def __init__(self):
        self.keys_lock = threading.Lock()
        self.reset()

    def reset(self):
        self.keys_lock.acquire()
        self.keys = {}
        self.keys_lock.release()

    def check_expiration(self, service=None):
        def check(key):
            if key['expiration'] and key['expiration'] < time.time():
                del self.keys[service]

        self.keys_lock.acquire()
        if service:
            if service in self.keys:
                check(self.keys[service])
        else:
            services = self.keys.keys()
            for service in services:
                check(self.keys[service])
        self.keys_lock.release()

    def set_key(self, service, key, timeout=600):
        if not service or not key or timeout < 0:
            raise InvalidKeyException()

        self.keys_lock.acquire()
        self.keys[service] = {
            'key': key,
            'expiration': time.time() + timeout,
            'timeout': timeout,
        }
        self.keys_lock.release()

    def get_key(self, service):
        self.check_expiration(service)
        self.keys_lock.acquire()
        try:
            if self.keys.has_key(service):
                key = self.keys[service]
                key['expiration'] = time.time() + key['timeout']
                result = key['key']
            else:
                raise MissingKeyException("No key for '%s' service" % service)
        finally:
            self.keys_lock.release()
        return result
        

class HousekeeperDaemon(daemon.DaemonContext):
    def __init__(self, directory=os.path.expanduser('~/.housekeeper'), write_envfile=False, replace=True):
        self.directory = directory
        self.pidfile = os.path.join(directory, 'pid')
        self.envfile = os.path.join(directory, 'env')
        self.socketfile = os.path.join(directory, 'socket')
        self.keyring = HousekeeperKeyring()
        self.write_envfile = write_envfile
        self.replace = replace

        self.__startup()

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.env_content = "HOUSEKEEPER_SOCKET='%s'; export HOUSEKEEPER_SOCKET;" % self.socketfile
        print self.env_content
        sys.stdout.flush()

        super(HousekeeperDaemon, self).__init__(
            working_directory = self.directory,
            pidfile = pidlockfile.PIDLockFile(self.pidfile),
            detach_process = True,
        )

        self.signal_map = {
            signal.SIGTERM: 'terminate',
            signal.SIGHUP: None,
            signal.SIGUSR1: self.reset_keyring,
        }
        
    def __startup(self):
        # Check if daemon already running
        if os.path.isfile(self.pidfile):
            try:
                pid = int(open(self.pidfile).read())
                # Check For the existence of a unix pid.
                os.kill(pid, 0)
            except (OSError, ValueError):
                sys.stderr.write("Removing stale locking file: %s\n" % self.pidfile)
                os.unlink(self.pidfile)
            else:
                if self.replace:
                    sys.stderr.write("Replacing daemon PID: %d\n" % pid)
                    os.kill(pid, signal.SIGTERM)
                else:
                    sys.stderr.write("Daemon already running PID: %d\n" % pid)
                    exit(1)

    def __check_expiration(self):
        class Checker(threading.Thread):
            def __init__(self, keyring):
                super(Checker, self).__init__()
                self.keyring = keyring
                self.event = threading.Event()
                # TODO: Kill the thread with stop() instead of with self.daemon
                self.daemon = True

            def run(self):
                while not self.event.isSet():
                    self.keyring.check_expiration()
                    self.event.wait(60)

            def stop(self):
                self.event.set()

        return Checker(self.keyring)

    def reset_keyring(self):
        self.keyring.reset()

    def handle_command(self, command):
        tokens = command.split(' ')
        if tokens[0] == 'GET' and len(tokens) == 2:
            return self.keyring.get_key(tokens[1])
        elif tokens[0] == 'SET' and len(tokens) >= 3:
            args = [tokens[1], tokens[2]]
            if len(tokens) > 3:
                args.append(int(tokens[3]))
            self.keyring.set_key(*args)
            return ''
        else:
            raise InvalidCommandException()

    def handle_connection(self, conn):
        socket_file = conn.makefile('rw')
        try:
            command = socket_file.readline()
            response = self.handle_command(command.strip())
            if response:
                socket_file.write(response + '\r\n')
            socket_file.write('OK\r\n')
            socket_file.flush()
            socket_file.close()
        except MissingKeyException:
            socket_file.write('MissingKeyException\r\nERROR\r\n')
        except InvalidKeyException:
            socket_file.write('InvalidKeyException\r\nERROR\r\n')
        except InvalidCommandException:
            socket_file.write('InvalidCommandException\r\nERROR\r\n')
        finally:
            conn.close()

    def close(self):
        if os.path.exists(self.socketfile):
            os.unlink(self.socketfile)
        if os.path.exists(self.envfile):
            os.unlink(self.envfile)
        super(HousekeeperDaemon, self).close()

    def main(self):
        self.open()

        self.checker = self.__check_expiration()
        self.checker.start()

        if os.path.lexists(self.socketfile):
            os.unlink(self.socketfile)

        if self.write_envfile:
            env = open(self.envfile, 'w')
            env.write(self.env_content)
            env.close()

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        umask = os.umask(0077)
        self.socket.bind(self.socketfile)
        umask = os.umask(umask)
        self.socket.listen(1)

        while True:
            conn, addr = self.socket.accept()
            self.handle_connection(conn)



def main():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-d", "--directory",
        dest="directory",
        help="Uses DIRECTORY as working directory",
        metavar="DIRECTORY",
        default=os.path.expanduser('~/.housekeeper'),
    )
    parser.add_option("-e", "--write-env-file",
        dest="write_envfile",
        help="Write environment file in working directory",
        action="store_true",
        default=False,
    )
    parser.add_option("-r", "--replace",
        dest="replace",
        help="Replace running daemon if any",
        action="store_true",
        default=False,
    )

    (options, args) = parser.parse_args()

    daemon = HousekeeperDaemon(
        directory=options.directory,
        write_envfile=options.write_envfile,
        replace=options.replace,
    )
    daemon.main()


if __name__ == "__main__":
    main()

