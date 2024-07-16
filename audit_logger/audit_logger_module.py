from datetime import datetime
from enum import Enum
from pymongo import MongoClient

from flask import Blueprint, request, g, has_app_context, current_app as app
from audit_logger.utils import get_json_body, get_only_changed_values_and_id

SUCCESS_STATUS_CODES = [200, 201, 204]
DEFAULT_LOG_METHODS = ["GET", "POST", "PUT", "DELETE"]


class ActionEnum(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class MongDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls, *args, **kwargs):
        print("=== MongoDB New Called")
        if cls._instance is None:
            print("=== MongoDB New is None")
            cls._instance = super(MongDB, cls).__new__(cls)

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


class AuditBlueprint(Blueprint):
    """
        AuditBlueprint is a blueprint that logs changes to a collection in a MongoDB database.
    """
    def __init__(self, *args, **kwargs):
        self.log_methods = kwargs.pop("log_methods", DEFAULT_LOG_METHODS)
        self.audit_collection = None

        super(AuditBlueprint, self).__init__(*args, **kwargs)
        self.after_request(self.after_data_request)

    def _is_loggable(self, response) -> bool:
        return request.method in self.log_methods and response.status_code in SUCCESS_STATUS_CODES

    def after_data_request(self, response):
        if self._is_loggable(response):
            if g.get("old_data"):
                old_data = g.old_data
            else:
                old_data = None

            new_data = get_json_body(request)

            if request.method == 'DELETE':
                new_data = None
            elif request.method == 'GET':
                new_data = old_data = None
            else:
                new_data = get_only_changed_values_and_id(old_data or {}, new_data) if old_data else new_data

            self.create_log(ActionEnum(request.method), response.status_code, request.path, new_value=new_data, old_value=old_data)

        return response

    def get_audit_collection(self):
        if not self.audit_collection:
            MongDB.create_instance()
            self.audit_collection = MongDB._instance._db["audit"]

    def create_log(self, action: ActionEnum, status_code: int, endpoint: str, new_value=None, old_value=None):
        user_info = g.auth_user if g.get("auth_user") else {}

        audit_log = {
            "collection": g.get("table_name"),
            "action": action.value,
            "status_code": status_code,
            "endpoint": endpoint,
            "user": user_info,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow()
        }
        self.get_audit_collection()
        self.audit_collection.insert_one(audit_log)
