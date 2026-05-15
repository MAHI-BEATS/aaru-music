"""
Active Chats Plugin for AnonXMusic
🤞 𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ BETA BOTS.🙂❤️
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatForbidden
from unidecode import unidecode

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)

POWERED_BY = "🤞 **𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ BETA BOTS.🙂❤️**"

async def generate_invite_link(chat_id: int) -> str:
    """Safely generate chat invite link"""
    try:
        invite_link = await app.export_chat_invite_link(chat_id)
        return invite_link
    except (ChatAdminRequired, UserNotParticipant, ChatForbidden):
        chat_str = str(chat_id)
        if chat_str.startswith("-100"):
            return f"https://t.me/c/{chat_str[4:]}/1"
        return f"https://t.me/c/{chat_str[1:]}/1"
    except Exception:
        return "❌ Invite Link Unavailable"

def ordinal_number(n: int) -> str:
    """Convert integer to ordinal (1st, 2nd, 3rd)"""
    if 10 <= (n % 100) <= 19:
        return f"{n}th"
    elif n % 10 == 1:
        return f"{n}st"
    elif n % 10 == 2:
        return f"{n}nd"
    elif n % 10 == 3:
        return f"{n}rd"
    return f"{n}th"

@app.on_message(filters.command(["activevc", "vc", "activevoice"]) & SUDOERS)
async def active_voice_chats(_, message: Message):
    """🎤 Active voice chats list"""
    mystic = await message.reply_text("🔄 **Fetching active voice chats...**")
    
    try:
        served_chats = await get_active_chats()
    except Exception as e:
        await mystic.edit_text(f"❌ **Error:** `{str(e)}`")
        return
    
    if not served_chats:
        await mystic.edit_text(f"📭 **No active voice chats.**\n\n{POWERED_BY}")
        return
    
    text = ""
    buttons = []
    j = 0
    
    for chat_id in served_chats:
        try:
            chat_info = await app.get_chat(chat_id)
            title = chat_info.title or "Unknown Chat"
            invite_link = await generate_invite_link(chat_id)
            
            clean_title = unidecode(title)[:30]
            if len(title) > 30:
                clean_title += "..."
            
            if chat_info.username:
                text += f"**{j + 1}.** [{clean_title}](https://t.me/{chat_info.username}) `[{chat_id}]`\n"
            else:
                text += f"**{j + 1}.** {clean_title} `[{chat_id}]`\n"
            
            buttons.append([
                InlineKeyboardButton(
                    f"🎵 Join {ordinal_number(j + 1)}", 
                    url=invite_link
                )
            ])
            j += 1
            
        except Exception:
            try:
                await remove_active_chat(chat_id)
            except:
                pass
            continue
    
    if not text:
        await mystic.edit_text(f"📭 **No valid voice chats found.**\n\n{POWERED_BY}")
        return
    
    await mystic.edit_text(
        f"**🎤 Active Voice Chats ({j}):**\n\n{text}\n\n{POWERED_BY}",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@app.on_message(filters.command(["activevideo", "av", "activev"]) & SUDOERS)
async def active_video_chats(_, message: Message):
    """📹 Active video chats list"""
    mystic = await message.reply_text("🔄 **Fetching active video chats...**")
    
    try:
        served_chats = await get_active_video_chats()
    except Exception as e:
        await mystic.edit_text(f"❌ **Error:** `{str(e)}`")
        return
    
    if not served_chats:
        await mystic.edit_text(f"📭 **No active video chats.**\n\n{POWERED_BY}")
        return
    
    text = ""
    buttons = []
    j = 0
    
    for chat_id in served_chats:
        try:
            chat_info = await app.get_chat(chat_id)
            title = chat_info.title or "Unknown Chat"
            invite_link = await generate_invite_link(chat_id)
            
            clean_title = unidecode(title)[:30]
            if len(title) > 30:
                clean_title += "..."
            
            if chat_info.username:
                text += f"**{j + 1}.** [{clean_title}](https://t.me/{chat_info.username}) `[{chat_id}]`\n"
            else:
                text += f"**{j + 1}.** {clean_title} `[{chat_id}]`\n"
            
            buttons.append([
                InlineKeyboardButton(
                    f"🎥 Join {ordinal_number(j + 1)}", 
                    url=invite_link
                )
            ])
            j += 1
            
        except Exception:
            try:
                await remove_active_video_chat(chat_id)
            except:
                pass
            continue
    
    if not text:
        await mystic.edit_text(f"📭 **No valid video chats found.**\n\n{POWERED_BY}")
        return
    
    await mystic.edit_text(
        f"**📹 Active Video Chats ({j}):**\n\n{text}\n\n{POWERED_BY}",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@app.on_message(filters.command(["astats"]) & SUDOERS)
async def astats(_, message: Message):
    """📊 Active stats with inline buttons"""
    try:
        voice_count = len(await get_active_chats())
        video_count = len(await get_active_video_chats())
        total = voice_count + video_count
        
        stats_text = (
            f"📊 **Active Chats Stats**\n\n"
            f"🎤 **Voice Chats:** `{voice_count}`\n"
            f"📹 **Video Chats:** `{video_count}`\n"
            f"📈 **Total:** `{total}`\n\n"
            f"{POWERED_BY}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎤 Voice Chats", callback_data="activevc_cb"),
                InlineKeyboardButton("📹 Video Chats", callback_data="activev_cb")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="astats_cb"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ])
        
        await message.reply_text(
            stats_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`\n\n{POWERED_BY}")

@app.on_callback_query(filters.regex("activevc_cb") & SUDOERS)
async def cb_activevc(client, callback_query: CallbackQuery):
    """Voice chats callback"""
    await callback_query.message.edit_text("🔄 **Loading voice chats...**")
    await active_voice_chats(client, callback_query.message)

@app.on_callback_query(filters.regex("activev_cb") & SUDOERS)
async def cb_activev(client, callback_query: CallbackQuery):
    """Video chats callback"""
    await callback_query.message.edit_text("🔄 **Loading video chats...**")
    await active_video_chats(client, callback_query.message)

@app.on_callback_query(filters.regex("astats_cb") & SUDOERS)
async def cb_astats(client, callback_query: CallbackQuery):
    """Refresh stats callback"""
    await callback_query.message.edit_text("🔄 **Refreshing stats...**")
    await astats(client, callback_query.message)

@app.on_callback_query(filters.regex("close") & SUDOERS)
async def cb_close(_, callback_query: CallbackQuery):
    """Close callback"""
    await callback_query.message.delete()
