import threading
import random
import logging

from time import time

import MySQLdb

from django.db import connections
from django.db.backends.mysql import base
from django.db.utils import DatabaseError, DEFAULT_DB_ALIAS


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
CHECK_INTERVAL = 30


class PeerState(object):
    """
    Track state of configured MySQL servers.

    When a MySQL server fails to connect it is moved to a list of down peers.
    It is then checked again periodically to see if it has returned. This
    avoids many connection errors if we blindly try each server.
    """

    def __init__(self):
        self.state_lock = threading.Lock()
        self.retry_lock = threading.Lock()
        self.check_interval = None
        self.peers = None
        self.peers_up = None
        self.peers_down = None

    def initialize(self, peers, check_interval):
        "Get settings from settings.DATABASES. Not available during __init__()"
        if self.peers:
            LOGGER.warn('Re-initialization attempted')
            return

        self.check_interval = check_interval
        self.peers = set(peers)
        self.peers_up = set(peers)
        self.peers_down = {}

    def reset(self):
        "Reset all peers to peers_up."
        self.peers_down.clear()
        for peer_name in self.peers:
            self.peers_up.add(peer_name)

    def mark_peer_up(self, peer_name):
        "Remove the named peer from peers_down and add to peers_up."
        with self.state_lock:
            self.peers_down.pop(peer_name)
            self.peers_up.add(peer_name)
        LOGGER.info('Marked peer %s as up', peer_name)

    def mark_peer_down(self, peer_name):
        "Remove the named peer from peers_up and add to peers_down."
        with self.state_lock:
            retry = time() + self.check_interval
            self.peers_up.discard(peer_name)
            self.peers_down[peer_name] = retry
        LOGGER.info('Marked peer %s as down, retry at %s', peer_name, retry)

    def get_peer_connection(self, peer_name):
        "Get a connection to the named peer."
        peer = connections[peer_name]
        peer.connect()
        return peer

    def try_downed_peers(self):
        "Try peers_down and return a live connection (if available)."
        if not self.retry_lock.acquire(False):
            return

        try:
            for peer_name, retry in self.peers_down.items():
                if time() >= retry:
                    # Time to re-check this peer.
                    try:
                        conn = self.get_peer_connection(peer_name)

                    except DatabaseError as e:
                        # Still down.
                        LOGGER.debug(e, exc_info=True)
                        LOGGER.info('Peer %s is still down', peer_name)
                        self.mark_peer_down(peer_name)

                    else:
                        self.mark_peer_up(peer_name)
                        return conn

        finally:
            self.retry_lock.release()

    def get_random_peer(self):
        "Select a random peer and ensure it is alive."
        while True:
            try:
                peer_name = random.sample(self.peers_up, 1)[0]

            except ValueError:
                # No peers up.
                raise DatabaseError('No available peers')

            try:
                return self.get_peer_connection(peer_name)

            except MySQLdb.Error as e:
                LOGGER.info(e, exc_info=True)
                self.mark_peer_down(peer_name)


class DatabaseWrapper(base.DatabaseWrapper):
    "DatabaseWrapper that handles multiple peers."

    # Tracks the state of our peers.
    state = PeerState()

    def __init__(self, settings_dict, alias=DEFAULT_DB_ALIAS):
        "Initialize the base DatabaseWrapper and our peer state."
        super(DatabaseWrapper, self).__init__(settings_dict, alias=alias)
        self.state.initialize(
            settings_dict['PEERS'],
            settings_dict.get('CHECK_INTERVAL', CHECK_INTERVAL))

    def connect(self):
        "Try to connect to a configured peer."
        conn = self.state.try_downed_peers() or self.state.get_random_peer()
        self.connection = conn.connection
