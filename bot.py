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


class KikBot(Flask):
    """ Flask kik bot application class"""

    roles = ["Front End", "Back End", "Android", "iOS", "Web Dev", "Hardware"]
    curr_roles = []
    looking_for = None

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
        search = None

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

                if message_body.split()[0].lower() in ["hi", "hello"]:
                    self.curr_roles = []
                    self.looking_for = None
                    self.search = None

                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Hi {}!".format(user.first_name),
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="I'm May, aka June2.0.",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Quick Search or Detailed Search?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("<3 Quickies"), TextResponse("Mmmm details")])]))

                # if haven't defined search type
                elif not self.search:
                    if "quick" in message_body.lower():
                        self.search = "quick"
                    elif "detail" in message_body.lower():
                        self.search = "detailed"
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
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="What are you looking for?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

                #user looking for a team
                elif message_body == "Team":
                    self.looking_for = "member"
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Awesome sauce! What are your roles?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=list(map(lambda x: TextResponse(x), self.roles)))]))

                #user looking for a member
                elif message_body == "Member":
                    self.looking_for = "team"
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Cool! What roles are you looking to fill?",
                        keyboards=[SuggestedResponseKeyboard(
                            responses=list(map(lambda x: TextResponse(x), self.roles)))]))

                elif self.looking_for:
                    if message_body in self.roles:
                        if message_body not in self.curr_roles: self.curr_roles.append(message_body)
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="You are currently looking for roles in: " + ", ".join(self.curr_roles)
                        ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Are you looking for anymore roles to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                        ))

                    #looking for more roles
                    elif message_body == "Moar roles pls":
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Cool! What roles are you looking to fill?",
                            keyboards=[SuggestedResponseKeyboard(
                                responses=list(map(lambda x: TextResponse(x), self.roles)))]))

                    #no more roles
                    elif message_body == "I'm good":
                        print (self.looking_for)
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Cool! Searching for team member..." if (self.looking_for == "team")
                            else "Cool! Searching for a team..."
                        ))

                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Sorry, I didn't quite understand that."))
                        if len(self.curr_roles) > 0:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="You are currently looking for roles in: " + ", ".join(self.curr_roles)
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Are you looking for anymore roles to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=[TextResponse("Moar roles pls"), TextResponse("I'm good")])]
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="What roles are you looking to fill?",
                                keyboards=[SuggestedResponseKeyboard(
                                    responses=list(map(lambda x: TextResponse(x), self.roles)))]))

                elif message_body.lower() == "profile":
                    # Send the user a response along with their profile picture (function definition is below)
                    response_messages += self.profile_pic_check_messages(user, message)

                elif message_body in ["no thanks", "no thank you"]:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Ok, {}. Chat with me again if you change your mind.".format(user.first_name)))
                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Sorry, I didn't quite understand that. What are you looking for?",
                        # keyboards are a great way to provide a menu of options for a user to respond with!
                        keyboards=[
                            SuggestedResponseKeyboard(responses=[TextResponse("Team"), TextResponse("Member")])]))

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
    def profile_pic_check_messages(user, message):
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

            profile_picture_response = "Here's your profile picture!"
        else:
            profile_picture_response = "It does not look like you have a profile picture, you should set one"

        messages_to_send.append(
            TextMessage(to=message.from_user, chat_id=message.chat_id, body=profile_picture_response))

        return messages_to_send


if __name__ == "__main__":
    """ Main program """
    kik = KikApi('maybot', '3a42f662-6593-49e3-bcfe-ddf805a21726')
    # For simplicity, we're going to set_configuration on startup. However, this really only needs to happen once
    # or if the configuration changes. In a production setting, you would only issue this call if you need to change
    # the configuration, and not every time the bot starts.
    kik.set_configuration(Configuration(webhook='http://85cc67b6.ngrok.io/incoming'))
    app = KikBot(kik, __name__)
    app.run(port=8080, host='127.0.0.1', debug=True)
