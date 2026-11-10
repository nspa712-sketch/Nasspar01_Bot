import os
from datetime import datetime
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@seriesmoviesplanet007"
CREATOR_ID = 5188275898

KAY_PHONE = "09448948562"
WAVE_PHONE = "09448948562"
ACCOUNT_NAME = "Nyein Sopyay Aung"

bot = telebot.TeleBot(TOKEN)
USER_DATA_FILE = "unique_users.txt"


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
      "💬 **Ashita No Joe** ဇာတ်ကားအကြောင်း၊ သမိုင်းကြောင်းများကိုလည်း စာတိုပေးပို့၍"
      " လွတ်လပ်စွာ မေးမြန်းနိုင်ပါတယ် 🧠✨"
  )

  markup = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "🥊 Ashita No Joe Series အကြောင်း လေ့လာရန်", callback_data="about_joe"
  )
  btn2 = types.InlineKeyboardButton(
      "💳 Member ကြေး ငွေပေးချေရန်", callback_data="payment_info"
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
        "⚠️ *(Ashita No Joe Series တစ်ခုတည်းအတွက် သီးသန့်ဖြစ်သည်)*\n\n"
        "✨ မြန်မာစာတန်းထိုးဖြင့် အပြည့်အစုံကို ကျွန်ုပ်တို့ ချန်နယ်တွင်"
        " ကြည့်ရှုနိုင်ပါပြီ!"
    )
    bot.send_message(chat_id, joe_text, parse_mode="Markdown")

  elif call.data == "payment_info":
    bot.answer_callback_query(call.id)
    pay_text = (
        "💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• 💸 KBZ Pay: `{KAY_PHONE}`\n"
        f"• 💸 Wave Pay: `{WAVE_PHONE}`\n"
        f"• 👤 Account Name: `{ACCOUNT_NAME}`\n"
        f"• 💵 ကျသင့်ငွေ: ၅,၀၀၀ ကျပ် (Joe Series သီးသန့်)\n\n"
        "📷 ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံသို့ တိုက်ရိုက်ဆက်သွယ်ပေးပါ"
        " ခင်ဗျာ။ 🙏"
    )
    bot.send_message(chat_id, pay_text, parse_mode="Markdown")

  elif call.data == "premium_info":
    bot.answer_callback_query(call.id)
    prem_text = (
        "👑 **Nasspar's Premium Channel**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 လက်ရှိတွင် Premium Channel သီးသန့်ကြီးအနေဖြင့် မဖွင့်လှစ်သေးပါ။"
        " ဝန်ဆောင်မှုအသစ်များ ထွက်ရှိလာပါက ဤ Bot မှတစ်ဆင့် အမြန်ဆုံး"
        " အသိပေးသွားပါမည်။ စောင့်မျှော်အားပေးကြပါဦး ခင်ဗျာ။ 🌟"
    )
    bot.send_message(chat_id, prem_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
  text = message.text.lower()

  # ငွေပေးချေမှုဆိုင်ရာ
  if any(
      kw in text
      for kw in [
          "ဈေး",
          "ဘယ်လောက်",
          "ငွေ",
          "လွှဲ",
          "ကြေး",
          "ပေး",
          "k",
          "member",
          "မန်ဘာ",
          "ဝယ်",
          "ဖိုး",
      ]
  ):
    reply = (
        "💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• 💵 ကျသင့်ငွေ: ၅,၀၀၀ ကျပ် (Joe Series တစ်ခုတည်းအတွက် သီးသန့်)\n"
        f"• 💸 KBZ Pay: `{KAY_PHONE}`\n"
        f"• 💸 Wave Pay: `{WAVE_PHONE}`\n"
        f"• 👤 Account Name: `{ACCOUNT_NAME}`\n\n"
        "📷 ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံသို့ ဆက်သွယ်ပေးပါရန်"
        " မေတ္တာရပ်ခံအပ်ပါတယ်။"
    )
    bot.reply_to(message, reply, parse_mode="Markdown")

  # အချက်အလက်ဆိုင်ရာ
  elif any(
      kw in text
      for kw in [
          "joe",
          "တစ်ခုတည်း",
          "တခြား",
          "ကား",
          "season",
          "ep",
          "episode",
          "ပိုင်း",
          "ဇာတ်လမ်း",
      ]
  ):
    reply = (
        "🥊 **Ashita No Joe အချက်အလက်များ:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• 📺 Season 1 - Episode 79\n"
        "• 📺 Season 2 - Episode 47\n"
        "• 🎬 Total Episodes: 126 ပိုင်း\n"
        "• ⭐ IMDb Rating: 8.2/10\n\n"
        "⚠️ **Ashita No Joe Series တစ်ခုတည်းအတွက်သာ ဖြစ်ပါသည်။**\n"
        "လက်ရှိတွင် တခြားကားများအတွက် Premium သီးသန့် မဖွင့်လှစ်သေးပါ။"
    )
    bot.reply_to(message, reply, parse_mode="Markdown")

  # သမိုင်းကြောင်းဆိုင်ရာ
  elif any(
      kw in text
      for kw in [
          "သမိုင်း",
          "history",
          "ဇာတ်ကြောင်း",
          "နောက်ခံ",
          "story",
          "about",
          "ဘယ်လို",
          "ဇာတ်ကောင်",
      ]
  ):
    reply = (
        "📖 **Ashita No Joe ၏ နောက်ခံသမိုင်းကြောင်း:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "ယဘုယျအားဖြင့် **Ashita no Joe** (Tomorrow's Joe) သည် ဂျပန်နိုင်ငံ၏"
        " အထင်ကရ ဂန္တဝင်လက်ဝှေ့မန်ဂါနှင့် အန်နီမေးရှင်း ဖြစ်ပါသည်။ Yabuki"
        " Joe အမည်ရှိ လူငယ်လေးတစ်ဦး ဆင်းရဲမွဲတေမှု၊ လမ်းပေါ်ဘဝမှသည်"
        " လက်ဝှေ့ကြိုးဝိုင်းအတွင်းသို့ ရောက်ရှိလာပုံ၊ ပြိုင်ဘက်များနှင့်"
        " ရင်ဆိုင်ရုန်းကန်ပုံများကို အလွန်ရင်သပ်ရှုမောဖွယ်"
        " တင်ဆက်ထားခြင်းဖြစ်ပါသည်။\n\n"
        "🥊 ၎င်း၏ ကြေကွဲဖွယ်ကောင်းသော ဇာတ်သိမ်းပိုင်းနှင့် လူငယ်ဘဝ ရုန်းကန်လှုပ်ရှားမှု"
        " အခိုက်အတန့်များသည် ကမ္ဘာတစ်ဝှမ်းရှိ ပရိသတ်များကို ယနေ့တိုင်"
        " ဖမ်းစားထားဆဲ ဖြစ်ပါတယ်။ ✨"
    )
    bot.reply_to(message, reply, parse_mode="Markdown")

  # လူကြိုက်များမှုဆိုင်ရာ
  elif any(
      kw in text
      for kw in ["popular", "နာမည်ကြီး", "လူကြိုက်များ", "top", "best", "rating"]
  ):
    reply = (
        "🌟 **Ashita No Joe ၏ နာမည်ကြီးမှုနှင့် အောင်မြင်မှု:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• 🏆 ဂျပန်နိုင်ငံ၏ အချိန်ကာလတိုင်းတွင် အကောင်းဆုံးနှင့် အထင်ရှားဆုံး"
        " အားကစားအန်နီမေးရှင်းစာရင်းဝင် တစ်ခုဖြစ်ပါသည်။\n"
        "• ⭐ IMDb တွင် 8.2 အထိ မြင့်မားသော Rating ရရှိထားပြီး၊"
        " ဝေဖန်ရေးသမားများနှင့် ပရိသတ်များ၏ အသိအမှတ်ပြုမှုကို အပြည့်အဝ"
        " ရရှိထားသော လက်ရာမြောက် ဇာတ်ကားကောင်း ဖြစ်ပါသည်။ 🔥"
    )
    bot.reply_to(message, reply, parse_mode="Markdown")

  # Fallback
  else:
    ai_reply = (
        "🤖 **Nasspar's Bot AI Assistant:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "မိတ်ဆွေ မေးမြန်းထားသော အချက်အလက်နှင့် ပတ်သက်၍ အသေးစိတ်သိရှိလိုပါက"
        " အောက်ပါ Admin များထံသို့ တိုက်ရိုက် ဆက်သွယ်စုံစမ်းနိုင်ပါတယ် ခင်ဗျာ-👇\n\n"
        "• 💬 Admin (1): @Nazzpar\n"
        "• 💬 Admin (2): @hikarikenn"
    )
    bot.reply_to(message, ai_reply, parse_mode="Markdown")


if __name__ == "__main__":
  print("Bot is running...")
  bot.infinity_polling()
