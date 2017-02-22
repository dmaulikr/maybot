#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""An example Kik bot implemented in Python.

It's designed to greet the user, send a suggested response and replies to them with their profile picture.
Remember to replace the BOT_USERNAME_HERE, BOT_API_KEY_HERE and WEBHOOK_HERE fields with your own.

See https://github.com/kikinteractive/kik-python for Kik's Python API documentation.

Apache 2.0 License

(c) 2016 Kik Interactive Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

"""

from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, PictureMessage, \
    SuggestedResponseKeyboard, TextResponse, StartChattingMessage
import find_team
import user_modifier
import json


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
        category = None  # WHO YOU ARE SEARCHING FOR
        search = None  # DETAILED OR QUICK SEARCH
        matched_user = None  # WHO YOU ARE PAIRED WITH

        for message in messages:
            user = self.kik_api.get_user(message.from_user)

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

                info = user_modifier.get_info(message.from_user)
                if info:
                    roles = info["roles"]
                    category = info["looking"]
                    search_type = info["search"]
                    matched_user = info["match"]

                # START NEW CONVERSATION
                if message_body.split()[0].lower() in ["hi", "hello"]:
                    roles = []
                    category = None
                    search_type = None
                    matched_user = None

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
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Are you looking for a team or an extra member?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

                # SELECT CATEGORY: TEAM OR MEMBER
                elif not category:
                    if message_body == "Team":
                        category = "team"
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Awesome sauce! What are your roles?",
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
                            result = find_team.filter_role(roles)
                            # IF MATCH FOUND
                            if len(result) > 0:
                                # QUICK SEARCH
                                if search_type == "quick":
                                    result = result[0]
                                    username = result[0]
                                    matched_user = self.kik_api.get_user(username)
                                    matched_user = username
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="You have a match!"
                                    ))
                                    response_messages += self.get_profile(matched_user, message, result[3])
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Would you like to contact " + username + "?",
                                        keyboards=[SuggestedResponseKeyboard(
                                            responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                                # DETAILED SEARCH
                                else:
                                    matched_user = result
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Potential Team Members found!"
                                    ))
                                    output_msg = ""
                                    for user in result:
                                        output_msg += "User: " + user[0] + "\n"
                                        output_msg += "Looking to fill: " + ", ".join(user[3]) + "\n"
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
                                            responses=list(map(lambda x: TextResponse("I want " + x[0]), result)))]))
                            # NO MATCHES FOUND!
                            else:
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Sorry, not matches found!"
                                ))
                    # QUICK MATCH WITH SINGLE USER
                    elif message_body == "Hook me up!":
                        response_messages.append(TextMessage(
                            to=matched_user,
                            body="Hey, I'm " + message.from_user +
                                 "!\nWould you like to join my dank ass team and disrupt industries?"))
                    # DECLINE MATCH
                    elif message_body == "Ew no":
                        roles = []
                        category = None
                        search_type = None
                        matched_user = None
                        response_messages.append(TextMessage(
                            to=matched_user,
                            chat_id=message.chat_id,
                            body="k thx bai"))
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
                            body="Sorry, I didn't quite understand that. Would you like to contact " + username + "?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("Hook me up!"), TextResponse("Ew no")])]))
                # LOOKING FOR A TEAM
                elif category == "team":
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Cool! What roles are you looking to fill?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=list(map(lambda x: TextResponse(x), self.positions)))]))

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
                user_modifier.put_info(message.from_user, roles, category, search_type, matched_user)

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
    def get_profile(user, message, roles=None):
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
        profile_picture_response += "\nLooking to fill: " + ", ".join(roles)

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
    kik = KikApi('maybot', '3a42f662-6593-49e3-bcfe-ddf805a21726')
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook='http://5a9b14b2.ngrok.io/incoming'))
    app = KikBot(kik, __name__)
    app.run(port=8080, host='127.0.0.1', debug=True)
