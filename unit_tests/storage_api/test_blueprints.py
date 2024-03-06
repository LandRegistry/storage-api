from unittest import TestCase
from unittest.mock import Mock, patch

from storage_api import blueprints


class TestBlueprints(TestCase):

    @patch('storage_api.blueprints.general')
    @patch('storage_api.blueprints.storage_v1_0')
    def test_register_blueprints(self, storage_mock, general_mock):
        """Should register the expected blueprints."""
        app_mock = Mock()
        app_mock.register_blueprint = Mock()

        blueprints.register_blueprints(app_mock)

        app_mock.register_blueprint.assert_any_call(storage_mock.storage_bp, url_prefix='/v1.0/storage')
        app_mock.register_blueprint.assert_any_call(general_mock.general)
