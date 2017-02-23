import json
import os

FIND_MEMBERS = "find_members.txt"


def load_data(database_name):
    """Loads data from database"""
    with open(database_name, 'r') as infile:
        if os.stat(database_name).st_size == 0:
            return {"users": {}}
        else:
            data = json.load(infile)
    return data


def write_data(data, database_name):
    with open(database_name, 'w') as outfile:
        json.dump(data, outfile)


def put_info(username, roles, skills):
    data = load_data(FIND_MEMBERS)

    if username not in data["users"]:
        data["users"][username] = {}
    data["users"][username]["roles"] = roles
    data["users"][username]["skills"] = skills
    write_data(data, FIND_MEMBERS)


def get_info(username):
    data = load_data(FIND_MEMBERS)
    if username in data["users"]:
        return data["users"][username]
    else:
        return None


def remove_user(username):
    data = load_data(FIND_MEMBERS)
    if username in data["users"]:
        del data["users"][username]
    write_data(data, FIND_MEMBERS)
