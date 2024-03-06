import io
from unittest.mock import MagicMock, Mock, patch

from flask import url_for
from flask_testing import TestCase
from storage_api import main
from storage_api.model.storage_item import StorageItem

mock_file = io.BytesIO(b'testfile')


class TestStorage(TestCase):
    def create_app(self):
        return main.app

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_file_found(self, mock_factory):
        storage_item = StorageItem(mock_file, "abc", "mockfile.txt")
        mock_file_service = MagicMock()
        mock_file_service.is_directory.return_value = False
        mock_file_service.get_file.return_value = storage_item

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 200)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_is_directory(self, mock_factory):
        storage_item = StorageItem(mock_file, "abc", "mockfile.txt")
        mock_file_service = MagicMock()
        mock_file_service.is_directory.return_value = True
        mock_file_service.zip_directory.return_value = storage_item

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 200)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_file_not_found(self, mock_factory):
        mock_file_service = MagicMock()
        mock_file_service.is_directory.return_value = False
        mock_file_service.get_file.return_value = None

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 404)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_directory_failed_to_zip(self, mock_factory):
        mock_file_service = MagicMock()
        mock_file_service.is_directory.return_value = True
        mock_file_service.zip_directory.return_value = None

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 404)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_exception_thrown(self, mock_factory):
        mock_file_service = MagicMock()
        mock_file_service.is_directory.return_value = False
        mock_file_service.get_file.side_effect = Exception("test")

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 500)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_storage_factory_exception_thrown(self, mock_factory):

        mock_factory.get_storage_type.side_effect = NotImplementedError

        get_response = self.client.get(url_for('storage.get_file', bucket=1, file_id=1))
        self.assertEqual(get_response.status_code, 500)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_delete_storage_file_successful(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.delete_file.return_value = True

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.delete(url_for('storage.delete_file', bucket=1, file_id=1),
                                          headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 204)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_delete_storage_file_no_file(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.delete_file.return_value = False

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.delete(url_for('storage.delete_file', bucket=1, file_id=1),
                                          headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 404)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_delete_storage_factory_exception(self, mock_factory, validate):

        mock_factory.get_storage_type.side_effect = NotImplementedError

        get_response = self.client.delete(url_for('storage.delete_file', bucket=1, file_id=1),
                                          headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 500)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_successful(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.save_file.return_value = {"bucket": "1", "key": "123"}

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.post(
            url_for('storage.save_file', bucket=1),
            data={'file': (io.BytesIO(b'my file contents'), 'file.txt')},
            headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 201)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    @patch('storage_api.views.v1_0.storage.pyclamd')
    def test_scan_and_save_successful(self, mock_pyclamd, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.save_file.return_value = {"bucket": "1", "key": "123"}

        mock_factory.get_storage_type.return_value = mock_file_service

        mock_pyclamd.ClamdUnixSocket.return_value.scan_stream.return_value = False

        get_response = self.client.post(
            url_for('storage.save_file', bucket=1, scan=True),
            data={'file': (io.BytesIO(b'my file contents'), 'file.txt')},
            headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 201)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.rollback')
    @patch('storage_api.views.v1_0.storage.pyclamd')
    def test_scan_and_save_threat_found(self, mock_pyclamd, mock_rollback, validate):
        eicar_test = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'

        mock_pyclamd.ClamdUnixSocket.return_value.scan_stream.return_value = True

        response = self.client.post(url_for('storage.save_file', bucket=1, scan=True),
                                    data={'file': (io.BytesIO(eicar_test), 'file.txt')},
                                    headers={'Authorization': 'Fake JWT'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error_message'], "Virus scan failed on uploaded document")
        mock_rollback.assert_called()

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_successful_with_expires_header(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.save_file.return_value = {"bucket": "1", "key": "123"}

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.post(
            url_for('storage.save_file', bucket=1),
            data={'file': (io.BytesIO(b'my file contents'), 'file.txt')},
            headers={"Expires": "abc", 'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 201)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_no_file(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.save_file.return_value = {"bucket": "1", "key": "123"}

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.post(url_for('storage.save_file', bucket=1),
                                        headers={'Authorization': 'Fake JWT'})
        response = get_response.json
        self.assertEqual(get_response.status_code, 400)
        self.assertEqual(response['error_code'], 400)
        self.assertEqual(response['error_message'], 'No File in request')

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_more_than_one_file(self, mock_factory, validate):
        mock_file_service = MagicMock()
        mock_file_service.save_file.return_value = {"bucket": "1", "key": "123"}

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.post(
            url_for('storage.save_file', bucket=1),
            data={
                'file1': (io.BytesIO(b'my file contents'), 'file1.txt'),
                'file2': (io.BytesIO(b'my file contents'), 'file2.txt')
            },
            headers={'Authorization': 'Fake JWT'})
        self.assertEqual(get_response.status_code, 201)

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_factory_exception(self, mock_factory, validate):

        mock_factory.get_storage_type.side_effect = Exception("no service implemented")

        get_response = self.client.post(url_for('storage.save_file', bucket=1), data={
            'file1': (io.BytesIO(b'my file contents'), 'file1.txt')
        },
            headers={'Authorization': 'Fake JWT'})
        response = get_response.json
        self.assertEqual(get_response.status_code, 500)
        self.assertEqual(response['error_message'], "Failed to save the requested file. Rolling back any changes")

    @patch('storage_api.app.validate')
    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_save_storage_file_exception(self, mock_factory, validate):
        mock_file_service = Mock()
        mock_file_service.save_file.side_effect = Exception('failed to save')
        mock_file_service.delete_file.return_value = True

        mock_factory.get_storage_type.return_value = mock_file_service

        get_response = self.client.post(url_for('storage.save_file', bucket=1), data={
            'file1': (io.BytesIO(b'my file contents'), 'file1.txt')
        },
            headers={'Authorization': 'Fake JWT'})

        response = get_response.json
        self.assertEqual(get_response.status_code, 500)
        self.assertEqual(response['error_code'], 'S-01')
        self.assertEqual(response['error_message'], 'Failed to save the requested file. Rolling back any changes')

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_file_external_url(self, mock_factory):
        mock_file_service = Mock()
        mock_file_service.get_file_external_url.return_value = {"external_reference": "abc"}
        mock_factory.get_storage_type.return_value = mock_file_service

        result = self.client.get(url_for('storage.get_file_external_url', bucket=1, file_id=1))

        json = result.json
        self.assertEqual(result.status_code, 200)
        self.assertIn('external_reference', json)
        self.assertEqual('abc', json['external_reference'])

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_file_external_url_no_file(self, mock_factory):
        mock_file_service = Mock()
        mock_file_service.get_file_external_url.return_value = None
        mock_factory.get_storage_type.return_value = mock_file_service

        result = self.client.get(url_for('storage.get_file_external_url', bucket=1, file_id=1))

        self.assertEqual(result.status_code, 404)

    @patch('storage_api.views.v1_0.storage.storage_type_factory')
    def test_get_file_external_url_error(self, mock_factory):
        mock_file_service = Mock()
        mock_file_service.get_file_external_url.side_effect = Exception('failed to save')
        mock_factory.get_storage_type.return_value = mock_file_service

        result = self.client.get(url_for('storage.get_file_external_url', bucket=1, file_id=1))

        self.assertEqual(result.status_code, 500)
