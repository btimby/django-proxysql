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

This project was developed for MySQL and it's kin, but could be used with any
Django compatible database engine. Most likely the connection error detection
would need to be adapted (as ``MySQLdb.Error`` is used to detect failure).

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
route queries, that is left to ProxySQL.

If you are running a Galera cluster and you are not interested in read / write
split, this database engine can be used in place of a load balancer. Just
configure your Galera nodes as peers.

How?
====

Configure your MySQL peers as additional databases in Django settings. Then
configure your ``default`` django database to use this engine and specify the
peers.


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
distributed to the peers. Failure of a peer is transparent to Django. Failed
peers will recover after the configured `CHECK_INTERVAL`.

Anything Else?
==============

Yes, to perform maintenance on a ProxySQL instance, just connect to it's admin
port, ``6032`` and issue a ``PROXYSQL PAUSE`` command. This will start refusing
new clients, but allow running queries to complete. `django-proxysql` will
detect the "failure" of the node and stop attempting to connect to it. Once all
active connections are drained, you can stop ProxySQL, perform maintenance then
restore the service. You can repeat this for each instance of ProxySQL without
any downtime.

Also note that when migrations are applied, Django performs a check of ALL
CONFIGURED DATABASES. This means that all peers must be online in order for
migrations to succeed.
