# -*- coding: utf-8 -*-
import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup
from pyrogram.enums import ParseMode

import config
from maythusharmusic import YouTube, app
from maythusharmusic.core.call import Hotty
from maythusharmusic.misc import db
from maythusharmusic.utils.database import add_active_video_chat, is_active_chat
from maythusharmusic.utils.exceptions import AssistantErr
from maythusharmusic.utils.inline import aq_markup, close_markup, stream_markup
from maythusharmusic.utils.pastebin import HottyBin
from maythusharmusic.utils.stream.queue import put_queue, put_queue_index
from maythusharmusic.utils.thumbnails import get_thumb


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if forceplay:
        await Hotty.force_stop_stream(chat_id)

    # 🟢 [PREMIUM EMOJI - SAFE HTML ဖြင့် ပြင်ဆင်ချက်] 🟢
    def get_stream_text(t, d, u):
        # ValueError မတက်စေရန် အထူးသင်္ကေတများကို ပြင်ဆင်ခြင်း
        t = str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        u = str(u).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        return (
            f"<emoji id='6131758159473156126'>🎧</emoji> <b>စတင်ထုတ်လွှင့်နေပြီ </b>\n"
            f"<emoji id='6300622254778616022'>🎵</emoji> <b>ခေါင်းစဉ် :</b> {t[:27]}\n"
            f"<emoji id='6300757202651055745'>⏱</emoji> <b>ကြာချိန် :</b> {d} ᴍɪɴᴜᴛᴇs\n"
            f"<emoji id='6298751564592973547'>👤</emoji> <b>တောင်းဆိုသူ :</b> {u}"
        )
        
    def get_queue_text(t, d, u, p):
        t = str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        u = str(u).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        return (
            f"<emoji id='6131758159473156126'>📝</emoji> <b>Aᴅᴅᴇᴅ ᴛᴏ ʟɪsᴛ</b>\n"
            f"<emoji id='6300757202651055745'>🎵</emoji> <b>Tɪᴛʟᴇ :</b> {t[:27]}\n"
            f"<emoji id='6300622254778616022'>⏱</emoji> <b>Dᴜʀᴀᴛɪᴏɴ :</b> {d} ᴍɪɴᴜᴛᴇs\n"
            f"<emoji id='6298751564592973547'>👤</emoji> <b>Rᴇǫᴜᴇsᴛᴇʀ :</b> {u}\n"
            f"<emoji id='6300853298249336390'>🔢</emoji> <b>Sᴇʀɪᴀʟ :</b> {p}"
        )
    # -----------------------------------------------------------

    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None

                try:
                    await mystic.edit_text(
                        _["play_dl"].format(title), 
                        disable_web_page_preview=True
                    )
                except KeyError:
                    await mystic.edit_text(
                        f"နှလုံးသားမပါလျှင် ဘယ်အရာမှတရားမဝင် ● ᥫ᭡ {title}", 
                        disable_web_page_preview=True
                    )

                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    raise AssistantErr(_["play_14"])
                await Hotty.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                    image=thumbnail,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await get_thumb(vidid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=get_stream_text(title, duration_min, user_name),
                    reply_markup=InlineKeyboardMarkup(button),
                    parse_mode=ParseMode.HTML,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        else:
            link = await HottyBin(msg)
            upl = close_markup(_)
            return await app.send_message(
                original_chat_id,
                text=_["play_21"].format(position, link),
                reply_markup=upl,
                disable_web_page_preview=True
            )
            
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None

        current_queue = db.get(chat_id)

        if current_queue is not None and len(current_queue) >= 50:
            return await app.send_message(original_chat_id, "You can't add more than 50 songs to the queue.")

        try:
            await mystic.edit_text(
                _["play_dl"].format(title), 
                disable_web_page_preview=True
            )
        except KeyError:
            await mystic.edit_text(
                f"နှလုံးသားမပါလျှင် ဘယ်အရာမှတရားမဝင် ● ᥫ᭡ {title}", 
                disable_web_page_preview=True
            )

        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,  
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=get_queue_text(title, duration_min, user_name, position),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path, 
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=get_stream_text(title, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=get_queue_text(title, duration_min, user_name, position),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=get_stream_text(title, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=get_queue_text(title, duration_min, user_name, position),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(chat_id, original_chat_id, file_path, video=status)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=get_stream_text(title, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=get_queue_text(title, duration_min, user_name, position),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail if thumbnail else None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=get_stream_text(title, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=get_queue_text(title, duration_min, user_name, position),
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            
            index_text = (
                f"<emoji id='6131758159473156126'>🎧</emoji> <b>Sᴛʀᴇᴀᴍɪɴɢ sᴛᴀʀᴛᴇᴅ (Index Stream)</b>\n\n"
                f"<emoji id='6300622254778616022'>👤</emoji> <b>Rᴇǫᴜᴇsᴛᴇʀ :</b> {user_name}"
            )
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=index_text,
                reply_markup=InlineKeyboardMarkup(button),
                parse_mode=ParseMode.HTML,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
