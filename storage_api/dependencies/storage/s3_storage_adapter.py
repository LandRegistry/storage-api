import io
import os
import threading
import uuid
import zipfile
from mimetypes import guess_extension

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from flask import current_app
from storage_api.dependencies.storage.storage_base import StorageBase
from storage_api.exceptions import ApplicationError
from storage_api.model.storage_item import StorageItem


class S3StorageAdapter(StorageBase):

    _instance = None
    _lock = threading.Lock()
    _connection = None

    def __new__(cls, s3_instance=None):
        with S3StorageAdapter._lock:
            if S3StorageAdapter._instance is None:
                S3StorageAdapter._instance = super(S3StorageAdapter, cls).__new__(cls)
                S3StorageAdapter._instance._connection = boto3.client('s3',
                                                                      config=Config(
                                                                          signature_version='s3v4',
                                                                          s3={'addressing_style': 'virtual'}))
        return S3StorageAdapter._instance

    def get_file(self, bucket, file_id, subdirectories=None):
        full_key = S3StorageAdapter.get_full_key(bucket, file_id, subdirectories)

        try:
            response = self._connection.get_object(Bucket=current_app.config['S3_BUCKET'], Key=full_key)
            file = io.BytesIO(response["Body"].read())
            metadata = response["Metadata"]
            return StorageItem(file, metadata['content-type'], metadata['file-name'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                error_message = 'Key {} does not exist. Exception - {}' \
                    .format(full_key, e)
                current_app.logger.warning(error_message)
                return None
            raise
        except Exception as ex:
            error_message = 'Failed to get to the requested file. Exception - {}' \
                .format(ex)
            current_app.logger.warning(error_message)
            raise ApplicationError('Failed to get to the requested file', 'S3-GET')

    def save_file(self, bucket, storage_item, subdirectories=None):
        try:
            key = str(uuid.uuid4())
            full_key = S3StorageAdapter.get_full_key(bucket, key, subdirectories)

            reference = "{}/{}".format(bucket, key)
            if subdirectories is not None:
                reference = reference + "?subdirectories={}".format(subdirectories)

            self._connection.put_object(Body=storage_item.file,
                                        ContentType=storage_item.meta_type,
                                        Bucket=current_app.config['S3_BUCKET'],
                                        Key=full_key,
                                        Metadata={
                                            'file-name': storage_item.file_name,
                                            'content-type': storage_item.meta_type}
                                        )
            url = self.get_s3_signed_url(full_key)

            response = {
                "bucket": bucket,
                "file_id": str(key),
                "reference": reference,
                "external_reference": url
            }

            if subdirectories is not None:
                response["subdirectory"] = "{}".format(subdirectories)

            return response

        except Exception as ex:
            error_message = 'Failed to save to the requested file. Exception - {}' \
                .format(ex)
            current_app.logger.exception(error_message)
            raise ApplicationError('Failed to save to the requested file', 'S3-SAVE')

    def zip_directory(self, bucket, file_id, subdirectories, name):
        try:
            full_key = S3StorageAdapter.get_full_key(bucket, file_id, subdirectories)
            response = self._connection.list_objects(Bucket=current_app.config['S3_BUCKET'],
                                                     Prefix=full_key,
                                                     Delimiter=',')
            if 'Contents' in response:
                files = []
                keys = response['Contents']
                if len(keys) > 0:
                    for s3_key in keys:
                        key = s3_key['Key']
                        response = self._connection.get_object(Bucket=current_app.config['S3_BUCKET'], Key=key)
                        file = io.BytesIO(response["Body"].read())
                        metadata = response["Metadata"]
                        files.append(StorageItem(file, metadata['content-type'], metadata['file-name']))

                    memory_file = io.BytesIO()

                    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for individual_file in files:
                            individual_file.file.seek(0)
                            zf.writestr(S3StorageAdapter.get_full_filename(individual_file),
                                        individual_file.file.getvalue())
                    memory_file.seek(0)

                    if memory_file:
                        if name is None:
                            name = "archive.zip"
                        return StorageItem(memory_file, "application/zip", name)
            return None
        except Exception as ex:
            error_message = 'Failed to zip to the requested files. Exception - {}' \
                .format(ex)
            current_app.logger.exception(error_message)
            raise ApplicationError(error_message, 'S3-ZIP', 500)

    def get_file_external_url(self, bucket, file_id, subdirectories=None):
        if self.is_directory(bucket, file_id, subdirectories):
            key = str(uuid.uuid4())
            name = "{}.zip".format(key)
            storage_item = self.zip_directory(bucket, file_id, subdirectories, name)

            if storage_item is None:
                return None

            full_key = "temp/{}".format(S3StorageAdapter.get_full_key(bucket, key, None))

            self._connection.put_object(Body=storage_item.file,
                                        ContentType=storage_item.meta_type,
                                        Bucket=current_app.config['S3_BUCKET'],
                                        Key=full_key,
                                        Metadata={
                                            'file-name': storage_item.file_name,
                                            'content-type': storage_item.meta_type}
                                        )

            return {"external_reference": self.get_s3_signed_url(full_key)}

        full_key = S3StorageAdapter.get_full_key(bucket, file_id, subdirectories)
        if self.does_file_exist(full_key):
            return {"external_reference": self.get_s3_signed_url(full_key)}

        return None

    def delete_file(self, bucket, file_id, subdirectories=None):
        full_key = S3StorageAdapter.get_full_key(bucket, file_id, subdirectories)

        if self.does_file_exist(full_key):
            try:
                self._connection.delete_object(Bucket=current_app.config['S3_BUCKET'], Key=full_key)
                return True
            except ClientError as ex:
                error_message = 'Failed to delete to the requested file. Exception - {}' \
                    .format(ex)
                current_app.logger.exception(error_message)
                raise ApplicationError(error_message, 'S3-DELETE', 500)

        return False

    def is_directory(self, bucket, file_id, subdirectories=None):
        full_key = S3StorageAdapter.get_full_key(bucket, file_id, subdirectories)
        response = self._connection.list_objects(Bucket=current_app.config['S3_BUCKET'],
                                                 Prefix=full_key,
                                                 Delimiter=',')
        if 'Contents' in response:
            keys = response['Contents']
            if len(keys) > 0:
                if len(keys) == 1:
                    if keys[0]['Key'] == full_key:
                        return False
                return True
        return False

    def get_s3_signed_url(self, key):
        try:
            url = self._connection.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': current_app.config['S3_BUCKET'],
                    'Key': key
                },
                ExpiresIn=current_app.config['S3_URL_EXPIRE_IN_SECONDS']
            )
            return url
        except ClientError as ex:
            error_message = 'Failed to generate external key for {}. Exception - {}' \
                .format(key, ex)
            current_app.logger.warning(error_message)
            raise ApplicationError(error_message, 'S3-EXTERNAL-URL', 500)

    def does_file_exist(self, key):
        try:
            self._connection.head_object(Bucket=current_app.config['S3_BUCKET'], Key=key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise ApplicationError('Failed to check if key exists. Exception - {}'.format(e), 'S3-EXISTS')
        return True

    @staticmethod
    def get_full_key(bucket, file_id, subdirectories=None):
        directory = bucket
        if subdirectories is not None:
            subdirectories = subdirectories.split(',')
            for subdirectory in subdirectories:
                directory = os.path.join(directory, subdirectory)

        return os.path.join(directory, file_id)

    @staticmethod
    def get_full_filename(storage_item: StorageItem) -> str:
        # Manual check for CSV files as we use Python 3.4 and CSV support wasn't added until Python 3.5
        # https://hg.python.org/cpython/rev/711672506b40
        if storage_item.meta_type == 'text/csv':
            extension = '.csv'
        else:
            extension = guess_extension(storage_item.meta_type)
        return '{0}{1}'.format(storage_item.file_name, extension)
