import json
import time
import os

import maybot_db

DATABASE_NAME = "maybot"
FINDING_COLLECTION = "finding"


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


def get_info(username):
    """Returns the specified user from the finding collection, returns None if not found"""
    database = maybot_db.access(DATABASE_NAME)
    search = database[FINDING_COLLECTION].find_one({"username": username})

    if search.count() > 0:
        return search[0]
    else:
        return None


def new_user(username, name, hackathon, roles, skills):
    """Inserts a new user into the database

    Keyword Arguments:
    username -- user's username as a string
    name -- user's name as a string
    hackathon -- hackathon attending as a string
    roles -- list of interested roles
    skills -- list of list of skills and their level from 1 to 5 as an integer
    """
    database = maybot_db.access(DATABASE_NAME)
    user = {"username": username,
            "name": name,
            'timestamp': time.time(),
            "hackathon": hackathon,
            "roles": roles,
            "skills": skills}
    database[FINDING_COLLECTION].insert_one(user)


def filter_role(roles, hackathon):
    """Returns all the matches of a user and all other users' roles"""
    if not isinstance(roles, list):
        print("Invalid Input!")
        return
    database = maybot_db.access(DATABASE_NAME)
    users = database[FINDING_COLLECTION].find({"hackathon": hackathon})
    matches = []

    for user in users:
        username = user["username"]
        user_roles = user["roles"]
        user_skills = user["skills"]
        score = score_user(roles, user_roles)
        timestamp = user["timestamp"]
        if score > 0:
            matches.append([username, score, timestamp, user_roles, user_skills])
    matches = sorted(matches, key=lambda match: (match[1] * (-1), match[2]))
    return matches


# scores users based on how many matches
def score_user(roles, user_roles):
    score = reduce(lambda x, y: (x + 1) if (y.lower() in (role.lower() for role in roles)) else x, user_roles, 0)
    return score


def remove_user(username):
    """Deletes a user from the finding collection,
    returns True if user was removed, otherwise False"""
    database = maybot_db.access(DATABASE_NAME)
    return database[FINDING_COLLECTION].delete_one({"username": username}).acknowledged
