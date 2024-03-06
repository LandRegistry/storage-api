from flask import current_app
from storage_api.dependencies.storage.file_storage_adapter import \
    FileStorageAdapter
from storage_api.dependencies.storage.s3_storage_adapter import \
    S3StorageAdapter


def get_storage_type():
    if current_app.config["STORAGE_TYPE"].lower() == 'file':
        return FileStorageAdapter()
    elif current_app.config["STORAGE_TYPE"].lower() == 's3':
        return S3StorageAdapter()
    else:
        raise NotImplementedError('no service implemented for {0}'.format(current_app.config["STORAGE_TYPE"]))
