from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from database.db import db  # Assuming you already have a database setup
from config import ADMINS, LOG_CHANNEL  # ADMINS: list of admin IDs; LOG_CHANNEL: ID of the logs channel
import asyncio
import time
import datetime


# Utility Function: Log user interactions
async def log_user_interaction(user_id, message):
    log_message = f"User Interaction:\n\nUser ID: {user_id}\nMessage: {message.text}"
    await message._client.send_message(LOG_CHANNEL, log_message)


# Utility Function: Authorization Check
async def is_authorized(user_id):
    authorized_users = await db.get_authorized_users()  # Fetch authorized users from the database
    return user_id in authorized_users


# Broadcast Function
async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await db.delete_user(int(user_id))  # Remove from database if deactivated, blocked, or invalid
        return False, "Error"
    except Exception:
        return False, "Error"


# Command: Broadcast Messages (Admin Only)
@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_handler(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    if not b_msg:
        return await message.reply_text("**Reply to this command with the message you want to broadcast.**")

    sts = await message.reply_text("Broadcasting your message...")
    start_time = time.time()
    total_users = await db.total_users_count()

    done = success = blocked = deleted = failed = 0

    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            else:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if done % 20 == 0:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users: {total_users}\nCompleted: {done}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(f"Broadcast Completed in {time_taken} seconds.\n\nTotal Users: {total_users}\nCompleted: {done}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")


# Command: Add User to Authorized List (Admin Only)
@Client.on_message(filters.command("add_user") & filters.user(ADMINS))
async def add_user_handler(bot, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /add_user <user_id>")
    user_id = int(message.command[1])
    await db.add_authorized_user(user_id)  # Add user to the database
    await message.reply_text(f"User {user_id} has been added to the authorized list.")


# Command: Remove User from Authorized List (Admin Only)
@Client.on_message(filters.command("remove_user") & filters.user(ADMINS))
async def remove_user_handler(bot, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /remove_user <user_id>")
    user_id = int(message.command[1])
    await db.remove_authorized_user(user_id)  # Remove user from the database
    await message.reply_text(f"User {user_id} has been removed from the authorized list.")


# General Interaction: Respond Only If Authorized
@Client.on_message(filters.text & ~filters.user(ADMINS))
async def general_interaction_handler(bot, message):
    user_id = message.from_user.id
    if not await is_authorized(user_id):
        await message.reply_text("You are not authorized to use this bot.")
        return
    await log_user_interaction(user_id, message)  # Log the interaction
    await message.reply_text("Thank you for your message!")  # Respond to authorized users
