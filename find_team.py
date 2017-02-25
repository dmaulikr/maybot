import time

import maybot_db

DATABASE_NAME = "maybot"
FINDING_COLLECTION = "finding"

def get_info(username):
    """Returns the specified user from the finding collection, returns None if not found"""

    return maybot_db.get_info(DATABASE_NAME, FINDING_COLLECTION, username)


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
    return maybot_db.put_info(DATABASE_NAME, FINDING_COLLECTION, username, name, hackathon, roles, skills)


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

    return maybot_db.remove_user(DATABASE_NAME, FINDING_COLLECTION, username)
