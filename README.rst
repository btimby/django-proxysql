.. image:: https://travis-ci.org/btimby/django-proxysql.png
   :target: https://travis-ci.org/btimby/django-proxysql

.. image:: https://coveralls.io/repos/github/btimby/django-proxysql/badge.svg?branch=master
   :target: https://coveralls.io/github/btimby/django-proxysql?branch=master

.. image:: https://badge.fury.io/py/django-proxysql.svg
    :target: https://badge.fury.io/py/django-proxysql

django-proxysql
---------------

What?
=====

A software load balancer for your Django database. This project provides a
Django database engine that manages multiple peer database connections and
distributes queries to each equally. It also notes if a peer fails and stops
sending queries to that peer until it recovers.

This project was developed for MySQL, Galera and ProxySQL. However it could be
used with any Django compatible database engine. Most likely the connection
error detection would need to be adapted (as ``MySQLdb.Error`` is used to
detect failure).

``django-proxysql`` can be used without ProxySQL (for instance, your peers
could be Galera cluster nodes), or with a different load balancer such as
MaxScale. You can also combine this with multidb, where your Django router
routes between multiple pools of database peers.

Why?
====

Django multidb support is implemented at a high level. Thus it is not aware of
connection failures. It will continue routing queries to a down host causing
errors.

Some suggest adding a liveness check within the multidb router, but this adds
unecessary overhead. ``django-proxysql`` also routes queries, but at the
database engine level which enables it to identify connection failures and
route queries accordingly.

``django-proxysql`` assumes you are using a pool of peer MySQL, ProxySQL or
MaxScale servers that are all exactly equivalent. It does not intelligently
route queries, that is left to the downstream peers.

How?
====

First install django-proxysql, for example:

.. code:: bash

    pip install django-proxysql

Then configure your MySQL peers as additional databases in Django settings.
Set your ``default`` django database to use this engine and specify the peers.
You can also specify the optional ``CHECK_INTERVAL`` which controls how often a
downed peer is rechecked (30s default).


.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django_proxysql.backends.proxysql',
            'PEERS': ['peer0', 'peer1'],
            'CHECK_INTERVAL': 30,
        },
        'peer0': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer0',
            'PORT': 6033,
        },
        'peer1': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer1',
            'PORT': 6033,
        },
    }

Now when you use the default database in Django, connections will be randomly
distributed to the peers.

If you don't need a dedicated load balancer such as ProxySQL or MaxScale, you
can simply configure your Galera cluster nodes as your peers.

.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django_proxysql.backends.proxysql',
            'PEERS': ['galera0', 'galera1'],
        },
        'peer0': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'galera0',
            'PORT': 6033,
        },
        'peer1': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'galera1',
            'PORT': 6033,
        },
    }


You can configure more than one ``django-proxysql`` backend and then use Django
multidb to route between those.

.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django_proxysql.backends.proxysql',
            'PEERS': ['peer0', 'peer1'],
        },
        'users': {
            'ENGINE': 'django_proxysql.backends.proxysql',
            'PEERS': ['peer2', 'peer3'],
        },
        'peer0': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer0',
            'PORT': 6033,
        },
        'peer1': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer1',
            'PORT': 6033,
        },
        'peer2': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer2',
            'PORT': 6033,
        },
        'peer3': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'db_name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'peer3',
            'PORT': 6033,
        },
    }


Anything Else?
==============

Because only connection errors are handled by the engine, other errors like
dropped connections will cause failures in your application. Therefore if you
are performing a rolling upgrade, you must gracefully drain each peer. For
example, with ProxySQL you can do this by issuing the ``PROXYSQL PAUSE``
command within the admin interface (port 6032). This causes ProxySQL to stop
accepting new connections, which ``django-proxysql`` will detect and handle
without a single error.

Also note that when migrations are applied, Django performs a check of ALL
CONFIGURED DATABASES. This bears repeating. All database peers must be online
in order to perform database migrations.

Compatability
=============

+--------------------------------------------+
| Python                                     |
+====================+=====+=====+=====+=====+
|                    | 2.7 | 3.5 | 3.6 | 3.7 |
+-------------+------+-----+-----+-----+-----+
| Django      | 1.10 |  O  |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+
|             | 1.11 |  O  |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+
|             | 2.0  |     |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+
|             | 2.1  |     |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+
|             | 2.2  |     |  O  |  O  |  O  |
+-------------+------+-----+-----+-----+-----+
