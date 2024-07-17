from datetime import datetime
from typing import Union

from flask import Request, g


def get_json_body(req: Request) -> Union[list, dict]:
    try:
        body = req.json or {}
    except Exception:
        body = {}

    return body


def get_only_changed_values(old_data: dict, new_data: dict) -> dict:
    diff_dict = {}

    for key in new_data:
        if key in old_data:
            if isinstance(new_data[key], dict) and isinstance(old_data[key], dict):
                # If both values are dictionaries, recursively compare them
                nested_diff = get_only_changed_values(old_data[key], new_data[key])
                if nested_diff:
                    diff_dict[key] = nested_diff
            elif new_data[key] != old_data[key]:
                # If the values are different, add to the diff_dict
                diff_dict[key] = new_data[key]
        else:
            # If the key is not present in dict2, add to the diff_dict
            diff_dict[key] = new_data[key]

    return diff_dict


def get_only_changed_values_and_id(old_data: dict, new_data: dict) -> dict:
    diff_dict = get_only_changed_values(old_data, new_data)

    if "_id" in old_data:
        diff_dict["_id"] = old_data.get("_id")
        diff_dict.pop("id", None)

    return diff_dict


def get_action(http_method: str, status_code: int) -> str:
    if http_method == "GET":
        return "RETRIEVE"

    if http_method == "POST":
        if status_code == 201:
            return "CREATE"
        return "UPDATE"

    if http_method == "PUT":
        return "UPDATE"

    if http_method == "DELETE":
        return "DELETE"
