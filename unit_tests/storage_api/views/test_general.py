from flask import url_for
from flask_testing import TestCase
from storage_api import main


class TestGeneral(TestCase):

    def create_app(self):
        return main.app

    def test_check_status(self):
        """Should respond with a 200."""
        response = self.client.get(url_for('general.check_status'))

        self.assert_status(response, 200)
