import json
import os
import time

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


def put_info(username, hackathon, roles, skills):
    data = load_data(FIND_MEMBERS)

    if username not in data["users"]:
        data["users"][username] = {}
    data["users"][username]["hackathon"] = hackathon
    data["users"][username]["roles"] = roles
    data["users"][username]["skills"] = skills
    data["users"][username]["timestamp"] = time.time()
    write_data(data, FIND_MEMBERS)


def get_info(username):
    data = load_data(FIND_MEMBERS)
    if username in data["users"]:
        return data["users"][username]
    else:
        return None


def filter_role(roles, hackathon):
    if not isinstance(roles, list):
        print ("Invalid Input!")
        return
    data = load_data(FIND_MEMBERS)
    matches = []
    for user in data["users"]:
        user_hackathon = data["users"][user]["hackathon"]
        if user_hackathon != hackathon:
            continue
        user_roles = data["users"][user]["roles"]
        user_skills = data["users"][user]["skills"]
        score = score_user(roles, user_roles)
        timestamp = data["users"][user]["timestamp"]
        if score > 0:
            matches.append([user, score, timestamp, user_roles, user_skills])
    matches = sorted(matches, key=lambda match: (match[1] * (-1), match[2]))
    return matches


# scores users based on how many matches
def score_user(roles, user_roles):
    score = reduce(lambda x, y: (x + 1) if (y.lower() in (role.lower() for role in roles)) else x, user_roles, 0)
    return score


def remove_user(username):
    data = load_data(FIND_MEMBERS)
    if username in data["users"]:
        del data["users"][username]
    write_data(data, FIND_MEMBERS)
