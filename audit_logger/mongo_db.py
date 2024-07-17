from flask import has_app_context, current_app as app
from pymongo import MongoClient


class MongoDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls, *args, **kwargs):
        print("=== MongoDB New Called")
        if cls._instance is None:
            print("=== MongoDB New is None")
            cls._instance = super(MongoDB, cls).__new__(cls)

        return cls._instance

    @classmethod
    def _initialize(cls):
        print("=== MongoDB Initialize Called")
        if not has_app_context():
            raise RuntimeError("Application context is required to initialize MongoDB")

        if cls._instance._client is None or cls._instance._db is None:
            print("=== MongoDB Vars are None")
            cls._instance._client = MongoClient(app.config['MONGO_URI'])
            cls._instance._db = cls._instance._client.get_default_database()

    @classmethod
    def create_instance(cls):
        instance = cls.__new__(cls)
        instance._initialize()
