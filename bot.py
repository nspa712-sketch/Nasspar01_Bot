import os
from datetime import datetime
from groq import Groq
import telebot
from telebot import types

# API Keys များကို Environment Variables မှ ယူခြင်း
TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq Client ကို Configure လုပ်ခြင်း
groq_client = Groq(api_key=GROQ_API_KEY)

# Bot Settings
CHANNEL_USERNAME = "@seriesmoviesplanet007"
CREATOR_ID = 5188275898

KAY_PHONE = "09448948562"
WAVE_PHONE = "09448948562"
ACCOUNT_NAME = "Nyein Sopyay Aung"
PREMIUM_CHANNEL_LINK = "https://t.me/+sFoFxmAXOVI5ZTg1"

bot = telebot.TeleBot(TOKEN)
USER_DATA_FILE = "unique_users.txt"
MEMBERS_DATA_FILE = "members_list.txt"

# Bot ရဲ့ Character နှင့် အချက်အလက်များကို System Prompt အဖြစ် သတ်မှတ်ခြင်း
SYSTEM_PROMPT = f"""
သင်သည် Nasspar's Bot ၏ AI Assistant ဖြစ်သည်။ Telegram channel {CHANNEL_USERNAME} တွင် 'Ashita No Joe' (Tomorrow's Joe) ဇာတ်ကားကို မြန်မာစာတန်းထိုးဖြင့် ဖြန့်ချိပေးနေသည်။
အဓိက အချက်အလက်များ:
- ဇာတ်ကားအကြောင်း: Ashita No Joe (Season 1 - 79 eps, Season 2 - 47 eps, Total 126 eps, IMDb 8.2/10, ထွက်ရှိခုနှစ် 1970-1981) ဂန္တဝင်လက်ဝှေ့ အန်နီမေးရှင်း။
- Member ကြေး: ၅,၀၀၀ ကျပ် (Joe Series တစ်ခုတည်းအတွက် သီးသန့်)။
- ငွေပေးချေရန်: KBZ Pay ({KAY_PHONE}) သို့မဟုတ် Wave Pay ({WAVE_PHONE}), Account Name: {ACCOUNT_NAME}။ 
- Admin များ: @Nazzpar နှင့် @hikarikenn။

စည်းမျဉ်းများ:
- အသုံးပြုသူများကို ဖော်ရွေစွာ၊ ယဉ်ကျေးစွာဖြင့် မြန်မာဘာသာဖြင့် သဘာဝကျကျ ဖြေကြားပါ။
- ဈေးနှုန်း၊ ငွေပေးချေမှု၊ ဇာတ်ကားအကြောင်း သို့မဟုတ် သမိုင်းကြောင်းမေးလျှင် အထပါ အချက်အလက်များကို အခြေခံ၍ ဉာဏ်ကောင်းစွာ ဖြေပေးပါ။
- အခြားအသေးစိတ် အခက်အခဲများရှိပါက Admin များ (@Nazzpar, @hikarikenn) ထံ တိုက်ရိုက်ဆက်သွယ်ရန် ညွှန်ကြားပါ။
"""


def track_and_count_user(user_id):
  users = set()
  if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
      for line in f:
        uid = line.strip()
        if uid:
          users.add(uid)

  str_user_id = str(user_id)
  is_new = str_user_id not in users
  if is_new:
    users.add(str_user_id)
    with open(USER_DATA_FILE, "w") as f:
      for uid in users:
        f.write(f"{uid}\n")

  return len(users), is_new


def save_member_record(user_id, name, username):
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  record = f"{user_id}|{name}|@{username if username else 'None'}|{current_time}\n"
  with open(MEMBERS_DATA_FILE, "a", encoding="utf-8") as f:
    f.write(record)


def log_user_activity(message, action="စတင်အသုံးပြုခြင်း (/start)"):
  try:
    user = message.from_user
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "Username မရှိပါ"
    user_id = user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_users, is_new = track_and_count_user(user_id)
    new_status = "✨ (User အသစ်)" if is_new else "🔄 (ပြန်လည်ဝင်ရောက်လာသူ)"

    log_text = f"""
⚠️ **[Bot Activity Log]** ⚠️ {new_status}
👤 **အမည်:** {name}
🔗 **Username:** {username}
🆔 **User ID:** `{user_id}`
⚡ **လုပ်ဆောင်ချက်:** {action}
👥 **စုစုပေါင်း အသုံးပြုသူ:** {total_users} ယောက်
🕒 **အချိန်:** {current_time}
"""
    bot.send_message(CREATOR_ID, log_text, parse_mode="Markdown")
  except Exception as e:
    print(f"Log Error: {e}")


@bot.message_handler(commands=["stats"])
def show_stats(message):
  if message.from_user.id != CREATOR_ID:
    return

  total_users = 0
  if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
      total_users = sum(1 for line in f if line.strip())

  bot.reply_to(
      message,
      f"📊 **Bot Statistics Dashboard:**\n\n👥 စုစုပေါင်း အသုံးပြုသူ (Total Users):"
      f" `{total_users}` ယောက် 🚀",
      parse_mode="Markdown",
  )


@bot.message_handler(commands=["members"])
def show_members_list(message):
  if message.from_user.id != CREATOR_ID:
    return

  if not os.path.exists(MEMBERS_DATA_FILE):
    bot.reply_to(message, "📭 လက်ရှိတွင် Member ဝင်ထားသူ စာရင်း မရှိသေးပါ။")
    return

  members_text = "👑 **Ashita No Joe - Verified Members List** 👑\n━━━━━━━━━━━━━━━━━━━━━━\n"
  count = 0
  with open(MEMBERS_DATA_FILE, "r", encoding="utf-8") as f:
    for line in f:
      parts = line.strip().split("|")
      if len(parts) == 4:
        uid, name, uname, t = parts
        count += 1
        members_text += f"{count}. {name} ({uname}) [ID: `{uid}`]\n   ⏱ {t}\n\n"

  members_text += f"📊 **စုစုပေါင်း Member ဝင်အရေအတွက်:** `{count}` ယောက်"
  bot.reply_to(message, members_text, parse_mode="Markdown")


@bot.message_handler(commands=["check"])
def check_specific_user(message):
  if message.from_user.id != CREATOR_ID:
    return

  try:
    args = message.text.split()
    if len(args) < 2:
      bot.reply_to(
          message,
          "⚠️ **အသုံးပြုပုံ:** `/check <user_id>`\nဥပမာ - `/check 5188275898`",
          parse_mode="Markdown",
      )
      return

    target_user_id = int(args[1])
    is_sub = check_user_subscription(target_user_id)

    if is_sub:
      bot.reply_to(
          message,
          f"✅ **User ID:** `{target_user_id}` သည် Channel ကို Join"
          " ထားပြီးသားဖြစ်ပါသည်!",
          parse_mode="Markdown",
      )
    else:
      bot.reply_to(
          message,
          f"❌ **User ID:** `{target_user_id}` သည် Channel ကို Join"
          " မထားသေးပါ (သို့မဟုတ်) Left ထွက်သွားပါပြီ!",
          parse_mode="Markdown",
      )
  except ValueError:
    bot.reply_to(
        message,
        "⚠️ ကျေးဇူးပြု၍ မှန်ကန်သော User ID (ဂဏန်းများသာ) ရိုက်ထည့်ပါ!",
    )
  except Exception as e:
    bot.reply_to(message, f"❌ Error: {e}")


def check_user_subscription(user_id):
  try:
    member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    if member.status in ["creator", "administrator", "member"]:
      return True
  except Exception as e:
    print(f"Error checking sub: {e}")
  return False


def show_main_menu(chat_id):
  welcome_text = (
      "✨ **မင်္ဂလာပါ မိတ်ဆွေ...** 👋\n"
      "━━━━━━━━━━━━━━━━━━━━━━\n"
      "🤖 ကျွန်တော်ကတော့ **Nasspar's Bot** ရဲ့ AI Assistant ပဲ ဖြစ်ပါတယ်ခင်ဗျာ။\n\n"
      "🎬 အောက်ပါ Menu ခလုတ်များကို အသုံးပြု၍ လိုအပ်သည်များကို လေ့လာနိုင်သလို၊\n"
      "💬 **Ashita No Joe** အကြောင်းနှင့် ပတ်သက်ပြီး Groq AI နဲ့ လွတ်လပ်စွာ"
      " စကားပြောမေးမြန်းနိုင်ပါတယ် 🧠✨"
  )

  markup = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "🥊 Ashita No Joe Series အကြောင်း လေ့လာရန်", callback_data="about_joe"
  )
  btn2 = types.InlineKeyboardButton(
      "💳 Joe Series အတွက် Member ကြေး ငွေပေးချေရန်",
      callback_data="payment_info",
  )
  btn3 = types.InlineKeyboardButton(
      "🎬 Ashita No Joe အစမ်းကြည့်ရန် (Channel)",
      url="https://t.me/ashitanojoefreeep",
  )
  btn_admin1 = types.InlineKeyboardButton(
      "💬 Admin (1) သို့ ဆက်သွယ်ရန် (@Nazzpar)", url="https://t.me/Nazzpar"
  )
  btn_admin2 = types.InlineKeyboardButton(
      "💬 Admin (2) သို့ ဆက်သွယ်ရန် (@hikarikenn)",
      url="https://t.me/hikarikenn",
  )
  btn5 = types.InlineKeyboardButton(
      "👑 Nasspar's Premium Channel အကြောင်း", callback_data="premium_info"
  )

  markup.add(btn1, btn2, btn3, btn_admin1, btn_admin2, btn5)
  bot.send_message(
      chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup
  )


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  log_user_activity(message, "Bot စတင်သုံးစွဲရန် (/start) နှိပ်ခဲ့သည်")

  if not check_user_subscription(user_id):
    markup = types.InlineKeyboardMarkup()
    btn_channel = types.InlineKeyboardButton(
        "📢 Channel သို့သွား၍ Join ရန်",
        url="https://t.me/seriesmoviesplanet007",
    )
    btn_check = types.InlineKeyboardButton(
        "🔄 Join ပြီးပြီ (စစ်ဆေးရန်)", callback_data="check_sub"
    )
    markup.add(btn_channel)
    markup.add(btn_check)

    bot.send_message(
        message.chat.id,
        "⚠️ **ချန်နယ် Join ရန် လိုအပ်ပါသည်**\n\n"
        f"ဤ Bot အား အသုံးမပြုမီ ကျေးဇူးပြု၍ ကျွန်ုပ်တို့၏ Channel"
        f" ({CHANNEL_USERNAME}) ကို ဦးစွာ Join ပေးပါရန် မေတ္တာရပ်ခံအပ်ပါတယ်ခင်ဗျာ။ 🙏",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return

  show_main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  user_id = call.from_user.id
  chat_id = call.message.chat.id

  if call.data == "check_sub":
    if check_user_subscription(user_id):
      bot.answer_callback_query(call.id, "✅ Channel Join ပြီးသားဖြစ်ပါသည်!")
      bot.delete_message(chat_id, call.message.message_id)
      show_main_menu(chat_id)
    else:
      bot.answer_callback_query(
          call.id,
          "❌ ကျေးဇူးပြု၍ Channel ကို ဦးစွာ Join ပေးပါ!",
          show_alert=True,
      )

  elif call.data == "about_joe":
    bot.answer_callback_query(call.id)
    joe_text = (
        "🥊 **Ashita No Joe (Tomorrow's Joe) အကြောင်း**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 အာရှနှင့် ကမ္ဘာ့လက်ဝှေ့အန်နီမေးရှင်းသမိုင်းတွင် အထင်ကရ အကောင်းဆုံး"
        " ဂန္တဝင်လက်ရာ တစ်ခုဖြစ်ပြီး လူငယ်ဘဝ ရုန်းကန်လှုပ်ရှားမှုများကို"
        " ရင်နင့်ဖွယ် ရိုက်ကူးပြသထားပါတယ်။\n\n"
        "📺 **Season အချက်အလက်များ:**\n"
        "• Season 1 - Episode 79\n"
        "• Season 2 - Episode 47\n"
        "• Total Episodes - 126 ပိုင်းတိတိ\n\n"
        "📅 **ထွက်ရှိသည့်ခုနှစ်:** 1970 - 1981\n"
        "⭐ **IMDb Rating:** 8.2 / 10\n\n"
        "💰 **Member ကြေး:** ၅,၀၀၀ ကျပ် (5k)\n"
        "⚠️ *(Ashita No Joe Series တစ်ခုတည်းအတွက် သီးသန့်ဖြစ်သည်)*"
    )
    bot.send_message(chat_id, joe_text, parse_mode="Markdown")

  elif call.data == "payment_info":
    bot.answer_callback_query(call.id)
    pay_prompt_text = (
        "💳 **Member ကြေး ပေးချေရန် ပတ်သတ်၍ အောက်ပါတို့မှ နှစ်သက်ရာကို ရွေးချယ်"
        " နိုင်ပါတယ်။** ✨"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_direct = types.InlineKeyboardButton(
        "👤 Admin ထံ တိုက်ရိုက် ငွေပေးချေရန်", callback_data="pay_direct"
    )
    btn_bot_pay = types.InlineKeyboardButton(
        "🤖 Bot ထဲ၌ တိုက်ရိုက်ပေးချေပြီး ပြန်ကြားချက် စောင့်ဆိုင်းရန်",
        callback_data="pay_bot",
    )
    markup.add(btn_direct, btn_bot_pay)
    bot.send_message(
        chat_id, pay_prompt_text, parse_mode="Markdown", reply_markup=markup
    )

  elif call.data == "pay_direct":
    bot.answer_callback_query(call.id)
    direct_text = (
        "💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• 💸 KBZ Pay:\n"
        f"`{KAY_PHONE}`\n"
        "• 💸 Wave Pay:\n"
        f"`{WAVE_PHONE}`\n"
        "• 👤 Account Name:\n"
        f"`{ACCOUNT_NAME}`\n"
        "• 💵 ကျသင့်ငွေ:\n"
        "၅,၀၀၀ ကျပ် (Joe Series သီးသန့်)\n\n"
        "📷 ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံသို့ တိုက်ရိုက်ဆက်သွယ်ပေးပါ"
        " ခင်ဗျာ။ 🙏\n\n"
        "• Owner Acc: @Nazzpar\n"
        "• Admin Acc: @hikarikenn"
    )
    bot.send_message(chat_id, direct_text, parse_mode="Markdown")

  elif call.data == "pay_bot":
    bot.answer_callback_query(call.id)
    bot_pay_text = (
        "💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• 💸 KBZ Pay:\n"
        f"`{KAY_PHONE}`\n"
        "• 💸 Wave Pay:\n"
        f"`{WAVE_PHONE}`\n"
        "• 👤 Account Name:\n"
        f"`{ACCOUNT_NAME}`\n"
        "• 💵 ကျသင့်ငွေ:\n"
        "၅,၀၀၀ ကျပ် (Joe Series သီးသန့်)\n\n"
        "⚠️ **မိတ်ဆွေ၏ ငွေလွှဲပြေစာ ကို Bot ထဲသို့ပေးပို့ ၍ ပြန်ကြားချက်အား"
        " စောင့်ဆိုင်းပါရန်။** 📸✨"
    )
    bot.send_message(chat_id, bot_pay_text, parse_mode="Markdown")

  elif call.data == "premium_info":
    bot.answer_callback_query(call.id)
    prem_text = (
        "👑 **Nasspar's Premium Channel**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 လက်ရှိတွင် Premium Channel သီးသန့်ကြီးအနေဖြင့် မဖွင့်လှစ်သေးပါ။"
        " ဝန်ဆောင်မှုအသစ်များ ထွက်ရှိလာပါက ဤ Bot မှတစ်ဆင့် အမြန်ဆုံး"
        " အသိပေးသွားပါမည်။ 🌟"
    )
    bot.send_message(chat_id, prem_text, parse_mode="Markdown")

  elif call.data.startswith("approve_"):
    target_uid = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "✅ အတည်ပြုပြီးပါပြီ။")

    try:
      chat_member = bot.get_chat(target_uid)
      u_name = f"{chat_member.first_name or ''} {chat_member.last_name or ''}".strip()
      u_uname = chat_member.username or "None"
    except Exception:
      u_name = "Unknown User"
      u_uname = "None"

    save_member_record(target_uid, u_name, u_uname)

    success_text = (
        "ဂုဏ်ယူပါတယ်..👏\n"
        "မိတ်ဆွေ Ashita No Joe Series အတွက် တစ်သက် စာ Member ဝင် တစ်ဦးဖြစ်သွားပါပြီ..👑\n"
        "ဝယ်ယူ အားပေးမှုအတွက် အထူး ကျေးဇူးတင်ရှိပါတယ်ခင်ဗျာ..✨"
    )
    markup_prem = types.InlineKeyboardMarkup()
    btn_prem_link = types.InlineKeyboardButton(
        "Ashita No Joe Premium Channel ထဲသို့ ဝင်ရန်။👑",
        url=PREMIUM_CHANNEL_LINK,
    )
    markup_prem.add(btn_prem_link)

    try:
      bot.send_message(
          target_uid, success_text, parse_mode="Markdown", reply_markup=markup_prem
      )
    except Exception as e:
      print(f"လင့်ခ်ပို့ရာတွင် အမှားဖြစ်သည်: {e}")

    try:
      bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
      bot.send_message(
          chat_id,
          f"✅ User ID (`{target_uid}`) အား Member အဖြစ် အောင်မြင်စွာ ခွင့်ပြုပေးလိုက်ပါပြီ။",
          parse_mode="Markdown",
      )
    except Exception:
      pass

  elif call.data.startswith("reject_"):
    target_uid = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "❌ ပယ်ဖျက်လိုက်ပါပြီ။")

    try:
      bot.send_message(
          target_uid,
          "❌ တောင်းပန်ပါတယ်ခင်ဗျာ။ တင်ပြလာသော ငွေလွှဲပြေစာ (Screenshot) မှာ မှန်ကန်မှုမရှိပါ သို့မဟုတ် အတည်မပြုနိုင်ပါ။ ကျေးဇူးပြု၍ Admin ထံ တိုက်ရိုက်ဆက်သွယ်စုံစမ်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။ 🙏",
      )
    except Exception as e:
      print(f"ပယ်ဖျက်ကြောင်းအကြောင်းကြားရာတွင် အမှားဖြစ်သည်: {e}")

    try:
      bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
      bot.send_message(
          chat_id,
          f"❌ User ID (`{target_uid}`) ၏ ငွေလွှဲပြေစာကို ပယ်ဖျက်လိုက်ပါပြီ။",
          parse_mode="Markdown",
      )
    except Exception:
      pass


# 1. Screenshot (ပုံ) လက်ခံပြီး Creator ဆီ ပို့မည့် Handler
@bot.message_handler(content_types=["photo"])
def handle_user_screenshot(message):
  user = message.from_user
  user_id = user.id
  name = f"{user.first_name or ''} {user.last_name or ''}".strip()
  username = f"@{user.username}" if user.username else "Username မရှိပါ"
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  auto_reply = (
      "Admin ထံ ငွေလွှဲပြေစာပေးပို့ပြီးပါပြီ ၂၄ နာရီ အတွင်း ပြန်လည်ဖြေကြားပေးသွားပါမည်။"
      " (အားပေးမှု အတွက် အထူးကျေးဇူးတင်ရှိပါတယ်။)"
  )
  bot.reply_to(message, auto_reply)

  caption_text = (
      f"📥 **[New Payment Screenshot Received]** 📸\n"
      f"━━━━━━━━━━━━━━━━━━━━━━\n"
      f"👤 **အမည်:** {name}\n"
      f"🔗 **Username:** {username}\n"
      f"🆔 **User ID:** `{user_id}`\n"
      f"⚡ **လုပ်ဆောင်ချက်:** ငွေလွှဲပြေစာ (Screenshot) ပို့ထားခြင်း\n"
      f"🕒 **အချိန်:** {current_time}"
  )

  admin_markup = types.InlineKeyboardMarkup(row_width=2)
  btn_approve = types.InlineKeyboardButton(
      "✅ အတည်ပြုရန် (Approve)", callback_data=f"approve_{user_id}"
  )
  btn_reject = types.InlineKeyboardButton(
      "❌ ပယ်ဖျက်ရန် (Reject)", callback_data=f"reject_{user_id}"
  )
  admin_markup.add(btn_approve, btn_reject)

  try:
    photo_file_id = message.photo[-1].file_id
    bot.send_photo(
        CREATOR_ID,
        photo_file_id,
        caption=caption_text,
        parse_mode="Markdown",
        reply_markup=admin_markup,
    )
  except Exception as e:
    print(f"Creator ဆီသို့ ပုံပို့ရာတွင် အမှားဖြစ်သည်: {e}")


# 2. သာမန်စာသားများအတွက် Groq AI (Llama 3) ဖြင့် တုံ့ပြန်မည့် Handler (ပုံများကို ဝင်မဖမ်းစေရန် ခြွင်းချက်ထည့်ထားသည်)
@bot.message_handler(
    func=lambda message: True,
    content_types=["text", "audio", "document", "video", "voice"],
)
def handle_groq_chat(message):
  try:
    # စာသား (Text) သို့မဟုတ် content မပါပါက ကျော်ရန်
    if not message.text:
      return

    user_text = message.text

    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    ai_reply = (
        f"🤖 **Nasspar's Bot AI Assistant:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{completion.choices[0].message.content}"
    )
    bot.reply_to(message, ai_reply, parse_mode="Markdown")
  except Exception as e:
    print(f"Groq API Error: {e}")
    fallback_reply = (
        "🤖 **Nasspar's Bot AI Assistant:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "လက်ရှိတွင် AI တုံ့ပြန်မှု အနည်းငယ်နှေးကွေးနေပါသည်။ အသေးစိတ်သိရှိလိုပါက"
        " Admin များဖြစ်သော @Nazzpar နှင့် @hikarikenn ထံသို့ တိုက်ရိုက်"
        " ဆက်သွယ်စုံစမ်းနိုင်ပါတယ် ခင်ဗျာ။ 🙏"
    )
    bot.reply_to(message, fallback_reply, parse_mode="Markdown")


if __name__ == "__main__":
  print("Bot is running with Groq API & Payment Approval System...")
  bot.infinity_polling()
