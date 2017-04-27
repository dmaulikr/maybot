#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""An Kik bot implemented in Python.  MAYBOT = TINDER FOR HACKERS.  BY RAPHAEL KOH AND CLAYTON HALIM.

See https://github.com/kikinteractive/kik-python for Kik's Python API documentation.
"""

from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, PictureMessage, \
    SuggestedResponseKeyboard, TextResponse, StartChattingMessage, ScanDataMessage
import find_team
import find_members
import active_users
import os
from envparse import env

# DEBUG variables
local = False
debug = False

'''
    GENERAL OVERVIEW MAP OF CHATBOT:

    0 - Home Screen
    New Member:
        1 - Hackathon
        2 - Looking for Team/Member
    Member:
        3 - Search Type
        4 - Roles
        5 - Confirm Roles
        6 - Match
        If no matches:
            7 - Discovered
            8 - Skills
    Team:
        3 - Roles
        4 - Confirm Roles
        5 - Match
        If no matches:
            6 - Discovered
            7 - Skills
            8 - Skill Levels
'''


class KikBot(Flask):
    """ Flask kik bot application class"""

    positions = ["Front End", "Back End", "Android", "iOS", "Web Dev", "Hardware"]

    def __init__(self, kik_api, import_name, static_path=None, static_url_path=None, static_folder="static",
                 template_folder="templates", instance_path=None, instance_relative_config=False,
                 root_path=None):

        self.kik_api = kik_api

        super(KikBot, self).__init__(import_name, static_path, static_url_path, static_folder, template_folder,
                                     instance_path, instance_relative_config, root_path)

        self.route("/incoming", methods=["POST"])(self.incoming)

    def incoming(self):
        """Handle incoming messages to the bot. All requests are authenticated using the signature in
        the 'X-Kik-Signature' header, which is built using the bot's api key (set in main() below).
        :return: Response
        """
        # verify that this is a valid request
        if not self.kik_api.verify_signature(
                request.headers.get("X-Kik-Signature"), request.get_data()):
            return Response(status=403)

        messages = messages_from_json(request.json["messages"])
        response_messages = []

        roles = []  # POSITIONS/ROLES LOOKING TO FILL
        skills = []  # SKILLS USER HAS (i.e. languages, frameworks)
        category = None  # WHO YOU ARE SEARCHING FOR
        search_type = None  # DETAILED OR QUICK SEARCH
        matched_user = None  # WHO YOU ARE PAIRED WITH
        hackathon = None    # WHICH HACKATHON
        level = 0           # KEEP TRACK OF WHERE USER IS (REFER TO OVERVIEW)

        for message in messages:
            user = self.kik_api.get_user(message.from_user)

            # Check if its the user's first message. Start Chatting messages are sent only once.
            if isinstance(message, StartChattingMessage) or isinstance(message, ScanDataMessage):
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Hi {}!".format(user.first_name)))
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="I'm May, aka June2.0, and I'm here to hook you up with the best team for this hackathon!"))
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="To start looking for potential matches or if you just wanna start chatting with me, just type 'hi' or 'hello'!  Try it now!"))

            # Check if the user has sent a text message.
            elif isinstance(message, TextMessage):
                user = self.kik_api.get_user(message.from_user)
                message_body = message.body

                # IF USER IS TO BE REMOVED FROM ACTIVE USERS
                remove = False

                info = active_users.get_info(message.from_user)
                if info:
                    roles = info["roles"]
                    skills = info["skills"]
                    category = info["looking"]
                    search_type = info["search"]
                    matched_user = info["match"]
                    hackathon = info["hackathon"]
                    level = info["level"]

                # Help menu
                if message_body.lower() == "help":
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="1. 'hi'/'hello' - Start new conversation\n2. 'reset' - Reset current conversation\n3. 'bye' - End conversation\n4. 'code' - View MayBot's Kik Code"))
                # Reset converation
                elif message_body.lower() == "reset":
                    roles = []
                    skills = []
                    category = None
                    search_type = None
                    matched_user = None
                    hackathon = None
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Your current conversation has been reset!"))
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Your current conversation has been reset!"))
                    results = self.home(message, user.first_name)
                    if results[0]:
                        category = results[0]
                    response_messages += results[1]
                # View Kik Code
                elif any(s in message_body.lower() for s in ['code', 'scan']):
                    response_messages.append(PictureMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        pic_url='http://i.imgur.com/vCy4u8B.png'
                    ))
                # START NEW CONVERSATION
                elif message_body.split()[0].lower() in ["hi", "hello"]:
                    level = 0
                    results = self.home(message, user.first_name)
                    if results[0]:
                        category = results[0]
                    response_messages += results[1]
                # END CONVERSATION
                elif message_body.lower() == "bye":
                    remove = True
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="I'll be here when you need me!  Goodbye for now!"))
                elif message_body.lower() == "profile":
                    # Send the user a response along with their profile picture (function definition is below)
                    response_messages += self.get_profile(user, message)

                # HOME
                elif level == 0:
                    # BEGIN SEARCH
                    if message_body == "Ready To Mingle!":
                        roles = []
                        skills = []
                        category = None
                        search_type = None
                        matched_user = None
                        hackathon = None
                        level = 1
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Which hackathon are you going to?"))
                    # EXIT
                    elif message_body == "No... I'm not ready...":
                        remove = True
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="k thx bai"))
                    # REMOVE USER FROM DATABASE
                    elif message_body == "I've found my match! <3  Remove me from the database!":
                        remove = True
                        if category == "team":
                            find_team.remove_user(message.from_user)
                        if category == "member":
                            find_members.remove_user(message.from_user)
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Glad to be of service!  You have been removed from our database!\nHack long and prosper!"))
                    # CHANGE CATEGORY
                    elif message_body in ["I want to find members instead!", "I want to find teams instead!",
                                          "Reset My Preferences"]:
                        roles = []
                        skills = []
                        search_type = None
                        matched_user = None
                        level = 3

                        # USER FINDING MEMBERS INSTEAD OF TEAMS
                        if category == "team":
                            data = find_team.get_info(message.from_user)
                            if message_body != "Reset My Preferences":
                                find_team.remove_user(message.from_user)
                                category = "member"
                        # USERS FINDING TEAMS INSTEAD OF MEMBERS
                        else:
                            data = find_members.get_info(message.from_user)
                            if message_body != "Reset My Preferences":
                                find_members.remove_user(message.from_user)
                                category = "team"

                        hackathon = data["hackathon"]

                        if category == "team":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Awesome sauce! What are roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Quick Search or Detailed Search?",
                                keyboards=[
                                    SuggestedResponseKeyboard(
                                        responses=[TextResponse("<3 Quickies"), TextResponse("Mmmm details")])]))
                    # INCORRECT RESPONSE
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Sorry, I didn't understand that."))
                        results = self.home(message, user.first_name)
                        response_messages += results[1]

                # HACKATHON
                elif level == 1:
                    hackathon = message_body.lower()
                    level = 2
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Are you looking for a team or an extra member?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

                # SELECT CATEGORY: TEAM OR MEMBER
                elif level == 2:
                    if message_body == "Team":
                        level = 3
                        category = "team"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Awesome sauce! What are roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                    elif message_body == "Member":
                        level = 3
                        category = "member"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Quick Search or Detailed Search?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(
                                    responses=[TextResponse("<3 Quickies"), TextResponse("Mmmm details")])]))
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Sorry, I didn't understand that.  Are you looking for a team or an extra member?",
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

                # SEARCHING FOR MEMBERS
                elif category == "member":
                    # SELECT SEARCH TYPE: DETAILED OR QUICK
                    if level == 3:
                        if "quick" in message_body.lower():
                            search_type = "quick"
                        elif "detail" in message_body.lower():
                            search_type = "detailed"
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't quite understand that."))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Quick Search or Detailed Search?",
                                # keyboards are a great way to provide a menu of options for a user to respond with!
                                keyboards=[
                                    SuggestedResponseKeyboard(
                                        responses=[TextResponse("<3 Quickies"), TextResponse("Mmmm details")])]))
                            continue

                        level = 4
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Cool! What roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.positions)))]))

                    # CHOOSE ROLES
                    elif level == 4:
                        if message_body in self.positions:
                            level = 5
                            roles.append(message_body)
                            roles = list(set(roles))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                        # INCORRECT RESPONSE
                        elif len(roles) == 0:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that.  What roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                        else:
                            level = 5
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))

                    elif level == 5:
                        # LOOKING FOR MORE ROLES
                        if message_body == "Moar roles pls":
                            level = 4
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Cool! What roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                        # SEARCH FOR MATCH
                        elif message_body == "I'm good":
                            result = find_team.filter_role(roles, hackathon)
                            # IF MATCH FOUND
                            if len(result) > 0:
                                level = 6
                                # QUICK SEARCH
                                if search_type == "quick":
                                    result = result[0]
                                    username = result[0]
                                    user_matched = self.kik_api.get_user(username)
                                    matched_user = username
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="You have a match!"
                                    ))
                                    response_messages += self.get_profile(user_matched, message, result[3], result[4])
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Would you like to contact " + username + "?",
                                        keyboards=[SuggestedResponseKeyboard(
                                            responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                                # DETAILED SEARCH
                                else:
                                    # TOP 5 MATCHES
                                    result = result[:5]
                                    matched_user = result
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Potential Team Members found!"
                                    ))
                                    output_msg = ""
                                    for user in result:
                                        output_msg += "User: " + user[0] + "\n"
                                        output_msg += "Looking to fill:\n - " + "\n - ".join(user[3]) + "\n"
                                        user_skills = list(map(lambda x: x[0] + ": " + str(x[1]), user[4]))
                                        output_msg += "Skills:\n - " + "\n - ".join(user_skills) + "\n"
                                        output_msg += "--------------------\n"
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body=output_msg
                                    ))
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Who would you like to contact?",
                                        keyboards=[SuggestedResponseKeyboard(
                                            responses=list(map(lambda x: TextResponse("I want " + x[0]), result)) +
                                                      [TextResponse("None of them")])]))
                            # NO MATCHES FOUND
                            else:
                                level = 7
                                matched_user = None
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Sorry, no matches found! Would you like me to notify you when there's a match?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Yes please"),
                                                   TextResponse("We'll find one without you </3")])]))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))

                    # MATCHED
                    elif level == 6:
                        # QUICK MATCH WITH SINGLE USER
                        if message_body == "Hook me up!":
                            remove = True
                            response_messages.append(TextMessage(
                                to=matched_user,
                                body="Hey, I'm " + message.from_user +
                                     "!\nWould you like to join my dank ass team and disrupt industries?"))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="We've messaged " + matched_user + "!\nThey will be in touch with you if they would like to join your team!"))
                        # DETAILED MATCH WITH LIST OF USERS
                        elif "I want " in message_body:
                            remove = True
                            matched_user = message_body.replace("I want ", "")
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="We've messaged " + matched_user + "!\nThey will be in touch with you if they would like to join your team!"))
                            response_messages.append(TextMessage(
                                to=matched_user,
                                body="Hey, you've been matched with " + message.from_user +
                                     "!\nWould you like to join their dank team and disrupt industries? If so, shoot them a message!"))
                        # DECLINE MATCHES
                        elif message_body in ["None of them", "Ew no"]:
                            level = 7
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Would you like to be discovered?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))
                        # INCORRECT RESPONSE
                        # QUICK SEARCH
                        elif search_type == "quick":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Would you like to contact " + matched_user + "?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                        # DETAILED SEARCH
                        else:
                            output_msg = ""
                            for user in result:
                                output_msg += "User: " + user[0] + "\n"
                                output_msg += "Looking to fill:\n - " + "\n - ".join(user[3]) + "\n"
                                user_skills = list(map(lambda x: x[0] + ": " + str(x[1]), user[4]))
                                output_msg += "Skills:\n - " + "\n - ".join(user_skills) + "\n"
                                output_msg += "--------------------\n"
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body=output_msg
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Who would you like to contact?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse("I want " + x[0]), result)) +
                                              [TextResponse("None of them")])]))

                    # CHECK IF USER WANTS TO BE INCLUDED IN DB
                    elif level == 7:
                        if message_body == "Yes please":
                            level = 8
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Key in all skills (i.e. languages or frameworks) you are looking for! Separate each skill with ','!",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills needed")])]))
                        # END CONVERSATION
                        elif message_body == "We'll find one without you </3":
                            remove = True
                            if category == "team":
                                find_team.remove_user(message.from_user)
                            elif category == "member":
                                find_members.remove_user(message.from_user)
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="k thx bai"))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. Would you like to be discovered?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))

                    # INPUT SKILLS
                    elif level == 8:
                        if message_body == "No skills needed":
                            skills = []
                        elif message_body == "No, I want to change them!":
                            skills = []
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Key in all skills (i.e. languages or frameworks) you are looking for! Separate each skill with ','!",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills needed")])]))
                            continue
                        # KEY IN SKILLS
                        elif len(skills) == 0:
                            skills = message_body.replace(" ", "").split(",")
                            skills_str = ', '.join(skills)
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are looking for the following skills: " + skills_str,
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No, I want to change them!"),
                                               TextResponse("Yup, all good!")])]))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are these ok?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No, I want to change them!"),
                                               TextResponse("Yup, all good!")])]))
                            continue
                        # INCORRECT RESPONSE
                        elif message_body != "Yup, all good!":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. You are looking for the following skills: " + skills_str,
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No, I want to change them!"),
                                               TextResponse("Yup, all good!")])]))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are these ok?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No, I want to change them!"),
                                               TextResponse("Yup, all good!")])]))
                            continue

                        find_members.put_info(message.from_user, user.first_name + " " + user.last_name, hackathon,
                                              roles, skills)
                        remove = True
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Yee!  You are now on the hunt!\nYou will be notified if you are matched!"
                        ))

                # SEARCHING FOR TEAM
                elif category == "team":
                    if level == 3:
                        # CHOOSE ROLES
                        if message_body in self.positions:
                            level = 4
                            roles.append(message_body)
                            roles = list(set(roles))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                        # INCORRECT RESPONSE
                        elif len(roles) == 0:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that.  What roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                        else:
                            level = 4
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))

                    elif level == 4:
                        # LOOKING FOR MORE ROLES
                        if message_body == "Moar roles pls":
                            level = 3
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Cool! What roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                        elif message_body == "I'm good":
                            result = find_members.filter_role(roles, hackathon)
                            # IF MATCH FOUND
                            if len(result) > 0:
                                level = 5
                                result = result[0]
                                username = result[0]
                                user_matched = self.kik_api.get_user(username)
                                matched_user = username
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="You have a match!"
                                ))
                                response_messages += self.get_profile(user_matched, message, result[3], result[4], True)
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Would you like to contact " + username + "?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                            # NO MATCHES FOUND!
                            else:
                                level = 6
                                matched_user = None
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Sorry, no matches found! Would you like me to notify you when there's a match?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Yes please"),
                                                   TextResponse("We'll find one without you </3")])]))
                        # INCORRECT RESPONSE
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. You are currently looking for roles in: " + ", ".join(roles),
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for any more roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))

                    elif level == 5:
                        # CONTACT MATCH
                        if message_body == "Hook me up!":
                            remove = True
                            response_messages.append(TextMessage(
                                to=matched_user,
                                body="Hey, you've been matched with " + message.from_user +
                                     "!\nIf you'd like them on your team, send them a message!"))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                body="We've contacted " + matched_user +
                                     "!\nThey'll be in touch with you if they would like you on their team!"))
                        elif message_body == "Ew no":
                            level = 6
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Would you like me to put you up for grabs?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. Would you like to contact " + matched_user + "?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))

                    # CHECK IF USER WANTS TO BE INCLUDED IN DB
                    elif level == 6:
                        # ADD MEMBER TO DATABASE
                        if message_body == "Yes please":
                            level = 7
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Nice!  What skills do you have? (i.e. languages, frameworks)\nIf multiple, separate with ','",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills rip... :(")])]))
                        # END CONVERSATION
                        elif message_body == "We'll find one without you </3":
                            remove = True
                            if category == "team":
                                find_team.remove_user(message.from_user)
                            elif category == "member":
                                find_members.remove_user(message.from_user)
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="k thx bai"))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't understand that. Would you like me to put you up for grabs?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))

                    # SKILLS
                    elif level == 7:
                        if message_body == "No skills rip... :(":
                            remove = True
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Right on!  You are now single ready to mingle!\nYou will be notified if you are matched!"
                            ))
                            find_team.put_info(message.from_user, user.first_name + " " + user.last_name, hackathon,
                                               roles, skills)
                        elif message_body == "Of course":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="What other skills do you have? (i.e. languages, frameworks)\nIf multiple, separate with ','",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills rip... :(")])]))
                        elif message_body == "Nah I'm good":
                            level = 8
                        elif message_body == "I want to change my skills":
                            skills = []
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="What skills do you have? (i.e. languages, frameworks)\nIf multiple, separate with ','",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills rip... :(")])]))
                        # ADD SKILLS
                        else:
                            message_body = message_body.replace(" ", "").split(",")
                            message_body = list(filter(lambda x: not(any(x in skill for skill in skills)), message_body))
                            skills.extend([[elem, 0] for elem in message_body])
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Your skills include: " + ", ".join(elem[0] for elem in skills) +
                                     "\nDo you have any more skills?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Of course"), TextResponse("Nah I'm good"), TextResponse("I want to change my skills")])]
                            ))

                    # PICK SKILL LEVEL
                    elif level == 8:
                        if message_body == "All good!":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Right on!  You are now single ready to mingle!\nYou will be notified if you are matched!"
                            ))
                            find_team.put_info(message.from_user, user.first_name + " " + user.last_name, hackathon,
                                               roles, skills)
                            remove = True
                        elif message_body == "Change Skills":
                            level = 7
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="What skills do you have? (i.e. languages, frameworks)\nIf multiple, separate with ','",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("No skills rip... :(")])]))
                        # first skill
                        elif not message_body.isdigit() and (skills[0][1] == 0 or message_body == "Change Skill Points"):
                            # reset skill points
                            if message_body == "Change Skill Points":
                                skills = list(map(lambda x: [x[0], 0], skills))

                            response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="How proficient are you with " + skills[0][0] + " on a scale from 1 to 5?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("1"), TextResponse("2"), TextResponse("3"),
                                                   TextResponse("4"), TextResponse("5")])]))
                            '''
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("⭐"), TextResponse("⭐⭐"), TextResponse("⭐⭐⭐"),
                                               TextResponse("⭐⭐⭐⭐"), TextResponse("⭐⭐⭐⭐⭐")])]))
                            '''
                        # subsequent skills
                        else:
                            index = -2
                            for i in range(len(skills)):
                                if skills[i][1] == 0:
                                    if index == -1:
                                        # curr skill
                                        index = i
                                        break
                                    else:
                                        index = -1
                                        # prev skill
                                        if message_body.isdigit():
                                            skills[i][1] = int(message_body)
                                        # INCORRECT RESPONSE
                                        else:
                                            response_messages.append(TextMessage(
                                                to=message.from_user,
                                                chat_id=message.chat_id,
                                                body="Please choose from the options given.\nHow proficient are you with " + skills[i][0] + " on a scale from 1 to 5?",
                                                keyboards=[SuggestedResponseKeyboard(
                                                    responses=[TextResponse("1"), TextResponse("2"), TextResponse("3"),
                                                               TextResponse("4"), TextResponse("5")])]))
                                            break
                            # MORE SKILLS
                            if index > -1:
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="How proficient are you with " + skills[index][0] + " on a scale from 1 to 5?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("1"), TextResponse("2"), TextResponse("3"),
                                                   TextResponse("4"), TextResponse("5")])]))
                            # INCORRECT RESPONSE
                            elif len(response_messages) > 0:
                                continue
                            # NO MORE SKILLS
                            else:
                                skills_str = list(map(lambda x: x[0] + ": " + str(x[1]), skills))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Your skills are:\n - " + "\n - ".join(skills_str),
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Of course"), TextResponse("Nah I'm good"),
                                                   TextResponse("I want to change my skills")])]
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Are these ok?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("All good!"), TextResponse("Change Skills"),
                                                   TextResponse("Change Skill Points")])]
                                ))

                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Sorry, I didn't understand that.  Type 'help' for a list of commands!"))
                if remove:
                    active_users.remove_user(message.from_user)
                else:
                    active_users.put_info(message.from_user, hackathon, roles, category, search_type, matched_user, skills, level)

            # If its not a text message, give them another chance to use the suggested responses
            else:
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Sorry, I didn't understand that.  Type 'help' for a list of commands!"))

            # We're sending a batch of messages. We can send up to 25 messages at a time (with a limit of
            # 5 messages per user).
            self.kik_api.send_messages(response_messages)

        return Response(status=200)

    @staticmethod
    def home(message, name):
        results = [False, []]

        searching = find_team.get_info(message.from_user)
        recruiting = find_members.get_info(message.from_user)

        if searching:
            results[0] = "team"
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Welcome back, {}!".format(name),
                # keyboards are a great way to provide a menu of options for a user to respond with!
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Reset My Preferences"),
                                                         TextResponse("I want to find members instead!"),
                                                         TextResponse(
                                                             "I've found my match! <3  Remove me from the database!")])]))
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="You are currently searching for a team.  What would you like to do?",
                # keyboards are a great way to provide a menu of options for a user to respond with!
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Reset My Preferences"),
                                                         TextResponse("I want to find members instead!"),
                                                         TextResponse(
                                                             "I've found my match! <3  Remove me from the database!")])]))
        elif recruiting:
            results[0] = "member"
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Welcome back, {}!".format(name),
                # keyboards are a great way to provide a menu of options for a user to respond with!
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Reset My Preferences"),
                                                         TextResponse("I want to find teams instead!"),
                                                         TextResponse(
                                                             "I've found my match! <3  Remove me from the database!")])]))
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="You are currently recruiting for team members.  What would you like to do?",
                # keyboards are a great way to provide a menu of options for a user to respond with!
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Reset My Preferences"),
                                                         TextResponse("I want to find teams instead!"),
                                                         TextResponse(
                                                             "I've found my match! <3  Remove me from the database!")])]))
        else:
            results.append(False)
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Hi there, {}!".format(name),
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Ready To Mingle!"),
                                                         TextResponse(
                                                             "No... I'm not ready...")])]))
            results[1].append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Are you ready to find your match?",
                # keyboards are a great way to provide a menu of options for a user to respond with!
                keyboards=[
                    SuggestedResponseKeyboard(responses=[TextResponse("Ready To Mingle!"),
                                                         TextResponse(
                                                             "No... I'm not ready...")])]))
        return results


    @staticmethod
    def get_profile(user, message, roles=None, skills=None,team_search=False):
        """Function to check if user has a profile picture and returns appropriate messages.
        :param user: Kik User Object (used to acquire the URL the profile picture)
        :param message: Kik message received by the bot
        :return: Message
        """

        messages_to_send = []
        profile_picture = user.profile_pic_url

        if profile_picture is not None:
            messages_to_send.append(
                # Another type of message is the PictureMessage - your bot can send a pic to the user!
                PictureMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    pic_url=profile_picture
                ))
        profile_picture_response = "Name: " + user.first_name + " " + user.last_name
        profile_picture_response += "\nLooking to fill\n - " + "\n - ".join(roles)
        if team_search:
            profile_picture_response += "\nPreferred Skills:\n - " + "\n - ".join(skills)
        else:
            skills = list(map(lambda x: x[0] + ": " + str(x[1]), skills))
            profile_picture_response += "\nSkills:\n - " + "\n - ".join(skills)

        messages_to_send.append(
            TextMessage(to=message.from_user, chat_id=message.chat_id, body=profile_picture_response))

        return messages_to_send


if __name__ == "__main__":
    """ Main program """
    if local:
        env.read_envfile()
    KIK_USERNAME = str(os.environ.get('APP_NAME'))
    KIK_API_KEY = str(os.environ.get('KIK_API_KEY'))
    port = int(os.environ.get('PORT', 8080))
    webhook = str(os.environ.get('WEBHOOK'))
    kik = KikApi(KIK_USERNAME, KIK_API_KEY)
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook=webhook))
    app = KikBot(kik, __name__)
    app.run(port=port, host="0.0.0.0", debug=debug)
