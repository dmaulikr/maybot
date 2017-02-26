import time
import maybot_db

DATABASE_NAME = "maybot"
ACTIVE_COLLECTION = "active"


def put_info(username, hackathon, roles, looking, search, match, skills):
    """Updates the info a user, if user doesn't exit inserts a new user. Returns True if successful,
    otherwise False
    """
    data = maybot_db.access(DATABASE_NAME)[ACTIVE_COLLECTION]
    user = {"timestamp": time.time(),
            "hackathon": hackathon,
            "roles": roles,
            "looking": looking,
            "search": search,
            "match": match,
            "skills": skills}

    return data.update_one({"username": username}, {"$set": user}, upsert=True).acknowledged


def get_info(username):
    return maybot_db.get_info(DATABASE_NAME, ACTIVE_COLLECTION, username)


def remove_user(username):
    return maybot_db.remove_user(DATABASE_NAME, ACTIVE_COLLECTION, username)
