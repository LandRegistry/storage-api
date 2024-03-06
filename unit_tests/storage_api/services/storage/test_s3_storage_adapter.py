import io
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from flask import g
from flask_testing import TestCase
from storage_api import main
from storage_api.dependencies.storage.s3_storage_adapter import \
    S3StorageAdapter
from storage_api.exceptions import ApplicationError
from storage_api.model.storage_item import StorageItem


@patch('botocore.client')
class TestS3StorageAdapter(TestCase):
    def create_app(self):
        main.app.config["S3_BUCKET"] = "abc"
        main.app.config["S3_URL_EXPIRE_IN_SECONDS"] = 10
        return main.app

    def test_get_file_successful(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.get_file('bucket', 'file')

        self.assertIsNotNone(result)
        self.assertEqual('plain/text', result.meta_type)
        self.assertEqual('test.txt', result.file_name)
        self.assertEqual(b'test', result.file.read())

    def test_get_file_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.get_object.side_effect = Exception('failed to get')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            self.assertRaises(ApplicationError, s3_adapter.get_file, 'bucket', 'file')

    def test_get_file_not_found(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.get_object.side_effect = ClientError({'Error': {'Code': 'NoSuchKey'}}, 'get_object')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            result = s3_adapter.get_file('bucket', 'file')
            self.assertIsNone(result)

    def test_get_file_s3_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.get_object.side_effect = ClientError({'Error': {'Code': 'Connection'}}, 'get_object')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            self.assertRaises(ClientError, s3_adapter.get_file, 'bucket', 'file')

    @patch('storage_api.dependencies.storage.s3_storage_adapter.uuid')
    def test_save_file_successful(self, mock_uuid, mock_s3):
        mock_uuid.uuid4.return_value = "123"
        mock_s3.generate_presigned_url.return_value = "abc"
        mock_file = MagicMock()
        item = StorageItem(mock_file, 'plain/text', "test")
        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.save_file('bucket', item)
        self.assertIsNotNone(result)
        self.assertEqual('abc', result['external_reference'])
        self.assertEqual('bucket', result['bucket'])
        self.assertEqual('123', result['file_id'])
        self.assertEqual('bucket/123', result['reference'])

    @patch('storage_api.dependencies.storage.s3_storage_adapter.uuid')
    def test_save_file_successful_with_sub_dirs(self, mock_uuid, mock_s3):
        mock_uuid.uuid4.return_value = "123"
        mock_s3.generate_presigned_url.return_value = "abc"
        mock_file = MagicMock()
        item = StorageItem(mock_file, 'plain/text', "test")
        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.save_file('bucket', item, 'dir')
        self.assertIsNotNone(result)
        self.assertEqual('abc', result['external_reference'])
        self.assertEqual('bucket', result['bucket'])
        self.assertEqual('123', result['file_id'])
        self.assertEqual('bucket/123?subdirectories=dir', result['reference'])

    def test_save_file_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_file = MagicMock()
            item = StorageItem(mock_file, 'plain/text', "test")
            mock_s3.put_object.side_effect = Exception('failed to get')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            self.assertRaises(ApplicationError, s3_adapter.save_file, 'bucket', item)

    def test_zip_directory_successful(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.list_objects.return_value = {'Contents': [
            {'Key': 'abc'}
        ]}

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.zip_directory('bucket', '123', 'dir', 'test.zip')

        self.assertIsNotNone(result)
        self.assertEqual('application/zip', result.meta_type)
        self.assertEqual('test.zip', result.file_name)

    def test_zip_directory_successful_no_name(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.list_objects.return_value = {'Contents': [
            {'Key': 'abc'}
        ]}

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.zip_directory('bucket', '123', 'dir', None)

        self.assertIsNotNone(result)
        self.assertEqual('application/zip', result.meta_type)
        self.assertEqual('archive.zip', result.file_name)

    def test_zip_directory_no_files(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.list_objects.return_value = {'Contents': []}

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3
        result = s3_adapter.zip_directory('bucket', '123', 'dir', 'test.zip')

        self.assertIsNone(result)

    def test_zip_directory_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.list_objects.side_effect = Exception('failed to get')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            self.assertRaises(ApplicationError, s3_adapter.zip_directory, 'bucket', '123', 'dir', 'test.zip')

    def test_get_file_external_url_file_successful(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        mock_s3.generate_presigned_url.return_value = "abc"

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        result = s3_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNotNone(result)
        self.assertIn('external_reference', result)
        self.assertEqual('abc', result['external_reference'])

    def test_get_file_external_url_file_no_file(self, mock_s3):
        mock_s3.head_object.side_effect = ClientError({'Error': {'Code': '404'}}, 'get_object')

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        result = s3_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNone(result)

    def test_get_file_external_url_dir_successful(self, mock_s3):
        body = io.BytesIO(b'test')

        mock_s3.list_objects.return_value = {'Contents': [
            {'Key': 'abc'}
        ]}

        mock_s3.get_object.return_value = {
            'Body': body,
            'Metadata': {
                'content-type': 'plain/text',
                'file-name': 'test.txt'
            }
        }

        mock_s3.generate_presigned_url.return_value = "abc"

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        result = s3_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNotNone(result)
        self.assertIn('external_reference', result)
        self.assertEqual('abc', result['external_reference'])

    def test_get_file_external_url_dir_no_file(self, mock_s3):
        mock_s3.list_objects.side_effect = [
            {'Contents': [{'Key': 'abc'}]}, {'Contents': []}]

        mock_s3.get_object.side_effect = ClientError({'Error': {'Code': 'NoSuchKey'}}, 'get_object')

        mock_s3.generate_presigned_url.return_value = "abc"

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        result = s3_adapter.get_file_external_url('bucket', 'file')

        self.assertIsNone(result)

    def test_delete_file_successful(self, mock_s3):

        mock_s3.head_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        mock_s3.delete_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 204}}

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertTrue(s3_adapter.delete_file('bucket', 'file'))

    def test_delete_file_failed(self, mock_s3):

        mock_s3.head_object.side_effect = ClientError({'Error': {'Code': '404'}}, 'get_object')

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertFalse(s3_adapter.delete_file('bucket', 'file'))

    def test_delete_file_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.delete_object.side_effect = ClientError({'Error': {'Code': '500'}}, 'delete_object')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3
            self.assertRaises(ApplicationError, s3_adapter.delete_file, 'bucket', 'file')

    def test_is_directory_true(self, mock_s3):
        mock_s3.list_objects.return_value = {'Contents': [
            {'Key': 'abc'}
        ]}

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertTrue(s3_adapter.is_directory('bucket', 'file'))

    def test_is_directory_false_if_only_key_matches(self, mock_s3):
        mock_s3.list_objects.return_value = {'Contents': [
            {'Key': 'bucket/abc'}
        ]}

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertFalse(s3_adapter.is_directory('bucket', 'abc'))

    def test_is_directory_false(self, mock_s3):
        mock_s3.list_objects.return_value = {'Contents': []}

        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertFalse(s3_adapter.is_directory('bucket', 'file'))

    def test_get_s3_signed_url_successful(self, mock_s3):
        mock_s3.generate_presigned_url.return_value = "abc"
        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        result = s3_adapter.get_s3_signed_url('key')

        self.assertEqual('abc', result)

    def test_get_s3_signed_url_failed(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.generate_presigned_url.side_effect = ClientError(
                {'Error': {'Code': '500'}}, 'generate_presigned_url')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3

            self.assertRaises(ApplicationError, s3_adapter.get_s3_signed_url, 'key')

    def test_does_file_exist_true(self, mock_s3):
        mock_s3.head_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertTrue(s3_adapter.does_file_exist('file'))

    def test_does_file_exist_false(self, mock_s3):
        mock_s3.head_object.side_effect = ClientError({'Error': {'Code': '404'}}, 'head_object')
        s3_adapter = S3StorageAdapter()
        s3_adapter._connection = mock_s3

        self.assertFalse(s3_adapter.does_file_exist('file'))

    def test_does_file_exist_exception(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'
            mock_s3.head_object.side_effect = ClientError({'Error': {'Code': '500'}}, 'head_object')
            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3

            self.assertRaises(ApplicationError, s3_adapter.does_file_exist, 'key')

    def test_get_full_filename_supports_csv(self, mock_s3):
        with main.app.test_request_context():
            g.trace_id = '123'

            s3_adapter = S3StorageAdapter()
            s3_adapter._connection = mock_s3

            mock_file = MagicMock()
            test_storage_item = StorageItem(mock_file, 'text/csv', 'testfile')

            result = s3_adapter.get_full_filename(test_storage_item)

            self.assertEqual(result, 'testfile.csv')
