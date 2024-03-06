from unittest.mock import patch

from flask_testing import TestCase
from storage_api import main
from storage_api.exceptions import ApplicationError


class TestExceptions(TestCase):

    def create_app(self):
        return main.app

    @patch('storage_api.exceptions.current_app')
    def test_application_error_init_default_http_code(self, mock_app):
        error = ApplicationError("test message", "abc")

        self.assertEqual(error.message, "test message")
        self.assertEqual(error.code, "abc")
        self.assertEqual(error.http_code, 500)

    @patch('storage_api.exceptions.current_app')
    def test_application_error_init_set_http_code(self, mock_app):
        error = ApplicationError("test message", "abc", 400)

        self.assertEqual(error.message, "test message")
        self.assertEqual(error.code, "abc")
        self.assertEqual(error.http_code, 400)
