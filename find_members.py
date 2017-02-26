import json
import os

import maybot_db

RECRUITING_COLLECTION = "recruiting"
DATABASE_NAME = "maybot"


def put_info(username, name, hackathon, roles, skills):
    """Updates the info a user, if user doesn't exit inserts a new user. Returns True if sucessful,
    otherwise False

    Keyword Arguments:
    username -- user's username as a string
    name -- user's name as a string
    hackathon -- hackathon attending as a string
    roles -- list of interested roles
    skills -- list of list of skills and their level from 1 to 5 as an integer
    """

    return maybot_db.put_info(DATABASE_NAME, RECRUITING_COLLECTION,
                              username, name, hackathon, roles, skills)


def get_info(username):
    """Returns the specified user from the recruiting collection, returns None if not found"""
    return maybot_db.get_info(DATABASE_NAME, RECRUITING_COLLECTION, username)


def filter_role(roles, hackathon):
    if not isinstance(roles, list):
        print ("Invalid Input!")
        return
    recruiting = maybot_db.access(DATABASE_NAME)[RECRUITING_COLLECTION]
    data = recruiting.find({"hackathon": hackathon})

    matches = []
    for user in data:
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
    """Deletes a user from the recruiting collection,
    returns True if user was removed, otherwise False"""
    return maybot_db.remove_user(DATABASE_NAME, RECRUITING_COLLECTION, username)
