from datetime import datetime
from enum import Enum

from flask import Blueprint, request, g
from audit_logger.utils import get_json_body, get_only_changed_values_and_id

SUCCESS_STATUS_CODES = [200, 201, 204]
DEFAULT_LOG_METHODS = ["GET", "POST", "PUT", "DELETE"]


class ActionEnum(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class AuditBlueprint(Blueprint):
    """
        AuditBlueprint is a blueprint that logs changes to a collection in a MongoDB database.
    """
    def __init__(self, *args, **kwargs):
        self.get_audit_database_func = kwargs.pop("get_audit_database_func", None)
        self.target_collection_name = kwargs.pop("target_collection_name", None)
        self.log_methods = kwargs.pop("log_methods", DEFAULT_LOG_METHODS)
        self.id_field = kwargs.pop("id_field", "_id")

        if self.get_audit_database_func is None or self.target_collection_name is None:
            raise ValueError("get_audit_database_func and target_collection are required")

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
                new_data = get_only_changed_values_and_id(old_data or {}, new_data, self.id_field) if old_data else new_data

            self.create_log(ActionEnum(request.method), request.path, new_value=new_data, old_value=old_data)

        return response

    def create_log(self, action: ActionEnum, endpoint: str, new_value=None, old_value=None):
        user_info = g.auth_user if g.get("auth_user") else {}

        audit_log = {
            "collection": self.target_collection_name,
            "action": action.value,
            "endpoint": endpoint,
            "user": user_info,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow()
        }
        self.get_audit_database_func().insert_one(audit_log)
