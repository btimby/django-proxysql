from unittest import mock
from datetime import datetime, timedelta

from freezegun import freeze_time
from MySQLdb._exceptions import OperationalError

from django.test import SimpleTestCase
from django.db import connection
from django.db.utils import DatabaseError, DEFAULT_DB_ALIAS


class ProxySQLTestCase(SimpleTestCase):
    @classmethod
    def _add_databases_failures(cls):
        """Django tests lock you out of the database unless a test database is
        created. We don't need a test database since we are not actually
        connecting to anything. Overriding this class disables the lockout so
        we can call connect()."""
        pass

    @classmethod
    def _remove_databases_failures(cls):
        "Overridden to match above."
        pass

    def assertItemsEqual(self, left, right):
        self.assertEqual(sorted(left), sorted(right))


class PeerTestCase(ProxySQLTestCase):
    def setUp(self):
        "Reset peer state between each test."
        connection.state.reset()

    @mock.patch('MySQLdb.connect')
    def test_connect_all_down(self, mock_connect):
        "Ensure an error is raised when all peers are down."
        mock_connect.side_effect = OperationalError()

        # If all servers are down, we should raise an exception:
        with self.assertRaises(DatabaseError):
            connection.connect()

        # No peers should be up.
        self.assertEqual(len(connection.state.peers_up), 0)

    @mock.patch('MySQLdb.connect')
    def test_connect_one_down(self, mock_connect):
        "Ensure that connect() works when a peer is down but another is up."
        mock_connect.side_effect = [OperationalError(), mock.MagicMock()]

        # If any server is up, connect() should succeed.
        connection.connect()

        # One peer should be up, and one down.
        self.assertEqual(len(connection.state.peers_up), 1)
        self.assertEqual(len(connection.state.peers_down), 1)

    @mock.patch('MySQLdb.connect')
    def test_connect_recovery(self, mock_connect):
        "Ensure that a peer is retried after check_interval passes."
        mock_connect.side_effect = [
            OperationalError(), mock.MagicMock(), mock.MagicMock()]

        # If any server is up, connect() should succeed.
        connection.connect()

        # One peer should be up, and one down.
        self.assertEqual(len(connection.state.peers_up), 1)
        self.assertEqual(len(connection.state.peers_down), 1)

        # FFWD time, our failed server should be retried.
        future = datetime.now() + timedelta(
            seconds=connection.state.check_interval)
        with freeze_time(future):
            connection.connect()

        # all peers should be up once again.
        self.assertItemsEqual(connection.state.peers_up, connection.state.peers)
