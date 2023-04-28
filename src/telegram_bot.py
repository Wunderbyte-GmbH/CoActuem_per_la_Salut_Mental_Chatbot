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

# external libraries
import telepot
import asyncio
import numpy as np
from time import sleep
from random import random
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import pave_event_space, per_chat_id, \
    create_open, include_callback_query_chat_id
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# internal libraries
from src.bot import Bot
from src.user import User
from src.telegram_user import TelegramUser
from src.event import Event
from src.status import Status
from src.settings import options
import src.hash_unhash as hash_unhash

class TelegramBot(Bot):
    def __init__(self, TOKEN):
        """ Create telegram bot """
        # this way of creating a DelegatorBot is outdated according to https://tinyurl.com/y4634okj (stackexchange)
        self.bot = telepot.aio.DelegatorBot(TOKEN, [
            include_callback_query_chat_id(
                pave_event_space())(
                per_chat_id(), 
                create_open, 
                TelegramUser, 
                timeout=600), # controlling how long to poll, in seconds (because this bot uses long polling)
            ])
        # Super: keep parents' inheritance function __init__()
        Bot.__init__(self) 
        # Start async event loop
        self._loop = asyncio.get_event_loop()
        # a incoming messages
        self._loop.create_task(MessageLoop(self.bot).run_forever())
    
    async def send_typing(self, chat_id): 
        """
        typing dots. 
        if user is Blocked, set his/her status: DOWN
        """
        try:
            userinfo = self.get_user_info(chat_id)
            tele_id = userinfo.get_un_hashed_user_id()#hash_unhash.un_hash_id(chat_id)
            await self.bot.sendChatAction(tele_id, 'typing')
        except telepot.exception.BotWasBlockedError as e: 
            # Bot is blocked or alike!
            user = self.get_user_info(chat_id)
            print("[E] While typing to {}: {}".format(user.data['_id'], e))
            self.remove_user(user)
            print("user ", str("user was removed")) # remove user from pending, waiting, busy list
            user.data['status'] = Status.DOWN
        except Exception as ex:
            user = self.get_user_info(chat_id)
            print("[E] While sending to {}: {}".format(user.data['_id'], ex))
            
    async def set_up_buttons(self, buttons):
        """
        Depending on how long the text on the buttons is, 
        set them horizontally side by side 
        or vertically one below the other
        # several lines on one button can be achieved by "\n" within the button text
        """
        total_length = 0 # counter for text on all buttons
        for text, value in buttons: # count how the button texts are in total
            total_length+=len(text)
        if total_length > 15: # if long, set vertical
            buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=value)]\
                for text, value in buttons])
        else: # if short, set horizontal (e.g. buttons A, B, C)
            buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=value) for text, value in buttons]])
        return buttons

    async def calc_delay_sending(self, message, img= None, pdf=None, poll=None):
        """
        calculates for how many seconds the user should receive typing event
        """
        if options.dev:
                l = 0
        else:
            try:
                l = len(message)//450+1
            except:
                l = 0
            if img or pdf or poll:
                l += 1
        return l

    async def send_message(self, chat_id, message, img= None, buttons=None, pdf=None, poll=None):
        """
        set up buttons and send them together with img, pdf with their respective Chat actions (..., >>>) 
        """        
        if buttons:
            # get reply_markup
           buttons = await self.set_up_buttons(buttons)
        if poll: 
            # feature not working yet!
            # question: Poll question, 1-300 characters
            # options: Array of String, A JSON-serialized list of answer options, 2-10 strings 1-100 characters each
            question = message
            options = await self.set_up_buttons(poll)
        userinfo = self.get_user_info(chat_id)
        tele_id = userinfo.get_un_hashed_user_id()#hash_unhash.un_hash_id(chat_id)
        try:
            # delay sending message according to length of message
            l = await self.calc_delay_sending(message, img, pdf, poll)            
            if img:
                photo = open("./data/outgoing_files/img/"+img, 'rb')
                while l>0:
                    await self.bot.sendChatAction(tele_id, 'upload_photo')
                    sleep(1)
                    l-=1
                return await self.bot.sendPhoto(tele_id, photo, caption=message, reply_markup=buttons, parse_mode= 'HTML')
            elif pdf:                
                pdf_file = open("./data/outgoing_files/"+pdf, 'rb')
                while l>0:
                    await self.bot.sendChatAction(tele_id, 'upload_document')
                    sleep(1)
                    l-=1
                return await self.bot.sendDocument(tele_id, pdf_file, caption=message, parse_mode= 'HTML')
            elif poll:
                # feature not working yet!
                while l>0:
                    await self.bot.sendChatAction(tele_id, 'typing')
                    sleep(1)
                    l-=1
                return await self.bot.sendPoll(tele_id, question, options, is_anonymous=True, allows_multiple_answers=True, parse_mode= 'HTML')                
            else:
                while l>0:
                    await self.bot.sendChatAction(tele_id, 'typing')
                    sleep(min(1, l)) # the 5 secs that a normal chat action takes
                    l-=1
                try:
                    return await self.bot.sendMessage(tele_id, message, reply_markup=buttons, parse_mode= 'HTML')#'Markdown')
                except:
                    print("[E] Message could not be sent: ", message)
        except telepot.exception.BotWasBlockedError as e:
            # Bot is blocked or alike!
            user = self.get_user_info(chat_id)
            print("[E] While sending to {}: {}".format(user.data['_id'], e))
            self.remove_user(user) # remove user from pending, waiting, busy list
            user.data['status'] = Status.DOWN
            return None
        except Exception as ex:
            try:
                print("[E] While sending to {}: {}".format(user.data['_id'], ex))
            except:
                if hasattr(ex, 'message') and hasattr(ex, args):
                    print(ex.message, ex.args)
                else:
                    print(ex)

    def send_message_after(self, chat_id, seconds, message, wait=1, on_done=None):
        if options.dev:
            seconds = 0
        self.typing_event(chat_id, seconds, lambda: self.send_message(chat_id, message))

    def typing_event(self, chat_id, seconds, on_done, wait=1):
        """
        send typing event during a given time 
        """
        #if options.dev:
        #    seconds = 1
        #for secs in np.arange(wait, seconds, 1): # count from wait to seconds in steps of 1
        #    User.appbot.add_event(Event.after(min((wait + secs)*25, 5), lambda: self.send_typing(chat_id)))
        self.add_event(Event.after(seconds, on_done))

    async def get_me(self):
        """
        telepot.getMe() : bot info in form of User object
        """
        info = await self.bot.getMe()
        print('Bot info', info)

    def wait(self): # overrides asyncio wait?????
        self._loop.run_forever()
