from housekeeper import HousekeeperClient

c = HousekeeperClient()
c.set('mercurial', 'fooobar')
print c.get('mercurial')
c.set('mercurial', 'stuff', 10)
print c.get('mercurial')
