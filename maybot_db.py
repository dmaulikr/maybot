"""Allows access to maybot mongoDB database"""
import time
import pymongo

def access(db_name):
    """Returns maybot database object"""

    uri = ""
    with open("config.cfg", "r") as config:
        uri = config.readline().strip()

    return pymongo.MongoClient(uri)[db_name]

def get_info(database, collection, username):
    """Returns the specified user from a collection, returns None if not found"""
    database = access(database)
    search = database[collection].find_one({"username": username})

    if search.count() > 0:
        return search[0]
    else:
        return None

def put_info(database, collection, username, name, hackathon, roles, skills):
    """Updates the info a user, if user doesn't exit inserts a new user. Returns True if sucessful,
    otherwise False

    Keyword Arguments:
    username -- user's username as a string
    name -- user's name as a string
    hackathon -- hackathon attending as a string
    roles -- list of interested roles
    skills -- list of list of skills and their level from 1 to 5 as an integer
    """
    data = access(database)[collection]
    user = {"name": name,
            'timestamp': time.time(),
            "hackathon": hackathon,
            "roles": roles,
            "skills": skills}
    return data.update_one({"username": username}, {"$set": user}, upsert=True).acknowledged

def remove_user(database, collection, username):
    """Deletes a user from the collection,
    returns True if user was removed, otherwise False"""
    database = access(database)
    return database[collection].delete_one({"username": username}).acknowledged
    