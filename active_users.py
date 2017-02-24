import json
import os

ACTIVE_USERS = "active_users.txt"


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


def put_info(username, hackathon, roles, looking, search, match, skills):
    users = load_data(ACTIVE_USERS)

    if username not in users["users"]:
        users["users"][username] = {}
    users["users"][username]["hackathon"] = hackathon
    users["users"][username]["roles"] = roles
    users["users"][username]["looking"] = looking
    users["users"][username]["search"] = search
    users["users"][username]["match"] = match
    users["users"][username]["skills"] = skills
    write_data(users, ACTIVE_USERS)


def get_info(username):
    users = load_data(ACTIVE_USERS)
    if username in users["users"]:
        return users["users"][username]
    else:
        return None


def remove_user(username):
    users = load_data(ACTIVE_USERS)
    if username in users["users"]:
        del users["users"][username]
    write_data(users, ACTIVE_USERS)
