
class StorageItem(object):

    meta_type = None
    file = None
    file_name = None

    def __init__(self, file, mime, file_name):
        self.meta_type = mime
        self.file = file
        self.file_name = file_name
