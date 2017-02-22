import json
import time

FIND_TEAM = "find_team_users.txt"


def load_data(database_name):
    """Loads data from database"""
    with open(database_name, 'r') as infile:
        data = json.load(infile)
    return data


def write_data(data, database_name):
    with open(database_name, 'w') as outfile:
        json.dump(data, outfile)


def get_info(username):
    data = load_data(FIND_TEAM)
    if username in data["users"]:
        return data["users"][username]
    else:
        return None


def new_user(username, name, roles, skills):
    """Inserts a new user into the database
    
    Keyword Arguments:
    username -- user's username as a string
    name -- user's name as a string
    roles -- list of interested roles
    skills -- dictionary of skills and their level from 1 to 5 as an integer
    """
    data = load_data(FIND_TEAM)
    data[username] = {'timestamp': time.time(),
                      "name": name,
                      "roles": roles,
                      "skills": skills}
    write_data(data, FIND_TEAM)


def filter_role(roles):
    if not isinstance(roles, list):
        print ("Invalid Input!")
        return
    data = load_data(FIND_TEAM)
    matches = []
    for user in data["users"]:
        user_roles = data["users"][user]["roles"]
        score = score_user(roles, user_roles)
        timestamp = data["users"][user]["timestamp"]
        if score > 0:
            matches.append([user, score, timestamp, user_roles])
    matches = sorted(matches, key=lambda match: (match[1] * (-1), match[2]))
    return matches


# scores users based on how many matches
def score_user(roles, user_roles):
    score = reduce(lambda x, y: (x + 1) if (y.lower() in (role.lower() for role in roles)) else x, user_roles, 0)
    return score

def remove_user(username):
    data = load_data(FIND_TEAM)
    if username in data["users"]:
        del data["users"][username]
    write_data(data, FIND_TEAM)
