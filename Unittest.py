import unittest
import pysftp
from unittest.mock import patch, Mock
from agileproject import user_request

class TestApp(unittest.TestCase):
    
    @patch('builtins.input', side_effect=['TestServerName', 'TestUser', 'help', 'bye-bye', 'y'])
    @patch('getpass.getpass')
    @patch.object(pysftp, 'Connection')
    def test_ask_help(self, mock_conn, mock_getpass, mock_input):
        mock_getpass.return_value = 'Testpwd'
        mock_conn.return_value.__enter__.return_value.close.return_value = None
        user_request()

    @patch('builtins.input', side_effect=['TestServerName', 'TestUser', 'cd', 'cd', 'testDir', 'bye-bye', 'y'])
    @patch('getpass.getpass')
    @patch.object(pysftp, 'Connection')
    def test_ask_cd(self, mock_conn, mock_getpass, mock_input):
        mock_getpass.return_value = 'Testpwd'
        mock_conn.return_value.__enter__.return_value.isdir.return_value = True
        mock_conn.return_value.__enter__.return_value.cwd.return_value = None
        mock_conn.return_value.__enter__.return_value.close.return_value = None
        user_request()

    @patch('builtins.input', side_effect=['TestServerName', 'TestUser', 'cd', 'cd', 'testDir', 'listloc', 'bye-bye', 'y'])
    @patch('getpass.getpass')
    @patch.object(pysftp, 'Connection')
    def test_ask_listloc(self, mock_conn, mock_getpass, mock_input):
        mock_getpass.return_value = 'Testpwd'
        mock_conn.return_value.__enter__.return_value.isdir.return_value = True
        mock_conn.return_value.__enter__.return_value.cwd.return_value = None
        mock_conn.return_value.__enter__.return_value.close.return_value = None
        user_request()