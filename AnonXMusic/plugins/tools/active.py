from pyrogram import filters
from pyrogram.types import Message
from unidecode import unidecode

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)


@app.on_message(filters.command(["activevc", "vc", "activevoice"]) & SUDOERS)
async def activevc(_, message: Message):
    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ʟɪsᴛ...")
    served_chats = await get_active_chats()
    text = ""
    j = 0
    buttons = []
    for x in served_chats:
        try:
            chat_info = await app.get_chat(x)
            title = chat_info.title
            invite_link = await generate_join_link(x)
        except:
            await remove_active_chat(x)
            continue
        try:
            if chat_info.username:
                user = chat_info.username
                text += f"<b>{j + 1}.</b> <a href=https://t.me/{user}>{unidecode(title).upper()}</a> [<code>{x}</code>]\n"
            else:
                text += (
                    f"<b>{j + 1}.</b> {unidecode(title).upper()} [<code>{x}</code>]\n"
                )
            button_text = f"๏ ᴊᴏɪɴ {ordinal(j + 1)} ɢʀᴏᴜᴘ ๏"
            buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
            j += 1
        except:
            continue
    if not text:
        await mystic.edit_text(f"» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ᴏɴ {app.mention}.")
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs :</b>\n\n{text}",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )


@app.on_message(filters.command(["activev", "av", "activevideo"]) & SUDOERS)
async def activevi_(_, message: Message):
    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ʟɪsᴛ...")
    served_chats = await get_active_video_chats()
    text = ""
    j = 0
    buttons = []
    for x in served_chats:
        try:
            chat_info = await app.get_chat(x)
            title = chat_info.title
            invite_link = await generate_join_link(x)
        except:
            await remove_active_video_chat(x)
            continue
        try:
            if chat_info.username:
                user = chat_info.username
                text += f"<b>{j + 1}.</b> <a href=https://t.me/{user}>{unidecode(title).upper()}</a> [<code>{x}</code>]\n"
            else:
                text += (
                    f"<b>{j + 1}.</b> {unidecode(title).upper()} [<code>{x}</code>]\n"
                )
            button_text = f"๏ ᴊᴏɪɴ {ordinal(j + 1)} ɢʀᴏᴜᴘ ๏"
            buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
            j += 1
        except:
            continue
    if not text:
        await mystic.edit_text(f"» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ᴏɴ {app.mention}.")
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs :</b>\n\n{text}",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )


@app.on_message(filters.command(["ac"]) & SUDOERS)
async def start(client: Client, message: Message):
    ac_audio = str(len(await get_active_chats()))
    ac_video = str(len(await get_active_video_chats()))
    await message.reply_text(
        f"✫ <b><u>ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛs ɪɴғᴏ</u></b> :\n\nᴠᴏɪᴄᴇ : {ac_audio}\nᴠɪᴅᴇᴏ  : {ac_video}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✯ ᴄʟᴏsᴇ ✯", callback_data=f"close")]]
        ),
    )
