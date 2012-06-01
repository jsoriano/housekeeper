#!/usr/bin/python
# Copyright (c) 2011 Tuenti Technologies
# See LICENSE for details

import time

from housekeeper.client import HousekeeperClient

c = HousekeeperClient()
c.set('mercurial', 'fooobar')
print c.get('mercurial')
c.set('mercurial', 'stuff', 1)
print c.get('mercurial')
time.sleep(3)
print c.get('mercurial')
