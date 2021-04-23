import sys

try:
    import pymongo
except ImportError:
    pass

loaded = 'pymongo' in sys.modules


class MongoDatabase:
    def __init__(self, host, timeout=50):
        self.host = host
        self.timeout = timeout

    def connect(self):
        try:
            client = pymongo.MongoClient(
                self.host,
                serverSelectionTimeoutMS=self.timeout
            )
            client.server_info()
            return client
        except pymongo.errors.ServerSelectionTimeoutError as exception:
            return str(exception)
