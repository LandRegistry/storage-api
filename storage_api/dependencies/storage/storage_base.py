from abc import ABCMeta, abstractmethod


class StorageBase(metaclass=ABCMeta):
    @abstractmethod
    def get_file(self, bucket, file_id, subdirectories=None):
        raise NotImplementedError()

    @abstractmethod
    def get_file_external_url(self, bucket, file_id, subdirectories=None):
        raise NotImplementedError()

    @abstractmethod
    def zip_directory(self, bucket, file_id, subdirectories, name):
        raise NotImplementedError()

    @abstractmethod
    def is_directory(self, bucket, file_id, subdirectories=None):
        raise NotImplementedError()

    @abstractmethod
    def delete_file(self, bucket, file_id, subdirectories=None):
        raise NotImplementedError()

    @abstractmethod
    def save_file(self, bucket, storage_item, subdirectories=None):
        raise NotImplementedError()
