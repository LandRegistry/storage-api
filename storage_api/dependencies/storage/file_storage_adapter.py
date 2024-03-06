import io
import os
import threading
import uuid
import zipfile
from mimetypes import guess_extension, guess_type

from flask import current_app
from storage_api.dependencies.storage.storage_base import StorageBase
from storage_api.model.storage_item import StorageItem


class FileStorageAdapter(StorageBase):

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with FileStorageAdapter._lock:
            if FileStorageAdapter._instance is None:
                FileStorageAdapter._instance = super(FileStorageAdapter, cls).__new__(cls)
        return FileStorageAdapter._instance

    def get_file(self, bucket, file_id, subdirectories=None):
        path = FileStorageAdapter.get_directory_path(bucket, subdirectories)
        file = FileStorageAdapter.get_file_stream(path, file_id)
        if file:
            return StorageItem(file, FileStorageAdapter.get_mime(file.name), file.name)
        return None

    def get_file_external_url(self, bucket, file_id, subdirectories=None):
        if subdirectories is not None:
            reference = '{}/{}?subdirectories={}'.format(bucket, file_id, subdirectories)
        else:
            reference = "{}/{}".format(bucket, file_id)

        if self.is_directory(bucket, file_id, subdirectories):
            if subdirectories is not None:
                reference = "{}/{}".format(bucket, subdirectories)

            response = {
                "external_reference": "{}/{}".format(current_app.config['FILE_EXTERNAL_URL_BASE'], reference)
            }
            return response

        response = {
            "external_reference": "{}/{}".format(current_app.config['FILE_EXTERNAL_URL_BASE'], reference)
        }
        return response

    def is_directory(self, bucket, file_id, subdirectories=None):
        path = FileStorageAdapter.get_directory_path(bucket, subdirectories)
        path = os.path.join(path, file_id)
        return FileStorageAdapter.is_path_directory(path)

    def zip_directory(self, bucket, file_id, subdirectories, name):
        path = FileStorageAdapter.get_directory_path(bucket, subdirectories)
        path = os.path.join(path, file_id)
        zipped_directory = FileStorageAdapter.zip_contents(path)
        if zipped_directory:
            if name is None:
                name = "archive.zip"
            return StorageItem(zipped_directory, "application/zip", name)
        return None

    def delete_file(self, bucket, file_id, subdirectories=None):
        try:
            path = FileStorageAdapter.get_directory_path(bucket, subdirectories)

            for search_file in os.listdir(path):
                if search_file.startswith("{0}.".format(file_id)):
                    full_path = os.path.join(path, search_file)
                    os.remove(full_path)
                    return True

        except Exception as ex:
            error_message = 'Failed to delete to the requested file. Exception - {}' \
                .format(ex)
            current_app.logger.exception(error_message)
        return False

    def save_file(self, bucket, storage_item, subdirectories=None):
        try:
            key = uuid.uuid4()
            directory = os.path.join(current_app.config['FILE_STORAGE_LOCATION'], bucket)

            FileStorageAdapter.make_directory(directory)
            reference = "{}/{}".format(bucket, key)

            if subdirectories is not None:
                reference = reference + "?subdirectories={}".format(subdirectories)
                directory = FileStorageAdapter.add_sub_directory_to_path(directory, subdirectories, True)

            extension = FileStorageAdapter.get_extension(storage_item.meta_type)
            filename = '{0}{1}'.format(key, extension)
            filepath = os.path.join(directory, filename)
            storage_item.file.save(filepath)

            response = {
                "bucket": bucket,
                "file_id": str(key),
                "reference": reference,
                "external_reference": "{}/{}".format(current_app.config['FILE_EXTERNAL_URL_BASE'], reference)
            }

            if subdirectories is not None:
                response["subdirectory"] = "{}".format(subdirectories)

            return response

        except Exception as ex:
            error_message = 'Failed to save to the requested file. Exception - {}' \
                .format(ex)
            current_app.logger.exception(error_message)
            raise ex

    @staticmethod
    def add_sub_directory_to_path(directory, subdirectories, is_save):
        subdirectories = subdirectories.split(',')
        for subdirectory in subdirectories:
            directory = os.path.join(directory, subdirectory)
            if is_save:
                FileStorageAdapter.make_directory(directory)

        return directory

    @staticmethod
    def is_path_directory(path):
        return os.path.isdir(path)

    @staticmethod
    def get_directory_path(bucket, subdirectories):
        directory_path = os.path.join(current_app.config["FILE_STORAGE_LOCATION"], bucket)
        if subdirectories is not None:
            directory_path = FileStorageAdapter.add_sub_directory_to_path(directory_path, subdirectories, False)
        return directory_path

    @staticmethod
    def make_directory(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def get_extension(mime):
        # Manual check for CSV files as we use Python 3.4 and CSV support wasn't added until Python 3.5
        # https://hg.python.org/cpython/rev/711672506b40
        if mime == 'text/csv':
            return '.csv'
        return guess_extension(mime)

    @staticmethod
    def get_mime(filename):
        # Manual check for CSV files as we use Python 3.4 and CSV support wasn't added until Python 3.5
        # https://hg.python.org/cpython/rev/711672506b40
        if filename[-4:] == '.csv':
            return 'text/csv'
        return guess_type(filename)[0]

    @staticmethod
    def zip_contents(directory):
        try:
            memory_file = io.BytesIO()
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            with zipfile.ZipFile(memory_file, 'w') as zf:
                for individual_file in files:
                    data = zipfile.ZipInfo(individual_file)
                    data.compress_type = zipfile.ZIP_DEFLATED
                    zf.write("{}/{}".format(directory, individual_file), os.path.basename(individual_file))
            memory_file.seek(0)
            return memory_file
        except Exception as ex:
            error_message = 'Failed to zip to the requested files. Exception - {}' \
                .format(ex)
            current_app.logger.exception(error_message)

    @staticmethod
    def get_file_stream(directory, file_id):
        if len(file_id) > 4 and file_id[-4] == '.':  # check if file_id includes file extension
            if os.path.isfile(os.path.join(directory, file_id)):
                return io.open(os.path.join(directory, file_id), 'rb')
        try:
            for path, dirs, files in os.walk(directory):
                for file in files:
                    if file.startswith("{}.".format(file_id)):
                        return io.open(os.path.join(path, file), 'rb')
            return None
        except Exception as ex:
            error_message = 'Failed to get the file. Exception - {}' \
                .format(ex)
        current_app.logger.exception(error_message)
