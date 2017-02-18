import json

FIND_MEMBERS = "find_members_users.txt"

def load_data(database_name):
    """Loads data from database"""
    
    data = {}
    with open(database_name, 'r') as infile:
        data = json.load(infile)
        
def write_data(data, database_name):
    with open(database_name, 'w') as outfile:
        json.dump(data, outfile)

def put_roles(username, role):
    recruiting = load_data(FIND_MEMBERS)
    recruiting["users"][username]["roles"].append(role)
    write_data(recruiting, FIND_MEMBERS)
    
def get_roles(username):
    recruiting = load_data(FIND_MEMBERS)
    return recruiting["users"][username]["roles"]
    