import threading
import time

import pymongo


DATABASE_INSTANCE = None


class Database:
    def __init__(
            self, host, name,
            logger_debug=lambda _: None, logger_info=lambda _: None,
            logger_warning=lambda _: None, logger_error=lambda _: None):
        global DATABASE_INSTANCE
        DATABASE_INSTANCE = self

        self.host = host
        self.name = name

        self.debug = logger_debug
        self.info = logger_info
        self.warning = logger_warning
        self.error = logger_error

        self.connection = None
        self.session = None

    def connect(self):
        try:
            self.connection = pymongo.MongoClient(
                self.host, serverSelectionTimeoutMS=1000
            )
            self.connection.server_info()
            self.session = self.connection[self.name]
            self.info('Connected to database')
        except pymongo.errors.ServerSelectionTimeoutError:
            self.error('Unable to connect to database')
            self.session = None


class KeepAliveService:
    def __init__(self, database, interval=5):
        self.database = database
        self.interval = interval

        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._service)
        thread.daemon = True
        thread.start()

    def wait_for_connection(self):
        while self.database.session is None:
            time.sleep(.001)

    def _service(self):
        while self.running:
            reset = (
                not self.database.connection or self.database.session is None
            )
            try:
                self.database.connection.server_info()
            except pymongo.errors.ServerSelectionTimeoutError:
                reset = True
            if reset:
                self.database.warning(
                    'Database Keep Alive Service: database connection reset'
                )
                self.database.connect()
            time.sleep(self.interval)
