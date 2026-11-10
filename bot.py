Import os
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
      f"📊 **Bot Statistics:**\n\n👥 စုစုပေါင်း အသုံးပြုသူ (Total Users):"
      f" `{total_users}` ယောက်",
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
      "မင်္ဂလာပါ မိတ်ဆွေ..👋\n"
      "ကျွန်တော်ကတော့ Nasspar's bot ပဲ ဖြစ်ပါတယ်..🤖\n\n"
      "သင်သိလိုသော အကြောင်းအရာများကို အောက်တွင် ဖော်ပြထားသော ခလုတ်များကို နှိပ်၍"
      " လေ့လာနိုင်ပါတယ် ခင်ဗျာ..✨\n"
      "(သို့မဟုတ်) Ashita No Joe အကြောင်းနှင့် ပတ်သက်သည်များကို စာတိုပေးပို့၍"
      " မေးမြန်းနိုင်ပါသည် 🧠"
  )

  markup = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "🥊 Ashita No Joe Series အကြောင်း လေ့လာရန်", callback_data="about_joe"
  )
  btn2 = types.InlineKeyboardButton(
      "💳 Ashita No Joe အတွက် ငွေပေးချေရန်", callback_data="payment_info"
  )
  btn3 = types.InlineKeyboardButton(
      "🎬 Ashita No Joe အစမ်းကြည့်ရန် (Channel)",
      url="https://t.me/ashitanojoefreeep",
  )
  btn_admin1 = types.InlineKeyboardButton(
      "💬 Admin (1) ဆက်သွယ်ရန်", url="https://t.me/Nazzpar"
  )
  btn_admin2 = types.InlineKeyboardButton(
      "💬 Admin (2) ဆက်သွယ်ရန်", url="https://t.me/hikarikenn"
  )
  btn5 = types.InlineKeyboardButton(
      "🔒 Nasspar's Premium Channel အကြောင်း", callback_data="premium_info"
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
        "⚠️ **မင်္ဂလာပါ မိတ်ဆွေ...**\n\n"
        f"ဤ Bot အား အသုံးမပြုမီ ကျေးဇူးပြု၍ ကျွန်ုပ်တို့၏ Channel"
        f" ({CHANNEL_USERNAME}) ကို Join ပေးပါရန် မေတ္တာရပ်ခံအပ်ပါတယ်ခင်ဗျာ။",
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
        "🥊 **Ashita No Joe (Tomorrow's Joe) အကြောင်း**\n\n"
        "Ashita no Joe ဟာ နာမည်ကြီး ဂန္တဝင် လက်ဝှေ့ အန်နီမေးရှင်း ဇာတ်ကား"
        " တစ်ကားဖြစ်ပြီး လူငယ်ဘဝ ရုန်းကန်လှုပ်ရှားမှုများကို အကောင်းဆုံး"
        " ရိုက်ကူးပြသထားပါတယ်။\n\n"
        "Ashita No Joe ခေါ် Tomorrow's Joe က Season အားဖြင့် ၂ ခု ထိ"
        " ထွက်ရှိထားပါတယ်။\n\n"
        "• Season 1 - Episode 79\n"
        "• Season 2 - Episode 47\n"
        "• Total Episode: 126\n\n"
        "• Released Date: (1970 - 1981)\n"
        "• IMDb 8.2/10\n"
        "• Running Time: Avg 25 min\n\n"
        "👑 Member ကြေး ၅၀၀၀ကျပ် (5k)\n\n"
        "⚠️ **Ashita No Joe Series တစ်ခုတည်း အတွက်သာ ဖြစ်သည်။**\n\n"
        "ဒီဇာတ်ကားကို ကျွန်ုပ်တို့ Channel မှာ မြန်မာစာတန်းထိုးဖြင့် အပြည့်အစုံ"
        " ကြည့်ရှုနိုင်ပါတယ်။"
    )
    bot.send_message(chat_id, joe_text, parse_mode="Markdown")

  elif call.data == "payment_info":
    bot.answer_callback_query(call.id)
    pay_text = (
        f"💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n\n"
        f"• KBZ Pay: `{KAY_PHONE}`\n"
        f"• Wave Pay: `{WAVE_PHONE}`\n"
        f"• Account Name: `{ACCOUNT_NAME}`\n"
        f"• ကျသင့်ငွေ: ၅,၀၀၀ ကျပ် (Joe Series တစ်ခု တည်းအတွက် သီးသန့်)\n\n"
        "ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံသို့ ဆက်သွယ်ပေးပါရန်"
        " မေတ္တာရပ်ခံအပ်ပါတယ်။"
    )
    bot.send_message(chat_id, pay_text, parse_mode="Markdown")

  elif call.data == "premium_info":
    bot.answer_callback_query(call.id)
    prem_text = (
        "👑 **Nasspar's Premium Channel**\n\n"
        "လက်ရှိတွင် Premium Channel သီးသန့် မဖွင့်လှစ်သေးပါ။ ဝန်ဆောင်မှုအသစ်များ"
        " ထွက်ရှိပါက ဤ Bot မှတစ်ဆင့် အသိပေးသွားပါမည်။ 📵"
    )
    bot.send_message(chat_id, prem_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
  text = message.text.lower()

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
        f"💳 **Member ကြေး ပေးချေရန် အချက်အလက်များ**\n\n"
        f"• ကျသင့်ငွေ: ၅,၀၀၀ ကျပ် (Joe Series တစ်ခုတည်းအတွက် သီးသန့်)\n"
        f"• KBZ Pay: `{KAY_PHONE}`\n"
        f"• Wave Pay: `{WAVE_PHONE}`\n"
        f"• Account Name: `{ACCOUNT_NAME}`\n\n"
        "ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံသို့ ဆက်သွယ်ပေးပါရန်"
        " မေတ္တာရပ်ခံအပ်ပါတယ်။"
    )
    bot.reply_to(message, reply)

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
        "🥊 **Ashita No Joe အချက်အလက်များ:**\n\n"
        "• Season 1 - Episode 79\n"
        "• Season 2 - Episode 47\n"
        "• Total Episode: 126\n"
        "• IMDb: 8.2/10\n\n"
        "⚠️ **Ashita No Joe Series တစ်ခုတည်းအတွက်သာ ဖြစ်ပါသည်။**\n"
        "လက်ရှိတွင် တခြားကားများအတွက် Premium သီးသန့် မဖွင့်လှစ်သေးပါ။"
    )
    bot.reply_to(message, reply)

  else:
    ai_reply = (
        "🤖 **Nasspar's Bot AI Assistant:**\n\n"
        "မိတ်ဆွေ မေးမြန်းထားသော အချက်အလက်အတွက် အောက်ပါ Admin များထံသို့"
        " တိုက်ရိုက် ဆက်သွယ်စုံစမ်းနိုင်ပါတယ် ခင်ဗျာ-\n"
        "• Admin (1): @Nazzpar\n"
        "• Admin (2): @hikarikenn"
    )
    bot.reply_to(message, ai_reply)


if __name__ == "__main__":
  print("Bot is running...")
  bot.infinity_polling()