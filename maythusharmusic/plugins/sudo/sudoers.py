from pyrogram import filters
from pyrogram.types import Message

from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import add_sudo, remove_sudo
from maythusharmusic.utils.decorators.language import language
from maythusharmusic.utils.extraction import extract_user
from maythusharmusic.utils.inline import close_markup
from config import BANNED_USERS, OWNER_ID

@app.on_message(filters.command(["addsudo"]) & filters.user(OWNER_ID))
@language
async def useradd(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)
    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention))
    added = await add_sudo(user.id)
    if added:
        SUDOERS.add(user.id)
        await message.reply_text(_["sudo_2"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@app.on_message(filters.command(["delsudo", "rmsudo"]) & filters.user(OWNER_ID))
@language
async def userdel(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)
    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"].format(user.mention))
    removed = await remove_sudo(user.id)
    if removed:
        SUDOERS.remove(user.id)
        await message.reply_text(_["sudo_4"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])


@app.on_message(filters.command(["sudolist", "listsudo", "sudoers"]) & ~BANNED_USERS)
@language
async def sudoers_list(client, message: Message, _):
    # Sudo မဟုတ်တဲ့သူတွေအတွက် Owner ကိုပဲ ID နဲ့တကွ ပြမယ်
    if message.from_user.id not in SUDOERS:
        owner = await app.get_users(OWNER_ID)
        owner_name = owner.first_name if not owner.mention else owner.mention
        return await message.reply_text(
            f"👑 **Owner:**\n{owner_name} (`{OWNER_ID}`)\n\n"
            f"💫 **Sudo Users တွေကြည့်ဖို့ Sudo ဖြစ်ရန်လိုအပ်ပါသည်။**",
            disable_web_page_preview=True
        )
    
    # Sudo users တွေအတွက် List အပြည့်အစုံ ပြမယ်
    text = "**👑 Owner & Sudo Users List:**\n\n"
    
    # Owner ရဲ့ အချက်အလက်
    owner = await app.get_users(OWNER_ID)
    owner_name = owner.first_name if not owner.mention else owner.mention
    text += f"**Owner:**\n{owner_name} (`{OWNER_ID}`)\n\n"
    
    # Sudo Users တွေ စာရင်း
    sudo_users = []
    for user_id in SUDOERS:
        if user_id != OWNER_ID:
            try:
                user = await app.get_users(user_id)
                user_name = user.first_name if not user.mention else user.mention
                sudo_users.append(f"• {user_name} (`{user_id}`)")
            except:
                sudo_users.append(f"• Unknown User (`{user_id}`)")
    
    if sudo_users:
        text += "**Sudo Users:**\n"
        text += "\n".join(sudo_users)
    else:
        text += "**Sudo Users:**\n• No sudo users found."
    
    await message.reply_text(text, reply_markup=close_markup(_))
