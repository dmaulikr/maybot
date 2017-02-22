import json
import os.path

FIND_MEMBERS = "recruiting_users.txt"

def load_data(database_name):
    """Loads data from database"""
    with open(database_name, 'r') as infile:
        data = json.load(infile)
    return data
        
def write_data(data, database_name):
    with open(database_name, 'w') as outfile:
        json.dump(data, outfile)

def put_info(username, roles, looking, search, match):
    recruiting = load_data(FIND_MEMBERS)

    if username not in recruiting["users"]:
        recruiting["users"][username] = {}
    recruiting["users"][username]["roles"] = roles
    recruiting["users"][username]["looking"] = looking
    recruiting["users"][username]["search"] = search
    recruiting["users"][username]["match"] = match
    write_data(recruiting, FIND_MEMBERS)
    
def get_info(username):
    recruiting = load_data(FIND_MEMBERS)
    if username in recruiting["users"]:
        return recruiting["users"][username]
    else: return None
    