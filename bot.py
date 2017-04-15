#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""An Kik bot implemented in Python.  MAYBOT = TINDER FOR HACKERS.  BY RAPHAEL KOH AND CLAYTON HALIM.

See https://github.com/kikinteractive/kik-python for Kik's Python API documentation.
"""

from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, PictureMessage, \
    SuggestedResponseKeyboard, TextResponse, StartChattingMessage
import find_team
import find_members
import active_users
import json
import os
from envparse import env


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

        for message in messages:
            user = self.kik_api.get_user(message.from_user)
            print(message.body)

            # Check if its the user's first message. Start Chatting messages are sent only once.
            if isinstance(message, StartChattingMessage):
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Hi {}!".format(user.first_name),
                    # keyboards are a great way to provide a menu of options for a user to respond with!
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

            # Check if the user has sent a text message.
            elif isinstance(message, TextMessage):
                user = self.kik_api.get_user(message.from_user)
                message_body = message.body
                username = None

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

                # START NEW CONVERSATION
                if message_body.split()[0].lower() in ["hi", "hello"]:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Hi {}!".format(user.first_name),
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="I'm May, aka June2.0.",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

                    searching = find_team.get_info(message.from_user)
                    recruiting = find_members.get_info(message.from_user)

                    if searching:
                        category = "team"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="You are currently searching for a team.  What would you like to do?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Edit My Preferences"),
                                                                     TextResponse("I want to find members instead!"),
                                                                     TextResponse(
                                                                         "I've found my match! <3  Remove me from the database!")])]))
                    elif recruiting:
                        category = "member"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="You are currently recruiting for team members.  What would you like to do?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Edit My Preferences"),
                                                                     TextResponse("I want to find teams instead!"),
                                                                     TextResponse(
                                                                         "I've found my match! <3  Remove me from the database!")])]))
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Are you ready to find your match?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Ready To Mingle!"),
                                                                     TextResponse(
                                                                         "No... I'm not ready...")])]))
                # END CONVERSATION
                elif "bye" in message_body.lower() or message_body in ["We'll find one without you </3", "No... I'm not ready..."]:
                    remove = True
                    # REMOVE FROM DATABASE
                    if message_body == "We'll find one without you </3":
                        if category == "team":
                            find_team.remove_user(message.from_user)
                        elif category == "member":
                            find_members.remove_user(message.from_user)
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="k thx bai"))
                elif message_body in ["I want to find members instead!", "I want to find teams instead!", "Edit My Preferences"]:
                    roles = []
                    skills = []
                    search_type = None
                    matched_user = None

                    # USER FINDING MEMBERS INSTEAD OF TEAMS
                    if category == "team":
                        data = find_team.get_info(message.from_user)
                        if message_body != "Edit My Preferences":
                            find_team.remove_user(message.from_user)
                            category = "member"
                    # USERS FINDING TEAMS INSTEAD OF MEMBERS
                    else:
                        data = find_members.get_info(message.from_user)
                        if message_body != "Edit My Preferences":
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
                # BEGIN SEARCH
                elif message_body == "Ready To Mingle!" or message_body.lower() == "add":
                    roles = []
                    skills = []
                    category = None
                    search_type = None
                    matched_user = None
                    hackathon = None
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Which hackathon are you going to?"))
                # REMOVE USER FROM DATABASE
                elif "remove" in message_body.lower():
                    remove = True
                    if category == "team":
                        find_team.remove_user(message.from_user)
                    if category == "member":
                        find_members.remove_user(message.from_user)
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Glad to be of service!  You have been removed from our database!\nHack long and prosper!"))
                # SELECT CATEGORY: TEAM OR MEMBER
                elif not category:
                    if not hackathon:
                        hackathon = message_body.lower()
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Are you looking for a team or an extra member?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                    elif message_body == "Team":
                        category = "team"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Awesome sauce! What are roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                    elif message_body == "Member":
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
                            body="Sorry, I didn't quite understand that. What are you looking for?",
                            # keyboards are a great way to provide a menu of options for a user to respond with!
                            keyboards=[
                                SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                # LOOKING FOR MEMBERS
                elif category == "member":
                    # INPUT HACKATHON (CHANGING PREFERENCES)
                    if not hackathon:
                        hackathon = message_body.lower()
                    # SELECT SEARCH TYPE: DETAILED OR QUICK
                    if not search_type:
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
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Cool! What roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                    # POST TEAM IN DB
                    elif message_body == "Yes please":
                        skills = ["temp"]
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Key in all skills (i.e. languages or frameworks) you are looking for! Separate each skill with ','!",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("No skills needed")])]))
                    elif not matched_user:
                        # CHOOSE ROLES
                        if message_body in self.positions:
                            if message_body not in roles:
                                roles.append(message_body)
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
                                body="Are you looking for anymore roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                        # LOOKING FOR MORE ROLES
                        elif message_body == "Moar roles pls":
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
                            # NO MATCHES FOUND!
                            else:
                                matched_user = -1
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Sorry, no matches found! Would you like us to notify you when there's a match?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Yes please"),
                                                   TextResponse("We'll find one without you </3")])]))
                    # DECLINE MATCHES
                    elif message_body in ["None of them", "Ew no"]:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Would you like to be discovered?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("Yes please"),
                                           TextResponse("We'll find one without you </3")])]))
                    # INPUT SKILLS
                    elif len(skills) > 0:
                        if message_body == "No skills needed":
                            skills = []
                        else:
                            skills = message_body.replace(" ", "").split(",")
                        find_members.put_info(message.from_user, user.first_name + " " + user.last_name, hackathon, roles, skills)
                        remove = True
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Yee!  You are now on the hunt!\nYou will be notified if you are matched!"
                        ))
                    # QUICK MATCH WITH SINGLE USER
                    elif message_body == "Hook me up!":
                        response_messages.append(TextMessage(
                            to=matched_user,
                            body="Hey, I'm " + message.from_user +
                                 "!\nWould you like to join my dank ass team and disrupt industries?"))
                    # DETAILED MATCH WITH LIST OF USERS
                    elif "I want " in message_body:
                        matched_user = message_body.replace("I want ", "")
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Contacting " + matched_user))
                        response_messages.append(TextMessage(
                            to=matched_user,
                            body="Hey, I'm " + message.from_user +
                                 "!\nWould you like to join my dank ass team and disrupt industries?"))
                    # INCORRECT INPUT
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Sorry, I didn't quite understand that."))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="You are currently looking for positions in:\n - " + "\n - ".join(roles)))
                        if username:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Would you like to contact " + username + "?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Would you like to be discovered?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))
                # LOOKING FOR A TEAM
                elif category == "team":
                    # INPUT HACKATHON (CHANGING PREFERENCES)
                    if not hackathon:
                        hackathon = message_body.lower()
                    # CHOOSE ROLES
                    if message_body in self.positions:
                        if message_body not in roles:
                            roles.append(message_body)
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
                            body="Are you looking for anymore roles to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                        ))
                    # LOOKING FOR MORE ROLES
                    elif message_body == "Moar roles pls":
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Cool! What roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.positions)))]))
                    # MATCHING WITH USERS
                    elif not matched_user:
                        if message_body == "I'm good":
                            result = find_members.filter_role(roles, hackathon)
                            # IF MATCH FOUND
                            if len(result) > 0:
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
                                matched_user = -1
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Sorry, not matches found! Would you like us to notify you when there's a match?",
                                    keyboards=[SuggestedResponseKeyboard(
                                        responses=[TextResponse("Yes please"),
                                                   TextResponse("We'll find one without you </3")])]))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Sorry, I didn't quite understand that. Would you like us to notify you when there's a match?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Yes please"),
                                               TextResponse("We'll find one without you </3")])]))
                    # CONTACT MATCH
                    elif message_body == "Hook me up!":
                        response_messages.append(TextMessage(
                            to=matched_user,
                            body="Hey, I'm " + message.from_user +
                                 "!\nWould you like to join my dank ass team and disrupt industries?"))
                    elif message_body == "Ew no":
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Would you like us to put you up for grabs?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("Yes please"),
                                           TextResponse("We'll find one without you </3")])]))
                    # ADD MEMBER TO DATABASE
                    elif message_body in ["Yes please", "Of course"]:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Nice!  What skills do you have? (i.e. languages, frameworks)\nIf multiple, separate with ','",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("No skills rip... :(")])]))
                    # ANYMORE SKILLS?
                    elif message_body.isdigit():
                        index = -2
                        for i in range(len(skills)):
                            if skills[i][1] == 0:
                                if index == -1:
                                    index = i
                                    break
                                else:
                                    skills[i][1] = int(message_body)
                                    index = -1
                        # MORE SKILLS
                        if index > -1:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="How proficient are you with " + skills[index][0] + " on a scale from 1 to 5?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("1"), TextResponse("2"), TextResponse("3"),
                                               TextResponse("4"), TextResponse("5")])]))
                        # NO MORE SKILLS
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Your skills include: " + ", ".join(elem[0] for elem in skills) +
                                     "\nDo you have any more skills?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Of course"), TextResponse("Nah I'm good")])]
                            ))
                    # ADD USER TO DATA
                    elif message_body in ["Nah I'm good", "No skills rip... :("]:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Right on!  You are now single ready to mingle!\nYou will be notified if you are matched!"
                        ))
                        find_team.put_info(message.from_user, user.first_name + " " + user.last_name, hackathon, roles, skills)
                        remove = True
                    # ADD SKILLS
                    elif len(roles) > 0:
                        message_body = message_body.replace(" ", "").split(",")
                        message_body = list(filter(lambda x: x != skills, message_body))
                        skills.extend([[elem, 0] for elem in message_body])
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="How proficient are you with " + message_body[0] + " on a scale from 1 to 5?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("1"), TextResponse("2"), TextResponse("3"),
                                           TextResponse("4"), TextResponse("5")])]))
                        '''
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("⭐"), TextResponse("⭐⭐"), TextResponse("⭐⭐⭐"),
                                           TextResponse("⭐⭐⭐⭐"), TextResponse("⭐⭐⭐⭐⭐")])]))
                            '''
                elif message_body.lower() == "profile":
                    # Send the user a response along with their profile picture (function definition is below)
                    response_messages += self.get_profile(user, message)
                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Sorry, I didn't quite understand that. What are you looking for?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                if remove:
                    active_users.remove_user(message.from_user)
                else:
                    active_users.put_info(message.from_user, hackathon, roles, category, search_type, matched_user, skills)

            # If its not a text message, give them another chance to use the suggested responses
            else:
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Sorry, I didn't quite understand that. What are you looking for?",
                    # keyboards are a great way to provide a menu of options for a user to respond with!
                    keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

            # We're sending a batch of messages. We can send up to 25 messages at a time (with a limit of
            # 5 messages per user).

            self.kik_api.send_messages(response_messages)

        return Response(status=200)

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

    @staticmethod
    def contact(user):
        request.post(
            'https://api.kik.com/v1/message',
            auth=('maybot', '3a42f662-6593-49e3-bcfe-ddf805a21726'),
            headers={
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'messages': [
                    {
                        'body': 'Hey, would you like to join my dank ass team and disrupt industries?',
                        'to': user,
                        'type': 'text'
                    }
                ]
            })
        )


if __name__ == "__main__":
    """ Main program """
    local = False
    if local:
        env.read_envfile()
    KIK_USERNAME = str(os.environ.get('APP_NAME'))
    KIK_API_KEY = str(os.environ.get('KIK_API_KEY'))
    port = int(os.environ.get('PORT', 8080))
    webhook = str(os.environ.get('WEBHOOK'))
    print(KIK_USERNAME, KIK_API_KEY, port, webhook)
    kik = KikApi(KIK_USERNAME, KIK_API_KEY)
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook=webhook))
    app = KikBot(kik, __name__)
    app.run(port=port, host="0.0.0.0", debug=True)
