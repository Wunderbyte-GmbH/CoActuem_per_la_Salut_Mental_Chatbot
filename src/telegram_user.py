"""
    CoActuem per la Salut Mental Chatobot
    Copyright (C) Franziska Peter, Santi Seguí, Guillem Pascual Guinovart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import pymongo
import copy
import asyncio
import time

import telepot
from telepot import message_identifier, glance

from src.user import User
from src.conversation_elements import random_charged_emoji_html
import src.hash_unhash as hash_unhash


class TelegramUser(telepot.aio.helper.ChatHandler, User):
    """
    basic functions to handle chat,
    overrides telepot functions

    on_chat_message   ::  extract message info from income message
    send_message      ::  get chat id from  telepot helper sender and send message 
    on_callback_query ::  glance on callback data from query, get: query_id, from_id, query_data
    on_close          ::
    """
    
    appbot = None

    def __init__(self, *args, **kwargs):
        telepot.aio.helper.ChatHandler.__init__(self, *args, **kwargs)
        User.__init__(self)

    async def on_chat_message(self, msg):
        """
        extract message info from income message
        """
        content_type, chat_type, chat_id = telepot.glance(msg)
        if 'text' in msg:
            # call user.py method to get the adequate reaction on a message
            await self.handle_on_message(content_type, msg['text'], msg['from'])

    async def send_message(self, msg):
        """
        When you are dealing with a particular chat, it is tedious to have to 
        supply the same chat_id every time to send a message, or to send 
        anything. The telepot helper sender gets that chat_id automatically for 
        you :)
        """
        await self.sender.sendMessage(msg)

    async def on_callback_query(self, msg):
        """
        glance on callback data from query
        """
        query_id, from_id, query_data = glance(msg, flavor='callback_query') # telepot.glance gives you: (msg['id'], msg['from']['id'], msg['data'])
        ##### carry on ..
        await self.handle_on_callback(query_data)

    async def on_close(self, ex):
        """
        calls user.py function handle_on_close()
        saves user info with user_info.py save function: updates mongoDB
        """
        await self.handle_on_close(ex)
