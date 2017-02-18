import json
import time

looking_users = {}

def new_user(username, name, roles, skills):
    """Inserts a new user into the database
    
    Keyword Arguments:
    username -- user's username as a string
    name -- user's name as a string
    roles -- list of interested roles
    skills -- dictionary of skills and their level from 1 to 5 as an integer
    """
    
    looking_users[username] = {'timestamp': time.time(),
                               "name": name, 
                               "roles": roles, 
                               "skills": skills}
                               
    with open('data.txt', 'w') as outfile:
        json.dumps(looking_users, outfile)

def load_data(database_name):
    """Loads data from database"""
    
    with open(database_name, 'r') as infile:
        looking_users = json.load(infile)
        
def get_user(username):
    """Returns a user's data
    
    Keyword Arguments:
    username -- user's username as a string"""
    
    return looking_users["users"][username]