from unittest import TestCase

from storage_api.dependencies.storage.storage_base import StorageBase


class TestStorageBase(TestCase):

    def test_base_can_not_be_initiated(self):
        with self.assertRaises(TypeError):
            StorageBase()

    def test_base_get_file_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.get_file(1, 1)

    def test_base_delete_file_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.delete_file(1, 1)

    def test_base_save_file_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.save_file(1, 1, 1)

    def test_base_is_directory(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.is_directory(1, 1)

    def test_base_zip_directory(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.zip_directory(1, 1, 1, 1)

    def test_get_file_external_url(self):
        with self.assertRaises(NotImplementedError):
            mbase = MockBase()
            mbase.get_file_external_url(1, 1, 1)


class MockBase(StorageBase):
    def get_file_external_url(self, bucket, file_id, subdirectories=None):
        return super(MockBase, self).get_file_external_url(bucket, file_id, subdirectories)

    def is_directory(self, bucket, file_id, subdirectories=None):
        return super(MockBase, self).is_directory(bucket, file_id)

    def zip_directory(self, bucket, file_id, subdirectories, name):
        return super(MockBase, self).zip_directory(bucket, file_id, subdirectories, name)

    def get_file(self, bucket, file_id, subdirectory=None):
        return super(MockBase, self).get_file(bucket, file_id)

    def delete_file(self, bucket, file_id, subdirectories=None):
        return super(MockBase, self).delete_file(bucket, file_id)

    def save_file(self, bucket, storage_item, subdirectories=None, expires=None):
        return super(MockBase, self).save_file(bucket, storage_item, expires)
