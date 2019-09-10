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

A software load balancer for your Django database.

Why?
====

Often times you are using ProxySQL in conjunction with a highly available MySQL
server cluster. It would not make sense to use just a single ProxySQL instance.
You may wish to have an active / active ProxySQL cluster in this case. However
normal Django multidb does not smoothly handle failure of one of the ProxySQL
nodes. This engine does. When one of your configured ProxySQL servers refuses
a connection, it is marked down for a period of time before being retried.
Meanwhile all remaining ProxySQL servers are used without interruption.

How?
====

Configure your ProxySQL servers as additional databases django databases. Then
configure your `default` django database to use this engine and specify the
peers.


.. code:: python

    DATABASES = {
        'default': {
            'ENGINE': 'backends.proxysql',
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

Now when you use your database in Django, connections will be randomly
distributed to the peers. Failure of a peer is transparent to Django. Failed
peers will recover after the configured `CHECK_INTERVAL`.

Anything Else?
==============

Yes, to perform maintenance on a ProxySQL instance, just connect to it's admin
port, `6032` and issue a `PROXYSQL PAUSE` command. This will start refusing new
clients, but allow running queries to complete. `django-proxysql` will detect
the "failure" of the node and stop attempting to connect to it. Once all active
connections are drained, you can stop ProxySQL, perform maintenance then
restore the service. You can repeat this for each instance of ProxySQL without
any downtime.
