from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
import configparser
import sqlite3
import webbrowser
import asyncio
import re

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['pyrogram']['api_id']
api_hash = config['pyrogram']['api_hash']

session_name = 'user_session'

KEYWORDS = ['bot', 'human', 'check', 'verify', 'prove', 'бот', 'людина', 'перевірка', 'верифікація', 'send any message', 'kicked']

captcha_passed = False

class BotHandler:
    def __init__(self, client, chat_id, db_path='messages.db'):
        self.client = client
        self.chat_id = chat_id
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        # Create table to store bot and chat info
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS captcha_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    chat_name TEXT,
                    bot_id INTEGER,
                    bot_username TEXT,
                    captcha_type TEXT
                )
            """)

    def save_bot_info(self, chat_id, chat_name, bot_id, bot_username, captcha_type):
        # Save bot and chat information in the DB
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO captcha_messages (chat_id, chat_name, bot_id, bot_username, captcha_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, chat_name, bot_id, bot_username, captcha_type)
            )
            print(f"Information about bot '{bot_username}' successfully saved with captcha type '{captcha_type}'.")

    async def handle_captcha(self, event):
        global captcha_passed

        if captcha_passed:
            print("Captcha already passed, ignoring the message.")
            return

        print(f"Received message: {event.message.message}")

        captcha_handlers = [
            self.handle_text_captcha,
            self.handle_math_captcha,
            self.handle_button_captcha,
            self.handle_button_link_captcha
        ]

        for handler in captcha_handlers:
            if await handler(event):
                captcha_passed = True
                break

    async def handle_text_captcha(self, event):
        await asyncio.sleep(7)
        if "send any message" in event.message.message.lower():
            print("Bot requires a message for verification.")
            await self.client.send_message(event.chat_id, "Hello, I'm here!")
            print("Message sent.")
            return True
        return False

    async def handle_math_captcha(self, event):
        await asyncio.sleep(7)
        match = re.search(r'\((.*?)\)', event.message.message)
        if match:
            expression = match.group(1)
            try:
                solution = eval(expression)
                await self.client.send_message(event.chat_id, str(solution))
                print(f"Solution sent: {solution}")
                return True
            except Exception as e:
                print(f"Error calculating: {e}")
        return False

    async def handle_button_captcha(self, event):
        await asyncio.sleep(7)
        if not event.buttons:
            return False

        try:
            total_buttons = sum(len(row) for row in event.buttons)
            print(f"Number of buttons: {total_buttons}")

            if total_buttons == 1:
                button = event.buttons[0][0]
                if not button.url:
                    print("Clicking on the first button.")
                    await event.click(0)
                    print("Captcha successfully passed!")
                    return True
            else:
                for row in event.buttons:
                    for button in row:
                        button_text = button.text.lower()
                        print(f"Button text: {button_text}")
                        if not button.url and any(keyword in button_text for keyword in KEYWORDS):
                            print(f"Keyword found in button: {button_text}. Clicking button.")
                            await event.click(row.index(button))
                            print("Captcha successfully passed!")
                            return True
                print("No keywords found in button texts.")
        except Exception as e:
            print(f"Error clicking the button: {e}")
        return False

    async def handle_button_link_captcha(self, event):
        await asyncio.sleep(7)
        if not event.buttons:
            return False

        try:
            for row in event.buttons:
                for button in row:
                    if button.url:
                        print(f"Found ButtonLink: {button.url}. Opening in browser...")
                        webbrowser.open(button.url)
                        await asyncio.sleep(5)
                        bot_username = button.url.split('?start=')[0].replace('https://t.me/', '')
                        bot_entity = await self.client.get_entity(bot_username)
                        await self.client.send_message(bot_entity, '/start')
                        print(f"/start command sent to bot {bot_username}")
                        return True
        except Exception as e:
            print(f"Error handling button link: {e}")
        return False

# Connecting with user session
client = TelegramClient(session_name, api_id, api_hash)

async def main():
    chat_name = input("Enter the chat name (chatname or link): ")
    try:
        chat = await client.get_entity(chat_name)
        chat_id = chat.id
        await client(JoinChannelRequest(chat))
        print(f"Successfully joined chat {chat_name}")

        bot_handler = BotHandler(client, chat_id)

        @client.on(events.NewMessage(chats=chat_id))
        async def my_event_handler(event):
            sender = await event.get_sender()

            if sender.username and sender.username.endswith("bot"):
                bot_id = sender.id
                bot_username = sender.username

                # Check for captcha types
                captcha_type = "unknown"
                if event.buttons:
                    # Check if button has URL
                    if any(button.url for row in event.buttons for button in row):
                        captcha_type = "buttonlink"
                    else:
                        captcha_type = "button"
                elif re.search(r'\((.*?)\)', event.message.message):
                    captcha_type = "math"
                elif "send any message" in event.message.message.lower():
                    captcha_type = "text"

                bot_handler.save_bot_info(chat_id, chat_name, bot_id, bot_username, captcha_type)
                await bot_handler.handle_captcha(event)
            else:
                print(f"Message from user {sender.username} who is not a bot.")

        print(f"Waiting for new messages in chat {chat_name}...")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Failed to join chat {chat_name}: {e}")

with client:
    client.loop.run_until_complete(main())
