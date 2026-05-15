import time
import re
import random
import asyncio
import logging

from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.errors.exceptions.flood_420 import SlowmodeWait
from ytSearch import VideosSearch

import config
from AnonXMusic import app
from AnonXMusic.misc import _boot_
from AnonXMusic.plugins.sudo.sudoers import sudoers_list
from AnonXMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    blacklist_chat,
)
from AnonXMusic.utils.decorators.language import LanguageStart
from AnonXMusic.utils.formatters import get_readable_time
from AnonXMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, LOGGER_ID
from strings import get_string
from AnonXMusic import LOGGER  # Added missing import

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    try:
        await add_served_user(message.from_user.id)
        
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        accha = await message.reply_text("**Sᴛᴀʀᴛɪɴɢ....🥀**")
        await asyncio.sleep(1.2)
        
        await accha.delete()
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        accha = await message.reply_text("**I..Aᴍ..Aʟɪᴠe..Bᴀʙʏ...🍫**")
        await asyncio.sleep(1.8)
        
        await accha.delete()
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        accha = await message.reply_text("**Bᴇᴛᴀ..Bᴏᴛs.....❤️❤️**")
        await asyncio.sleep(1.5)
        await accha.delete()
        
        if len(message.text.split()) > 1:
            name = message.text.split(None, 1)[1]
            if name.startswith("help"):
                keyboard = help_pannel(_)
                await app.send_chat_action(message.chat.id, ChatAction.TYPING)
                await message.reply_sticker("CAACAgUAAxkBAAFJgZ1qBGwx9Z9vW5BhG3dw0l1A5j4CyQACXRYAAuc-wVWs4--9DGlDKzsE")
                return await message.reply_photo(
                    photo=random.choice(config.START_IMG_URL),
                    caption=_["help_1"].format(config.SUPPORT_CHAT),
                    reply_markup=keyboard,
                )
            if name.startswith("sud"):
                await app.send_chat_action(message.chat.id, ChatAction.TYPING)
                await sudoers_list(client=client, message=message, _=_)
                if await is_on_off(2):
                    try:
                        await app.send_message(
                            chat_id=config.LOGGER_ID,
                            text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                        )
                    except:
                        pass
                return
            if name.startswith("info_"):
                await app.send_chat_action(message.chat.id, ChatAction.TYPING)
                m = await message.reply_text("🔎")
                try:
                    query = name.replace("info_", "", 1)
                    query = f"https://www.youtube.com/watch?v={query}"
                    results = VideosSearch(query, limit=1)
                    for result in (await results.next())["result"]:
                        title = result["title"]
                        duration = result["duration"]
                        views = result["viewCount"]["short"]
                        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                        channellink = result["channel"]["link"]
                        channel = result["channel"]["name"]
                        link = result["link"]
                        published = result["publishedTime"]
                    
                    searched_text = _["start_6"].format(
                        title, duration, views, published, channellink, channel, app.mention
                    )
                    key = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text=_["S_B_8"], url=link),
                                InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                            ],
                        ]
                    )
                    await m.delete()
                    await app.send_photo(
                        chat_id=message.chat.id,
                        photo=thumbnail,
                        caption=searched_text,
                        reply_markup=key,
                    )
                    if await is_on_off(2):
                        try:
                            await app.send_message(
                                chat_id=config.LOGGER_ID,
                                text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                            )
                        except:
                            pass
                except Exception as e:
                    await m.edit("❌ **Error fetching video info!**")
                    LOGGER(__name__).error(f"Info command error: {e}")
                return
        else:
            # Default response
            await app.send_chat_action(message.chat.id, ChatAction.TYPING)
            out = private_panel(_)
            await message.reply_sticker("CAACAgUAAxkBAAFJgZ1qBGwx9Z9vW5BhG3dw0l1A5j4CyQACXRYAAuc-wVWs4--9DGlDKzsE")
            await message.reply_photo(
                photo=random.choice(config.START_IMG_URL),
                caption=_["start_2"].format(message.from_user.mention, app.mention),
                reply_markup=InlineKeyboardMarkup(out),
            )
            if await is_on_off(2):
                try:
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                    )
                except:
                    pass
                    
    except Exception as e:
        LOGGER(__name__).error(f"Start PM error: {e}")


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    try:
        out = start_panel(_)
        uptime = int(time.time() - _boot_)
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        await message.reply_photo(
            photo=random.choice(config.START_IMG_URL),
            caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=InlineKeyboardMarkup(out),
        )
        await add_served_chat(message.chat.id)
    except ChannelPrivate:
        pass
    except SlowmodeWait as e:
        await asyncio.sleep(e.value)
        try:
            await app.send_chat_action(message.chat.id, ChatAction.TYPING)
            uptime = int(time.time() - _boot_)  # Recalculate uptime
            await message.reply_photo(
                photo=random.choice(config.START_IMG_URL),
                caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=InlineKeyboardMarkup(out),
            )
            await add_served_chat(message.chat.id)
        except:
            pass
    except Exception as e:
        LOGGER(__name__).error(f"Start GP error: {e}")


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    try:
        for member in message.new_chat_members:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)
                
                # Myanmar character check
                try:
                    ch = await app.get_chat(message.chat.id)
                    if ch and ch.title and re.search(r'[\u1000-\u109F]', ch.title):
                        await blacklist_chat(message.chat.id)
                        await message.reply_text("This group is not allowed to play songs")
                        try:
                            await app.send_message(
                                LOGGER_ID, 
                                f"**BLACKLISTED AUTO**\n\nGroup: {ch.title}\nID: `{message.chat.id}`\nReason: Myanmar characters in title"
                            )
                        except:
                            pass
                        return await app.leave_chat(message.chat.id)
                    
                    if ch and ch.description and re.search(r'[\u1000-\u109F]', ch.description):
                        await blacklist_chat(message.chat.id)
                        await message.reply_text("This group is not allowed to play songs")
                        try:
                            await app.send_message(
                                LOGGER_ID, 
                                f"**BLACKLISTED AUTO**\n\nGroup: {ch.title}\nID: `{message.chat.id}`\nReason: Myanmar characters in description"
                            )
                        except:
                            pass
                        return await app.leave_chat(message.chat.id)
                except Exception as chat_error:
                    LOGGER(__name__).warning(f"Error getting chat info: {chat_error}")

                out = start_panel(_)
                await app.send_chat_action(message.chat.id, ChatAction.TYPING)
                await message.reply_photo(
                    photo=random.choice(config.START_IMG_URL),
                    caption=_["start_3"].format(
                        message.from_user.first_name if message.from_user else "Unknown",
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)  # Fixed indentation
                
                if await is_on_off(2):
                    try:
                        added_by = "Unknown User"
                        added_by_id = "Unknown"
                        added_by_username = "None"
                        if message.from_user:
                            added_by = message.from_user.mention
                            added_by_id = message.from_user.id
                            added_by_username = (
                                f"@{message.from_user.username}"
                                if message.from_user.username
                                else "None"
                            )
                        elif message.sender_chat:
                            added_by = message.sender_chat.title
                            added_by_id = message.sender_chat.id
                            added_by_username = (
                                f"@{message.sender_chat.username}"
                                if message.sender_chat.username
                                else "None"
                            )
                        chat_username = (
                            f"@{message.chat.username}"
                            if message.chat.username
                            else "None"
                        )
                        await app.send_message(
                            chat_id=config.LOGGER_ID,
                            text=(
                                f"{app.mention} was added to a new group.\n\n"
                                f"<b>Group Name :</b> {message.chat.title}\n"
                                f"<b>Group ID :</b> <code>{message.chat.id}</code>\n"
                                f"<b>Group Username :</b> {chat_username}\n"
                                f"<b>Added By :</b> {added_by}\n"
                                f"<b>Adder ID :</b> <code>{added_by_id}</code>\n"
                                f"<b>Adder Username :</b> {added_by_username}"
                            ),
                        )
                    except Exception as logger_error:
                        LOGGER(__name__).error(f"Logger error: {logger_error}")
                
                await message.stop_propagation()
                
    except Exception as ex:
        LOGGER(__name__).error(f"Welcome handler error: {ex}")
