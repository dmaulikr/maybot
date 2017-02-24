"""Allows access to maybot mongoDB database"""
import pymongo

def access(db_name):
    """Returns maybot database object"""

    uri = ""
    with open("config.cfg", "r") as config:
        uri = config.readline().strip()

    print(uri)
    return pymongo.MongoClient(uri)[db_name]
    