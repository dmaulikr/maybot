"""Allows access to maybot mongoDB database"""
import time
import pymongo
from bot import local
from envparse import env
import os


def access(db_name):
    """Returns maybot database object"""

    if local:
        env.read_envfile()
    uri = str(os.environ.get('DB_URI'))

    return pymongo.MongoClient(uri)[db_name]


def get_info(database, collection, username):
    """Returns the specified user from a collection, returns None if not found"""
    database = access(database)
    search = database[collection].find_one({"username": username})

    return search


def put_info(database, collection, username, name, hackathon, roles, skills):
    """Updates the info a user, if user doesn't exit inserts a new user. Returns True if successful,
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
    