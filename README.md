Housekeeper, simple agent for password caching
==============================================

This project contains an agent that can be run to cache password of other
programs and a client library to use the agent.

It requires python-daemon and python-keyring to run.


Features
--------

* Minimal dependencies, only python 2.X and python-daemon
* Stores used passwords in memory, it doesn't use any keyring in filesystem
* Can be reset with SIGUSR1 or replaced with -r
* Stored keys have an expiration time, by default they expire in 10 minutes
* Can generate environment configuration easily sourceable from shell scripts
  or profile
* It's kept alive between sessions
* Implements backend for python keyring


Installation
-----------

If you got housekeeper as a source package, you can build it as egg or deb.

To build it as an egg, run:

    python setup.py bdist_egg

To build it as a debian package:

    dpkg-buildpackage


Usage
-----

Housekeeper can be used to temporary cache passowords you frequently use
in your sessions. For that, you need a running housekeeper daemon and your
application has to be able to talk with it. If you're interested in develop
an application that makes use of housekeeper, go to the next section.

`housekeeper` is the command used to start the daemon, run housekeeper -h to
see the complete list of available parameters. It always outputs the needed
environment configuration for your shell, so you can eval it, it also can
write with -e a file that you can source. The recommended usage is to run
it when starting your shell session, e.g. adding this lines to your .profile:

    if [[ -e $HOME/.housekeeper/env ]]; then
        . $HOME/.housekeeper/env
    else
        eval $(housekeeper --write-env-file --replace)
    fi

By default it writes the env file and other runtime information, as the
pidfile in $HOME/.housekeeper, but you can also use -d to specify another
directory.


Development
-----------

housekeeper basically implements a two command protocol to store and retrieve
keys from its internal cache in memory, the commands are:

    SET <service> <password> [<timeout>]

    GET <service>

SET is used to store a <password> for a <service> and GET to retrieve it, you
can specify a <timeout> in seconds when storing the password to make it expire
after so many seconds without being used. Only a 1 minute granularity is
guaranteed.

To connect with the daemon you have to use the socket file shown in the output
of the daemon, this file is in the running directory and is called `socket`, by
default: $HOME/.housekeeper/socket, a client application should use the
`HOUSEKEEPER_SOCKET` environment variable to find this socket file.

housekeeper also provides a client-side python API with two convenience methods
mapped to those commands, you can find an example of the use of this API in
examples/test_client.py, but basically:

    from housekeeper.client import HousekeeperClient

    client = HousekeeperClient()
    client.set('mercurial', 'foobar', timeout=3600)
    print client.get('mercurial')

It also provides a backend for python keyring module, to use it:

    import keyring

    from housekeeper.client import HousekeeperKeyringBackend

    housekeeper = HousekeeperKeyringBackend(timeout=3600)
    keyring.set_keyring(housekeeper)

Timeout is always optional and it's always defaulted to 600 seconds, if you set
it to 0, the key never expires.
