import errno
import io
import os
from unittest.mock import MagicMock, patch

from flask import g
from flask_testing import TestCase
from storage_api import main
from storage_api.dependencies.storage.file_storage_adapter import \
    FileStorageAdapter


def side_effect(*args, **kwargs):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), 'sample.pdf')


mock_file = io.BytesIO(b'testfile')


class TestFileStorageAdapter(TestCase):
    def create_app(self):
        main.app.config["FILE_STORAGE_LOCATION"] = "abc"
        main.app.config["FILE_EXTERNAL_URL_BASE"] = "FILE_EXTERNAL_URL_BASE"
        return main.app

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.walk')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    @patch('storage_api.dependencies.storage.file_storage_adapter.io.open')
    def test_file_storage_adapter_get_file(self, mock_file_open, mock_list_dir, mock_walk):
        mock_list_dir.return_value = ["1.txt"]
        mock_walk.return_value = [
            ('/abc', ('abc',), ('1.txt',))
        ]
        file_mock = MagicMock(wraps=io.StringIO('test'))
        file_mock.name = "test.txt"

        mock_file_open.return_value = file_mock
        file_storage_adapter = FileStorageAdapter()
        storage_item = file_storage_adapter.get_file("abc", "1")
        self.assertEqual(storage_item.file, file_mock)
        self.assertEqual(storage_item.meta_type, 'text/plain')

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.walk')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isfile')
    @patch('storage_api.dependencies.storage.file_storage_adapter.io.open')
    def test_file_storage_adapter_get_file_with_ext(self, mock_file_open, mock_isfile, mock_walk):
        mock_isfile.return_value = True
        mock_walk.return_value = [
            ('/abc', ('abc',), ('1.jpg',))
        ]
        file_mock = MagicMock(wraps=io.StringIO('test'))
        file_mock.name = "test.jpg"

        mock_file_open.return_value = file_mock
        file_storage_adapter = FileStorageAdapter()
        storage_item = file_storage_adapter.get_file("abc", "1.jpg")
        self.assertEqual(storage_item.file, file_mock)
        self.assertEqual(storage_item.meta_type, 'image/jpeg')

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.walk')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    @patch('storage_api.dependencies.storage.file_storage_adapter.io.open')
    def test_file_storage_adapter_get_file_in_subdirectory(self, mock_file_open, mock_list_dir, mock_walk):
        mock_list_dir.return_value = ["1.txt"]
        mock_walk.return_value = [
            ('/abc', ('abc',), ('1.txt',))
        ]
        file_mock = MagicMock(wraps=io.StringIO('test'))
        file_mock.name = "test.txt"

        mock_file_open.return_value = file_mock
        file_storage_adapter = FileStorageAdapter()
        storage_item = file_storage_adapter.get_file("abc", "1", "list,of,subdirectories")

        self.assertEqual(storage_item.file, file_mock)
        self.assertEqual(storage_item.meta_type, 'text/plain')

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    @patch('storage_api.dependencies.storage.file_storage_adapter.io.open')
    def test_file_storage_adapter_get_file_not_found_exception(self, mock_file_open, mock_list_dir):
        with main.app.test_request_context():
            mock_list_dir.return_value = ["1.txt"]
            g.trace_id = "123"
            mock_file_open.side_effect = side_effect
            file_storage_adapter = FileStorageAdapter()
            file = file_storage_adapter.get_file("abc", "1")
            self.assertIsNone(file)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_get_file_empty_directory(self, mock_list_dir):
        mock_list_dir.return_value = []

        file_storage_adapter = FileStorageAdapter()
        storage_item = file_storage_adapter.get_file("abc", "1")
        self.assertIsNone(storage_item)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_get_file_no_matching_file(self, mock_list_dir):
        mock_list_dir.return_value = ["2.txt"]

        file_storage_adapter = FileStorageAdapter()
        storage_item = file_storage_adapter.get_file("abc", "1")
        self.assertIsNone(storage_item)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.remove')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_delete_file_successful(self, mock_list_dir, mock_remove):
        mock_list_dir.return_value = ["1.txt"]

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.delete_file("abc", "1")
        self.assertTrue(result)
        mock_remove.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.remove')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_delete_file_no_matching_file(self, mock_list_dir, mock_remove):
        mock_list_dir.return_value = ["2.txt"]

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.delete_file("abc", "1")
        self.assertFalse(result)
        mock_remove.assert_not_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.remove')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_delete_file_in_subdirectory_successful(self, mock_list_dir, mock_remove):
        mock_list_dir.return_value = ["1.txt"]

        file_mock = MagicMock(wraps=io.StringIO('test'))
        file_mock.name = "test.txt"

        file_storage_adapter = FileStorageAdapter()
        success = file_storage_adapter.delete_file("abc", "1", "list,of,subdirectories")
        self.assertTrue(success)
        mock_remove.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.remove')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.listdir')
    def test_file_storage_adapter_delete_file_exception(self, mock_list_dir, mock_remove):
        with main.app.test_request_context():
            g.trace_id = "123"
            mock_list_dir.return_value = ["1.txt"]
            mock_remove.side_effect = Exception("error")
            file_storage_adapter = FileStorageAdapter()
            result = file_storage_adapter.delete_file("abc", "1")
            self.assertFalse(result)
            mock_remove.return_value.assert_not_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.exists')
    def test_file_storage_adapter_save_file_successful(self, mock_dir):
        mock_file = MagicMock()
        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.save_file("abc", mock_file)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['file_id'])
        self.assertEqual(result['bucket'], 'abc')
        self.assertIsNone(result.get('subdirectory'))
        self.assertEqual(result['reference'], 'abc/{}'.format(result['file_id']))
        mock_dir.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.exists')
    def test_file_storage_adapter_save_file_successful_with_subdirectories(self, mock_dir):
        mock_file = MagicMock()
        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.save_file("abc", mock_file, "list,of,subdirectories")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['file_id'])
        self.assertEqual(result['subdirectory'], 'list,of,subdirectories')
        self.assertEqual(result['bucket'], 'abc')
        mock_dir.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.makedirs')
    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.exists')
    def test_file_storage_adapter_save_file_directory_missing(self, mock_dir, mock_make_dir):
        mock_dir.return_value = False
        mock_file = MagicMock()
        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.save_file("abc", mock_file)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['file_id'])
        self.assertEqual(result['bucket'], 'abc')
        self.assertEqual(result['reference'], 'abc/{}'.format(result['file_id']))
        mock_dir.assert_called()
        mock_make_dir.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.exists')
    def test_file_storage_adapter_save_file_exception(self, mock_dir):
        with main.app.test_request_context():
            g.trace_id = "123"
            with self.assertRaises(IOError):
                mock_dir.side_effect = IOError
                mock_file = MagicMock()
                file_storage_adapter = FileStorageAdapter()
                file_storage_adapter.save_file("abc", mock_file)
                mock_dir.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.FileStorageAdapter.make_directory')
    def test_add_sub_directory_to_path_1_item(self, mock__make_directory):
        actual = FileStorageAdapter.add_sub_directory_to_path("base_path", "subdirectory", False)
        expected = "base_path/subdirectory"
        self.assertEqual(expected, actual)

    @patch('storage_api.dependencies.storage.file_storage_adapter.FileStorageAdapter.make_directory')
    def test_add_sub_directory_to_path_1_item_save_is_true(self, mock__make_directory):
        actual = FileStorageAdapter.add_sub_directory_to_path("base_path", "subdirectory", True)
        expected = "base_path/subdirectory"
        self.assertEqual(expected, actual)
        mock__make_directory.assert_called()

    @patch('storage_api.dependencies.storage.file_storage_adapter.FileStorageAdapter.make_directory')
    def test_add_sub_directory_to_path_multiple_item(self, mock__make_directory):
        actual = FileStorageAdapter.add_sub_directory_to_path("base_path", "this,is,a,subdirectory", False)
        expected = "base_path/this/is/a/subdirectory"
        self.assertEqual(expected, actual)

    @patch('storage_api.dependencies.storage.file_storage_adapter.FileStorageAdapter.make_directory')
    def test_add_sub_directory_to_path_multiple_empty_item(self, mock__make_directory):
        actual = FileStorageAdapter.add_sub_directory_to_path("base_path", ",,,", False)
        expected = "base_path/"
        self.assertEqual(expected, actual)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_is_directory_with_directory_no_subdirectories(self, mock_is_dir):
        mock_is_dir.return_value = True

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.is_directory('bucket', 'directory_id')
        self.assertTrue(result)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_is_directory_with_directory_subdirectories(self, mock_is_dir):
        mock_is_dir.return_value = True

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.is_directory('bucket', 'directory_id', "list,of,subdirectories")
        self.assertTrue(result)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_is_directory_with_directory_subdirectories_false(self, mock_is_dir):
        mock_is_dir.return_value = False

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.is_directory('bucket', 'directory_id', "list,of,subdirectories")
        self.assertFalse(result)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_is_directory_without_directory_subdirectories_false(self, mock_is_dir):
        mock_is_dir.return_value = False

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.is_directory('bucket', 'directory_id')
        self.assertFalse(result)

    @patch('storage_api.dependencies.storage.file_storage_adapter.FileStorageAdapter.zip_contents')
    def test_zip_directory(self, mock_zip_contents):
        mock_zip_contents.return_value = mock_file

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.zip_directory('bucket', 'directory_id', None, 'somename')

        self.assertEqual(result.file_name, 'somename')
        self.assertEqual(result.meta_type, 'application/zip')
        self.assertEqual(result.file, mock_file)

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_get_external_url(self, mock_is_dir):
        mock_is_dir.return_value = False

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNotNone(result)
        self.assertIn('external_reference', result)
        self.assertEqual(result['external_reference'], 'FILE_EXTERNAL_URL_BASE/bucket/file')

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_get_external_url_directory(self, mock_is_dir):
        mock_is_dir.return_value = True

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNotNone(result)
        self.assertIn('external_reference', result)
        self.assertEqual(result['external_reference'], 'FILE_EXTERNAL_URL_BASE/bucket/file')

    @patch('storage_api.dependencies.storage.file_storage_adapter.os.path.isdir')
    def test_get_external_url_sub_directory(self, mock_is_dir):
        mock_is_dir.return_value = True

        file_storage_adapter = FileStorageAdapter()
        result = file_storage_adapter.get_file_external_url('bucket', 'file', 'sub')

        self.assertIsNotNone(result)
        self.assertIn('external_reference', result)
        self.assertEqual(result['external_reference'], 'FILE_EXTERNAL_URL_BASE/bucket/sub')

    def test_get_extension_supports_csv(self):
        file_storage_adapter = FileStorageAdapter()

        result = file_storage_adapter.get_extension('text/csv')

        self.assertEqual(result, '.csv')

    def test_get_mime_supports_csv(self):
        file_storage_adapter = FileStorageAdapter()

        result = file_storage_adapter.get_mime('test_filename.csv')

        self.assertEqual(result, 'text/csv')
