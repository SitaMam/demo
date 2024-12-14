import traceback
import uvloop
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from SubhoBhai.strings import strings
from config import API_ID, API_HASH
from database.db import database

SESSION_STRING_SIZE = 351

def get(obj, key, default=None):
    try:
        return obj[key]
    except:
        return default

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(_, msg):
    user_data = database.find_one({"chat_id": msg.chat.id})
    if user_data is None or not user_data.get('session'):
        return 
    data = {
        'session': None,
        'logged_in': False
    }
    database.update_one({'_id': user_data['_id']}, {'$set': data})
    await msg.reply("**Logout Successfully** ♦")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    database.insert_one({"chat_id": message.from_user.id})
    user_data = database.find_one({"chat_id": message.from_user.id})
    if get(user_data, 'logged_in', False):
        await message.reply(strings['already_logged_in'])
        return 
    user_id = int(message.from_user.id)
    phone_number_msg = await bot.ask(chat_id=user_id, text="<b>🖐Welcome! Please provide your phone number with the country code to proceed.</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code> \n<b>👉 Note: Type /cancel to stop the process at any time.</b>")
    if phone_number_msg.text=='/cancel':
        return await phone_number_msg.reply("<b>You have successfully canceled the current process. If you'd like to start again, please use the appropriate command to initiate. We're here to assist you! 😊</b>")
    phone_number = phone_number_msg.text
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    await phone_number_msg.reply("📤Sending OTP...")
    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "📩 Please check your official Telegram account for an OTP. Once you receive it, send the OTP here in the following format: \n\n➡️If OTP is `12345`, **please send it as** `1 2 3 4 5`.\n\n**👉 Note: Type /cancel to stop the process at any time**", filters=filters.text, timeout=600)
    except PhoneNumberInvalid:
        await phone_number_msg.reply("**⚠️ The phone number you entered is invalid. Please ensure it is correct and try again.**")
        return
    if phone_code_msg.text=='/cancel':
        return await phone_code_msg.reply("<b>You have successfully canceled the current process. If you want to start again, please initiate the login process.😊</b>")
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await phone_code_msg.reply("**🚫 The OTP you entered is invalid. Please double-check and provide the correct OTP.**")
        return
    except PhoneCodeExpired:
        await phone_code_msg.reply("**⏳ The OTP has expired. Please try again /login .**")
        return
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(user_id, "**🔒 Your account has two-step verification enabled. Please provide the password to proceed.\n👉 Note: Type /cancel to stop the process at any time.**"

, filters=filters.text, timeout=300)
        if two_step_msg.text=='/cancel':
            return await two_step_msg.reply("<b>You have successfully canceled the current process. If you want to start again, please initiate the login process.😊</b>")
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply("**🚫 The password you provided is incorrect. Please double-check and try again.**")
            return
    string_session = await client.export_session_string()
    await client.disconnect()
    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply("<b>⚠️ The generated session string is invalid. Please retry the login process.</b>")
    try:
        user_data = database.find_one({"chat_id": message.from_user.id})
        if user_data is not None:
            data = {
                'session': string_session,
                'logged_in': True
            }

            uclient = Client(":memory:", session_string=data['session'], api_id=API_ID, api_hash=API_HASH)
            await uclient.connect()

            database.update_one({'_id': user_data['_id']}, {'$set': data})
    except Exception as e:
        return await message.reply_text(f"<b>❗ An unexpected error occurred. Please try again or contact support for assistance.</b> `{e}`")
    await bot.send_message(message.from_user.id, "<b>✅ Login Successful! You are now logged in. \n\nIf you encounter any issues, such as authentication errors, use /logout and /login to reconnect.</b>")
