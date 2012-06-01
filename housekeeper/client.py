#!/usr/bin/python
# Copyright (c) 2011 Tuenti Technologies
# See LICENSE for details

import os
import os.path
import socket

from keyring.backend import KeyringBackend

#TODO: Better exceptions
class HousekeeperClientException(Exception): pass

if os.environ.has_key('HOUSEKEEPER_SOCKET'):
    default_socket = os.environ['HOUSEKEEPER_SOCKET']
else:
    default_socket = os.path.expanduser('~/.housekeeper/socket')

class HousekeeperClient:
    def __init__(self, socketfile=default_socket):
        self.socketfile = socketfile

    def __request(self, cmd):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self.socketfile)
        f = s.makefile('wr')
        f.write(cmd + '\r\n')
        f.flush()
        ret = f.read().strip().split('\r\n')

        if len(ret) == 1:
            if ret[0] == 'OK':
                return
            else:
                raise HousekeeperClientException
        else:
            response, result_code = ret
            s.close()
            if result_code == 'OK':
                return response
            else:
                raise HousekeeperClientException(response)

    def set(self, service, password, timeout=-1):
        cmd = "SET %s %s" % (service, password)
        if timeout >= 0:
            cmd += " %d" % timeout
        self.__request(cmd)

    def get(self, service):
        return self.__request("GET %s" % service)

class HousekeeperKeyringBackend(KeyringBackend):
    def __init__(self, socketfile=default_socket, timeout=600):
        self.socketfile = socketfile
        self.client = HousekeeperClient(socketfile)
        self.timeout = timeout

    def supported(self):
        if os.path.exists(self.socketfile):
            return 1
        else:
            return -1

    def get_password(self, service, username):
        try:
            return self.client.get("%s@%s" % (username, service))
        except HousekeeperClientException:
            return ''

    def set_password(self, service, username, password):
        self.client.set("%s@%s" % (username, service), password, self.timeout)
        return 0
