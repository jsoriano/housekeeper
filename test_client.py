import time

from housekeeper import HousekeeperClient

c = HousekeeperClient()
c.set('mercurial', 'fooobar')
print c.get('mercurial')
c.set('mercurial', 'stuff', 1)
print c.get('mercurial')
time.sleep(3)
print c.get('mercurial')
