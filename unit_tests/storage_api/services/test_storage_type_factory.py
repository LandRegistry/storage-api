from unittest.mock import patch

from flask_testing import TestCase
from storage_api import main
from storage_api.dependencies import storage_type_factory
from storage_api.dependencies.storage.file_storage_adapter import \
    FileStorageAdapter
from storage_api.dependencies.storage.s3_storage_adapter import \
    S3StorageAdapter


class TestStorageTypeFactory(TestCase):
    def create_app(self):
        return main.app

    def test_file_service(self):
        main.app.config["STORAGE_TYPE"] = "file"
        result = storage_type_factory.get_storage_type()
        self.assertTrue(type(result) is FileStorageAdapter)

    @patch('storage_api.dependencies.storage.s3_storage_adapter.boto3')
    def test_s3service(self, mock_s3):
        main.app.config["STORAGE_TYPE"] = "s3"
        result = storage_type_factory.get_storage_type()
        self.assertTrue(type(result) is S3StorageAdapter)

    def test_not_implemented(self):
        main.app.config["STORAGE_TYPE"] = "abc"
        try:
            storage_type_factory.get_storage_type()
            self.fail('Exception should have been thrown')
        except Exception as ex:
            self.assertTrue(type(ex) is NotImplementedError)
            self.assertTrue(True)
