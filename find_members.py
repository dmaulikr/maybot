import json
import time

recruiting_users = {}

def new_user(username, roles):
    """Inserts a new user into the database
    
    Keyword Arguments:
    username -- user's username as a string
    skills -- dictionary of skills and their level from 1 to 5 as an integer
    """
    
    recruiting_users[username] = {"roles": roles}
                               
    with open('data.txt', 'w') as outfile:
        json.dumps(recruiting_users, outfile)

def load_data(database_name):
    """Loads data from database"""
    
    global recruiting_users
    
    with open(database_name, 'r') as infile:
        recruiting_users = json.load(infile)
        
def get_user(username):
    """Returns a user's data
    
    Keyword Arguments:
    username -- user's username as a string"""
    
    return recruiting_users["users"][username]
