#!/usr/bin/python
# Copyright (c) 2012 Tuenti Technologies
# See LICENSE for details

import os
import os.path
import sys

from client import HousekeeperClient, HousekeeperClientException

def get_request():
    request = {}
    while True:
        line = sys.stdin.readline()
        if not line.strip():
            break
        key, value = line.strip().split('=')
        request[key] = value
    return request

def put_response(response):
    for key, value in response.iteritems():
        print "%s=%s" % (key, value)

def main():
    from optparse import OptionParser

    usage = "usage: %prog [options] <action>"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--directory",
        dest="directory",
        help="Uses DIRECTORY as working directory",
        metavar="DIRECTORY",
        default=os.path.expanduser('~/.housekeeper'),
    )
    parser.add_option("-t", "--timeout",
        dest="timeout",
        help="Uses TIMEOUT seconds as timeout (Default: 900)",
        metavar="DIRECTORY",
        type="int",
        default=900,
    )

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        return

    socketfile = os.path.join(options.directory, 'socket')
    action = args[0].strip()

    if not action in ['get', 'set']: return

    request = get_request()
    client = HousekeeperClient(socketfile)

    if not 'username' in request: return

    service = "%s@git" % (request['username'])
    if action == 'get':
        response = request
        try:
            response['password'] = client.get(service)
            put_response(response)
        except HousekeeperClientException:
            pass
    elif action == 'set':
        if not 'password' in request: return
        client.set(service, request['password'], options.timeout)

if __name__ == "__main__":
    main()
