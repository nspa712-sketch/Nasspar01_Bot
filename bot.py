import os
import html
import time
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import telebot
from telebot import types

# =========================================================
# 1. CONFIGURATION
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set BOT_TOKEN in Railway Variables.")

CREATOR_ID = 5188275898

CHANNEL_USERNAME = "@seriesmoviesplanet007"
CHANNEL_LINK = "https://t.me/seriesmoviesplanet007"
FREE_CHANNEL_LINK = "https://t.me/ashitanojoefreeep"

KAY_PHONE = "09448948562"
WAVE_PHONE = "09448948562"
ACCOUNT_NAME = "Nyein Sopyay Aung"

PREMIUM_CHANNEL_LINK = "https://t.me/+sFoFxmAXOVI5ZTg1"
MEMBER_PRICE = 5000

# Railway Persistent Volume သုံးပါက DB_FILE=/data/nasspar_bot.db ထားပါ။
DB_FILE = os.getenv("DB_FILE", "nasspar_bot.db")
DB_DIR = os.path.dirname(DB_FILE)
if DB_DIR:
    os.makedirs(DB_DIR, exist_ok=True)

TIMEZONE = ZoneInfo("Asia/Yangon")
MAX_MESSAGE_LENGTH = 3900

# =========================================================
# 2. LOGGING AND BOT CLIENT
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("NassparBot")
bot = telebot.TeleBot(TOKEN)

def current_time():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

# =========================================================
# 3. DATABASE
# =========================================================

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                joined_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                approved_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                screenshot_file_id TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                submitted_at TEXT,
                reviewed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                banned_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_user
            ON payments(user_id, status)
        """)
    logger.info("Database initialized successfully.")


initialize_database()

# =========================================================
# 4. USER MANAGEMENT
# =========================================================

def register_user(user):
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or ""
    with get_db() as conn:
        result = conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, first_name, username, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user.id, name, username, current_time()))
        is_new = result.rowcount > 0
        conn.execute("""
            UPDATE users SET first_name = ?, username = ?
            WHERE user_id = ?
        """, (name, username, user.id))
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return total_users, is_new


def is_banned(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row is not None


def is_verified_member(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id FROM members WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row is not None


def log_user_activity(message, action):
    try:
        user = message.from_user
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "Username မရှိပါ"
        total_users, is_new = register_user(user)
        status = "✨ User အသစ်" if is_new else "🔄 ပြန်လည်ဝင်ရောက်လာသူ"
        log_text = (
            "⚠️ <b>[Bot Activity Log]</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>အမည်:</b> {html.escape(name)}\n"
            f"🔗 <b>Username:</b> {html.escape(username)}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"⚡ <b>လုပ်ဆောင်ချက်:</b> {html.escape(action)}\n"
            f"📌 <b>Status:</b> {status}\n"
            f"👥 <b>Total Users:</b> {total_users}\n"
            f"🕒 <b>အချိန်:</b> {current_time()}"
        )
        bot.send_message(CREATOR_ID, log_text, parse_mode="HTML")
    except Exception:
        logger.exception("Activity logging failed.")

# =========================================================
# 5. SECURITY AND SUBSCRIPTION
# =========================================================

def is_admin(user_id):
    return user_id == CREATOR_ID


def check_user_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("creator", "administrator", "member"):
            return True
        if member.status == "restricted" and getattr(member, "is_member", False):
            return True
        return False
    except Exception:
        logger.exception("Subscription check failed.")
        return False


def subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Channel သို့ Join ရန်", url=CHANNEL_LINK),
        types.InlineKeyboardButton("🔄 Join ပြီးပြီ (စစ်ဆေးရန်)", callback_data="check_sub")
    )
    return markup


def require_subscription(message):
    if is_admin(message.from_user.id):
        return True
    register_user(message.from_user)
    if check_user_subscription(message.from_user.id):
        return True
    bot.send_message(
        message.chat.id,
        "⚠️ <b>Channel Join ရန် လိုအပ်ပါသည်။</b>\n\n"
        f"ကျေးဇူးပြု၍ {html.escape(CHANNEL_USERNAME)} သို့ ဦးစွာ Join ပေးပါခင်ဗျာ။",
        parse_mode="HTML",
        reply_markup=subscription_keyboard()
    )
    return False

# =========================================================
# 6. MESSAGE AND KEYBOARD UTILITIES
# =========================================================

def send_long_message(chat_id, text, reply_to=None):
    text = str(text or "")
    chunks = [
        text[i:i + MAX_MESSAGE_LENGTH]
        for i in range(0, len(text), MAX_MESSAGE_LENGTH)
    ] or [""]
    for index, chunk in enumerate(chunks):
        if index == 0 and reply_to:
            bot.reply_to(reply_to, chunk)
        else:
            bot.send_message(chat_id, chunk)


def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🥊 Ashita No Joe Series အကြောင်း", callback_data="about_joe"),
        types.InlineKeyboardButton("💳 Member ကြေး / ငွေပေးချေရန်", callback_data="payment_info"),
        types.InlineKeyboardButton("🎬 အစမ်းကြည့်ရှုရန်", url=FREE_CHANNEL_LINK),
        types.InlineKeyboardButton("💬 Admin (1) @Nazzpar", url="https://t.me/Nazzpar"),
        types.InlineKeyboardButton("💬 Admin (2) @hikarikenn", url="https://t.me/hikarikenn"),
        types.InlineKeyboardButton("👑 Premium Channel အကြောင်း", callback_data="premium_info")
    )
    return markup


def faq_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📖 ဇာတ်လမ်းအကျဉ်း", callback_data="faq_story"),
        types.InlineKeyboardButton("🥊 Joe ဆိုတာဘယ်သူလဲ", callback_data="faq_joe"),
        types.InlineKeyboardButton("🎭 ဇာတ်ကောင်များ", callback_data="faq_characters"),
        types.InlineKeyboardButton("🎬 Season / Episodes", callback_data="faq_episodes"),
        types.InlineKeyboardButton("✍️ ဖန်တီးသူများ", callback_data="faq_creators"),
        types.InlineKeyboardButton("⭐ ကြည့်သင့်လား", callback_data="faq_review"),
        types.InlineKeyboardButton("🔥 လူကြိုက်များမှု", callback_data="faq_legacy"),
        types.InlineKeyboardButton("💳 Member ဝင်နည်း", callback_data="faq_membership"),
        types.InlineKeyboardButton("🎞️ တခြား Series ရှိလား", callback_data="faq_catalog"),
        types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    ]
    markup.add(*buttons)
    return markup


def show_main_menu(chat_id):
    welcome_text = (
        "✨ <b>မင်္ဂလာပါ မိတ်ဆွေ...</b> 👋\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 Nasspar's Bot မှ ကြိုဆိုပါတယ်ခင်ဗျာ။\n\n"
        "🎬 အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် လိုအပ်သည်များကို လေ့လာနိုင်ပါတယ်။\n"
        "💬 Ashita No Joe အကြောင်း မေးလိုပါက FAQ ခလုတ်ကိုလည်း အသုံးပြုနိုင်ပါတယ်။"
    )
    bot.send_message(
        chat_id, welcome_text, parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


def show_faq_menu(chat_id):
    bot.send_message(
        chat_id,
        "🥊 <b>Ashita No Joe — မေးလေ့ရှိသော မေးခွန်းများ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "သိလိုသည့်အကြောင်းအရာကို အောက်ပါခလုတ်များမှ ရွေးချယ်ပါ။ "
        "စာရိုက်ပြီးလည်း မေးမြန်းနိုင်ပါတယ်။",
        parse_mode="HTML",
        reply_markup=faq_keyboard()
    )

# =========================================================
# 7. FACTUAL AUTO-REPLIES / FAQ CONTENT
# =========================================================

FAQ_ANSWERS = {
    "faq_story": (
        "📖 <b>Ashita No Joe — ဇာတ်လမ်းအကျဉ်း</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Ashita No Joe ဟာ ဘဝအခက်အခဲများကြားမှာ ကြီးပြင်းလာတဲ့ "
        "လူငယ်လေး Joe Yabuki ရဲ့ ဘဝကို အခြေခံထားတဲ့ လက်ဝှေ့ဇာတ်လမ်းပါ။\n\n"
        "Joe ဟာ အစပိုင်းမှာ စည်းကမ်းမဲ့ပြီး ရန်လိုတတ်သူတစ်ယောက်ဖြစ်ပေမဲ့ "
        "လက်ဝှေ့နည်းပြ Danpei Tange နဲ့ တွေ့ဆုံပြီးနောက် "
        "လက်ဝှေ့လောကထဲ ဝင်ရောက်လာပါတယ်။\n\n"
        "ဇာတ်လမ်းတစ်လျှောက် ပြိုင်ဘက်များ၊ လေ့ကျင့်မှု၊ ရှုံးနိမ့်မှု၊ "
        "အောင်မြင်မှုနဲ့ ကိုယ့်ဘဝရဲ့ အဓိပ္ပာယ်ကို ရှာဖွေမှုတွေကို "
        "စိတ်ခံစားမှု ပြင်းပြင်းထန်ထန်နဲ့ ဖော်ပြထားပါတယ်။"
    ),
    "faq_joe": (
        "🥊 <b>Joe Yabuki က ဘယ်သူလဲ?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Joe Yabuki ဟာ Ashita No Joe ရဲ့ အဓိကဇာတ်ကောင်ပါ။ "
        "အတိတ်ဘဝ မလွယ်ကူခဲ့တဲ့ လမ်းပေါ်က လူငယ်တစ်ယောက်ဖြစ်ပြီး "
        "သဘာဝအရည်အချင်း၊ သတ္တိနဲ့ မလျှော့တမ်းကြိုးစားမှုတို့ကြောင့် "
        "လက်ဝှေ့သမားတစ်ယောက် ဖြစ်လာပါတယ်။\n\n"
        "သူ့ရဲ့ အားသာချက်က ထိုးသတ်နိုင်စွမ်းတစ်ခုတည်း မဟုတ်ဘဲ "
        "အခက်အခဲတွေကို ရင်ဆိုင်တဲ့ စိတ်ဓာတ်နဲ့ သူ့ပြိုင်ဘက်တွေကြားက "
        "ဆက်ဆံရေးတွေပါပဲ။"
    ),
    "faq_characters": (
        "🎭 <b>အဓိက ဇာတ်ကောင်များ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🥊 <b>Joe Yabuki</b> — ဇာတ်လမ်းရဲ့ အဓိက လက်ဝှေ့သမား။\n"
        "🧢 <b>Danpei Tange</b> — Joe ကို လက်ဝှေ့လောကသို့ ဦးဆောင်ပေးတဲ့ နည်းပြ။\n"
        "🥊 <b>Rikiishi Toru</b> — Joe ရဲ့ အရေးကြီးဆုံး ပြိုင်ဘက်များထဲက တစ်ဦး။\n"
        "⭐ <b>Yoko Shiraki</b> — ဇာတ်လမ်းတွင် အရေးပါတဲ့ Shiraki မိသားစုဝင်။\n"
        "👊 <b>Nishi</b> — Joe နဲ့ နီးစပ်တဲ့ မိတ်ဆွေတစ်ဦး။\n\n"
        "ဇာတ်ကောင်တစ်ဦးချင်းစီရဲ့ အကြောင်းအရာတွေက ဇာတ်လမ်းတိုးတက်လာတာနဲ့အမျှ "
        "ပိုမိုပြည့်စုံလာပါတယ်။"
    ),
    "faq_episodes": (
        "🎬 <b>Season နဲ့ Episode အရေအတွက်</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📺 <b>Ashita No Joe (Season 1)</b> — 79 Episodes (1970–1971)\n"
        "📺 <b>Ashita No Joe 2 (Season 2)</b> — 47 Episodes (1980–1981)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "စုစုပေါင်း TV Series အပိုင်း 126 ပိုင်း ဖြစ်ပါတယ်။ "
        "ဒီအရေအတွက်မှာ ရုပ်ရှင်/အထူးအစီအစဉ်တွေ မပါဝင်ပါ။"
    ),
    "faq_creators": (
        "✍️ <b>Ashita No Joe ကို ဘယ်သူတွေ ဖန်တီးခဲ့သလဲ?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📚 <b>မူရင်း Manga ဇာတ်လမ်းရေးသူ</b> — Asao Takamori "
        "(အမည်ဝှက် Ikki Kajiwara)\n"
        "🎨 <b>Manga ပန်းချီရေးဆွဲသူ</b> — Tetsuya Chiba\n"
        "📺 <b>TV Anime Season 1</b> — ဒါရိုက်တာအဖြစ် Osamu Dezaki "
        "ပါဝင်ခဲ့ပါတယ်။\n\n"
        "မူရင်း Manga ကို 1968 မှ 1973 အတွင်း Weekly Shonen Magazine "
        "တွင် အမှတ်စဉ်ဖော်ပြခဲ့ပါတယ်။"
    ),
    "faq_review": (
        "⭐ <b>Ashita No Joe ကြည့်ကောင်းလား?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "လက်ဝှေ့ပွဲတွေကိုပဲ အဓိကထားတဲ့ Anime မဟုတ်ပါဘူး။ "
        "ဘဝရုန်းကန်မှု၊ ကိုယ့်ကိုယ်ကို ပြောင်းလဲတည်ဆောက်မှု၊ "
        "ပြိုင်ဘက်အပေါ် လေးစားမှုနဲ့ စိတ်ခံစားမှုတွေကို အဓိကထားပါတယ်။\n\n"
        "ဇာတ်လမ်းအရှိန်က ယနေ့ခေတ် Anime တွေနဲ့ နှိုင်းယှဉ်ရင် "
        "တချို့နေရာတွေမှာ နှေးနိုင်ပေမဲ့ Classic Sports Drama ကြိုက်သူ၊ "
        "ဇာတ်ကောင်ဖွံ့ဖြိုးမှုကို နှစ်သက်သူတွေအတွက် ကြည့်သင့်တဲ့ လက်ရာပါ။"
    ),
    "faq_legacy": (
        "🔥 <b>Ashita No Joe က လူကြိုက်များခဲ့လား?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "ဟုတ်ပါတယ်။ Ashita No Joe ဟာ ဂျပန် Manga နဲ့ Anime သမိုင်းမှာ "
        "အလွန်အရေးပါခဲ့တဲ့ Classic Sports Drama တစ်ခုပါ။ "
        "လက်ဝှေ့အားကစားကို လူငယ်ယဉ်ကျေးမှုနဲ့ ချိတ်ဆက်ဖော်ပြနိုင်ခဲ့ပြီး "
        "နောက်ပိုင်း Sports Manga/Anime လက်ရာများအပေါ်လည်း "
        "သက်ရောက်မှုရှိခဲ့ပါတယ်။\n\n"
        "လူကြိုက်များမှုကို တိကျတဲ့ လက်ရှိအဆင့်တစ်ခုအဖြစ် မဖော်ပြဘဲ "
        "သမိုင်းဝင်လွှမ်းမိုးမှုရှိတဲ့ လက်ရာအဖြစ် မှတ်ယူနိုင်ပါတယ်။"
    ),
    "faq_membership": (
        "💳 <b>Member ဘယ်လိုဝင်ရမလဲ?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Member ကြေး — <b>{MEMBER_PRICE:,} ကျပ်</b>\n"
        "1️⃣ ငွေပေးချေမှုနည်းလမ်းကို ရွေးပါ။\n"
        "2️⃣ KBZ Pay သို့မဟုတ် Wave Pay ဖြင့် ငွေလွှဲပါ။\n"
        "3️⃣ ငွေလွှဲပြေစာ Screenshot ကို Bot ထဲသို့ ပို့ပါ။\n"
        "4️⃣ Admin က စစ်ဆေးပြီး အတည်ပြုပေးပါမယ်။\n\n"
        "⚠️ Admin အတည်ပြုချက်မရမချင်း Member အဖြစ် မသတ်မှတ်သေးပါ။"
    ),
    "faq_catalog": (
        "🎞️ <b>တခြား Series / Anime တွေပါလား?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "လက်ရှိ ဒီ Bot ရဲ့ Member ဝန်ဆောင်မှုမှာ "
        "<b>Ashita No Joe Series</b> ကိုသာ သီးသန့်ဖော်ပြထားပါတယ်။\n\n"
        "တခြား Series သို့မဟုတ် Anime တွေကိုလည်း ထပ်မံထည့်သွင်းမယ်ဆိုရင် "
        "ဒီ Bot ကနေ ကြေညာပေးသွားပါမယ်။ လက်ရှိ မရရှိသေးတဲ့ Series တွေကို "
        "ရှိတယ်လို့ မမှားယွင်းပြောထားခြင်း မရှိပါ။"
    ),
    "faq_history": (
        "📜 <b>Ashita No Joe ရဲ့ သမိုင်းကြောင်း</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "မူရင်း Manga ကို 1968 ခုနှစ်မှာ စတင်ထုတ်ဝေခဲ့ပြီး "
        "1973 ခုနှစ်အထိ ဆက်လက်ဖော်ပြခဲ့ပါတယ်။\n\n"
        "ပထမ TV Anime ကို 1970–1971 ခုနှစ်မှာ ထုတ်လွှင့်ခဲ့ပြီး "
        "နောက်ဆက်တွဲ Ashita No Joe 2 ကို 1980–1981 ခုနှစ်မှာ "
        "ထုတ်လွှင့်ခဲ့ပါတယ်။\n\n"
        "လူငယ်တစ်ယောက်ရဲ့ လက်ဝှေ့ခရီးကိုသာမက လူမှုဘဝ၊ "
        "အိပ်မက်နဲ့ စိတ်ဓာတ်ခွန်အားတို့ကိုပါ ဖော်ပြနိုင်ခဲ့တာကြောင့် "
        "ဂျပန် Pop Culture ထဲမှာ မှတ်တမ်းဝင်ခဲ့တဲ့ လက်ရာတစ်ခု ဖြစ်လာပါတယ်။"
    ),
}

def payment_information():
    return (
        "💳 <b>Member ကြေး ပေးချေရန်</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💸 KBZ Pay: <code>{html.escape(KAY_PHONE)}</code>\n\n"
        f"💸 Wave Pay: <code>{html.escape(WAVE_PHONE)}</code>\n\n"
        f"👤 Account Name: <code>{html.escape(ACCOUNT_NAME)}</code>\n\n"
        f"💵 ကျသင့်ငွေ: <b>{MEMBER_PRICE:,} ကျပ်</b>\n"
        "⚠️ လက်ရှိ Member ဝန်ဆောင်မှုသည် Ashita No Joe Series အတွက်သာ ဖြစ်ပါတယ်။"
    )


def payment_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👤 Admin ထံ တိုက်ရိုက်ပေးချေရန်", callback_data="pay_direct"),
        types.InlineKeyboardButton("📸 Bot ထဲသို့ Screenshot ပို့ရန်", callback_data="pay_bot")
    )
    bot.send_message(
        chat_id, "💳 <b>ငွေပေးချေမှုနည်းလမ်း ရွေးချယ်ပါ။</b>",
        parse_mode="HTML", reply_markup=markup
    )


def normalize_text(text):
    return " ".join((text or "").lower().strip().replace("?", " ").replace("။", " ").split())


def auto_reply_for_text(user_text):
    """Keyword-based FAQ matching. Returns (reply_text, optional_keyboard)."""
    t = normalize_text(user_text)

    # Membership / price / payment questions
    if any(k in t for k in ["စျေး", "ဈေး", "ဘယ်လောက်", "member ကြေး", "မန်ဘာကြေး",
                            "အဖွဲ့ဝင်ကြေး", "ငွေဘယ်လောက်", "ကျသင့်ငွေ"]):
        return payment_information(), None

    if any(k in t for k in ["member ဝင်", "မန်ဘာဝင်", "member ဘယ်လို", "ဘယ်လိုဝင်",
                            "ဝင်ချင်", "ငွေလွှဲ", "ငွေပေးချေ", "ငွေချေ"]):
        return FAQ_ANSWERS["faq_membership"], None

    if any(k in t for k in ["kbz", "wave", "ဖုန်းနံပါတ်", "account name", "အကောင့်နာမည်"]):
        return payment_information(), None

    # Other content/catalog questions
    if any(k in t for k in ["တခြား series", "အခြား series", "တခြား anime", "အခြား anime",
                            "anime တွေ", "ဘာတွေပါ", "joe တစ်ခုတည်း", "တစ်ခုတည်းလား",
                            "တခြားကား", "အခြားကား"]):
        return FAQ_ANSWERS["faq_catalog"], None

    # Story / characters / production / history / episodes
    if any(k in t for k in ["ဇာတ်လမ်းအကျဉ်း", "အကျဉ်းချုပ်", "ဇာတ်လမ်းပြော", "ဇာတ်လမ်းကဘာ",
                            "ဇာတ်လမ်းဘယ်လို", "ဘာကား", "ဘာအကြောင်း"]):
        return FAQ_ANSWERS["faq_story"], None

    if any(k in t for k in ["joe ကဘယ်သူ", "joe ဘယ်သူ", "ဘယ်သူလဲ joe", "joe ဆိုတာ"]):
        return FAQ_ANSWERS["faq_joe"], None

    if any(k in t for k in ["ဇာတ်ကောင်", "character", "ရိကီရှီ", "rikiishi", "danpei", "yoko"]):
        return FAQ_ANSWERS["faq_characters"], None

    if any(k in t for k in ["ဘယ်သူရေး", "ရေးဆွဲ", "ပန်းချီ", "စာရေးသူ", "ဖန်တီးသူ",
                            "ဒါရိုက်တာ", "director", "author", "manga ရေး"]):
        return FAQ_ANSWERS["faq_creators"], None

    if any(k in t for k in ["အပိုင်း", "episode", "season", "ဘယ်နှပိုင်း", "ဘယ်လောက်ပိုင်း"]):
        return FAQ_ANSWERS["faq_episodes"], None

    if any(k in t for k in ["သမိုင်း", "ဘယ်တုန်းက", "ဘယ်နှစ်", "ထွက်ခဲ့", "ထုတ်လွှင့်"]):
        return FAQ_ANSWERS["faq_history"], None

    if any(k in t for k in ["ကြည့်ကောင်း", "ကြည့်သင့်", "ကောင်းလား", "ကြည့်ရမလား",
                            "recommend", "review", "rating"]):
        return FAQ_ANSWERS["faq_review"], None

    if any(k in t for k in ["လူကြိုက်", "ရေပန်းစား", "နာမည်ကြီး", "popular", "famous"]):
        return FAQ_ANSWERS["faq_legacy"], None

    if any(k in t for k in ["အကြောင်း", "မေးချင်", "help", "မေးခွန်း"]):
        return (
            "🥊 Ashita No Joe အကြောင်း ဘာသိချင်ပါသလဲခင်ဗျာ?\n"
            "အောက်က FAQ ခလုတ်တွေကို နှိပ်ပြီး မေးနိုင်ပါတယ်။",
            faq_keyboard()
        )

    return (
        "တောင်းပန်ပါတယ်ခင်ဗျာ။ ဒီမေးခွန်းအတွက် အဖြေကို FAQ ထဲမှာ မတွေ့သေးပါ။ "
        "အောက်က FAQ ခလုတ်ကို နှိပ်ကြည့်နိုင်သလို Admin @Nazzpar သို့မဟုတ် "
        "@hikarikenn ကိုလည်း ဆက်သွယ်မေးမြန်းနိုင်ပါတယ်။",
        faq_keyboard()
    )

# =========================================================
# 8. COMMANDS
# =========================================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "❌ Bot အသုံးပြုခွင့်ကို ပိတ်ထားပါသည်။")
        return
    log_user_activity(message, "Bot စတင်အသုံးပြုခြင်း (/start)")
    if not require_subscription(message):
        return
    show_main_menu(message.chat.id)


@bot.message_handler(commands=["faq", "help"])
def faq_command(message):
    if is_banned(message.from_user.id):
        return
    if not require_subscription(message):
        return
    show_faq_menu(message.chat.id)


@bot.message_handler(commands=["stats"])
def show_stats(message):
    if not is_admin(message.from_user.id):
        return
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM payments WHERE status='pending'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM payments WHERE status='approved'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM payments WHERE status='rejected'").fetchone()[0]
        banned = conn.execute("SELECT COUNT(*) FROM banned_users").fetchone()[0]
    response = (
        "📊 <b>Nasspar's Bot Dashboard</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <code>{total_users}</code>\n"
        f"👑 Total Members: <code>{total_members}</code>\n"
        f"⏳ Pending Payments: <code>{pending}</code>\n"
        f"✅ Approved Payments: <code>{approved}</code>\n"
        f"❌ Rejected Payments: <code>{rejected}</code>\n"
        f"🚫 Banned Users: <code>{banned}</code>\n"
        f"🕒 {current_time()}"
    )
    bot.reply_to(message, response, parse_mode="HTML")


@bot.message_handler(commands=["members"])
def show_members_list(message):
    if not is_admin(message.from_user.id):
        return
    with get_db() as conn:
        members = conn.execute("SELECT * FROM members ORDER BY approved_at DESC").fetchall()
    if not members:
        bot.reply_to(message, "📭 Member စာရင်း မရှိသေးပါ။")
        return
    bot.reply_to(message, f"👑 <b>Verified Members: {len(members)}</b>", parse_mode="HTML")
    output = ""
    for index, member in enumerate(members, 1):
        name = html.escape(member["name"] or "Unknown")
        username = html.escape("@" + member["username"] if member["username"] else "None")
        approved_at = html.escape(member["approved_at"] or "")
        line = (
            f"{index}. {name}\n"
            f"   Username: {username}\n"
            f"   ID: <code>{member['user_id']}</code>\n"
            f"   Date: {approved_at}\n\n"
        )
        if output and len(output) + len(line) > 3500:
            bot.send_message(message.chat.id, output, parse_mode="HTML")
            output = ""
        output += line
    if output:
        bot.send_message(message.chat.id, output, parse_mode="HTML")


@bot.message_handler(commands=["check"])
def check_specific_user(message):
    if not is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(message, "အသုံးပြုပုံ:\n/check USER_ID\n\nဥပမာ: /check 5188275898")
        return
    try:
        target_id = int(args[1])
        is_sub = check_user_subscription(target_id)
        with get_db() as conn:
            member = conn.execute("SELECT user_id FROM members WHERE user_id=?", (target_id,)).fetchone()
            payment = conn.execute("""
                SELECT status FROM payments WHERE user_id=?
                ORDER BY payment_id DESC LIMIT 1
            """, (target_id,)).fetchone()
        response = (
            f"🆔 User ID: <code>{target_id}</code>\n"
            f"📢 Channel: {'✅ Joined' if is_sub else '❌ Not Joined'}\n"
            f"👑 Member: {'✅ Verified' if member else '❌ Not Verified'}\n"
            f"💳 Latest Payment: {html.escape(payment['status'] if payment else 'No payment')}"
        )
        bot.reply_to(message, response, parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "❌ User ID ကို ဂဏန်းများဖြင့်သာ ရိုက်ထည့်ပါ။")


@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(message, "အသုံးပြုပုံ: /ban USER_ID")
        return
    try:
        target_id = int(args[1])
        if target_id == CREATOR_ID:
            bot.reply_to(message, "Owner ကို Ban လုပ်၍မရပါ။")
            return
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO banned_users (user_id, banned_at) VALUES (?, ?)",
                (target_id, current_time())
            )
        bot.reply_to(message, f"🚫 User <code>{target_id}</code> ကို Ban လုပ်ပြီးပါပြီ။", parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "မှန်ကန်သော User ID ထည့်ပါ။")


@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_admin(message.from_user.id):
        return
    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(message, "အသုံးပြုပုံ: /unban USER_ID")
        return
    try:
        target_id = int(args[1])
        with get_db() as conn:
            result = conn.execute("DELETE FROM banned_users WHERE user_id=?", (target_id,))
        if result.rowcount:
            bot.reply_to(message, f"✅ User {target_id} ကို Unban လုပ်ပြီးပါပြီ။")
        else:
            bot.reply_to(message, "ဒီ User ကို Ban မထားပါ။")
    except ValueError:
        bot.reply_to(message, "မှန်ကန်သော User ID ထည့်ပါ။")


@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    if not is_admin(message.from_user.id):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "အသုံးပြုပုံ:\n/broadcast သင့်ကြေညာချက်")
        return
    announcement = parts[1]
    with get_db() as conn:
        users = conn.execute("SELECT user_id FROM users").fetchall()
    success = failed = 0
    for row in users:
        uid = row["user_id"]
        if is_banned(uid):
            continue
        try:
            bot.send_message(
                uid,
                "📢 <b>Nasspar's Bot Announcement</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{html.escape(announcement)}",
                parse_mode="HTML"
            )
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
            logger.exception("Broadcast failed for user %s", uid)
    bot.reply_to(
        message,
        f"📊 <b>Broadcast Completed</b>\n\n✅ Success: {success}\n❌ Failed: {failed}",
        parse_mode="HTML"
    )

# =========================================================
# 9. CALLBACK HANDLER
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id if call.message else user_id
    data = call.data or ""

    if is_banned(user_id) and not is_admin(user_id):
        bot.answer_callback_query(call.id, "အသုံးပြုခွင့် ပိတ်ထားပါသည်။", show_alert=True)
        return

    if data == "check_sub":
        if check_user_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ Channel Join ပြီးပါပြီ!")
            if call.message:
                try:
                    bot.delete_message(chat_id, call.message.message_id)
                except Exception:
                    pass
            show_main_menu(chat_id)
        else:
            bot.answer_callback_query(call.id, "❌ Channel ကို ဦးစွာ Join ပေးပါ။", show_alert=True)
        return

    # Payment approval / rejection buttons are admin-only.
    if data.startswith(("approve_", "reject_")):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Admin Only!", show_alert=True)
            return
        try:
            action, payment_id_text, target_id_text = data.split("_")
            payment_id = int(payment_id_text)
            target_id = int(target_id_text)
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "Invalid payment information.", show_alert=True)
            return

        with get_db() as conn:
            payment = conn.execute("""
                SELECT * FROM payments
                WHERE payment_id=? AND user_id=? AND status='pending'
            """, (payment_id, target_id)).fetchone()
            if not payment:
                bot.answer_callback_query(call.id, "ဒီ Payment ကို အရင်က စစ်ဆေးပြီးဖြစ်သည်။", show_alert=True)
                return

            new_status = "approved" if action == "approve" else "rejected"
            result = conn.execute("""
                UPDATE payments SET status=?, reviewed_at=?
                WHERE payment_id=? AND status='pending'
            """, (new_status, current_time(), payment_id))
            if result.rowcount != 1:
                bot.answer_callback_query(call.id, "Payment ကို စစ်ဆေးပြီးပါပြီ။", show_alert=True)
                return

            if action == "approve":
                user_row = conn.execute(
                    "SELECT first_name, username FROM users WHERE user_id=?", (target_id,)
                ).fetchone()
                name = user_row["first_name"] if user_row else "Unknown User"
                username = user_row["username"] if user_row else ""
                conn.execute("""
                    INSERT INTO members (user_id, name, username, approved_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        name=excluded.name, username=excluded.username,
                        approved_at=excluded.approved_at
                """, (target_id, name, username, current_time()))

        bot.answer_callback_query(call.id, "အောင်မြင်စွာ ဆောင်ရွက်ပြီးပါပြီ။")
        if action == "approve":
            success_text = (
                "🎉 <b>ဂုဏ်ယူပါတယ်!</b> 👏\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "မိတ်ဆွေသည် Ashita No Joe Series အတွက် Member ဖြစ်သွားပါပြီ။ 👑\n\n"
                "ဝယ်ယူအားပေးမှုအတွက် အထူးကျေးဇူးတင်ရှိပါတယ်ခင်ဗျာ။ ✨"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👑 Premium Channel ထဲသို့ ဝင်ရန်", url=PREMIUM_CHANNEL_LINK))
            try:
                bot.send_message(target_id, success_text, parse_mode="HTML", reply_markup=markup)
            except Exception:
                logger.exception("Approval notification failed.")
            bot.send_message(chat_id, f"✅ User <code>{target_id}</code> အား Member အဖြစ် အတည်ပြုပြီးပါပြီ။", parse_mode="HTML")
        else:
            try:
                bot.send_message(
                    target_id,
                    "❌ <b>Payment Rejected</b>\n\n"
                    "တင်ပြလာသော ငွေလွှဲပြေစာကို အတည်မပြုနိုင်ပါ။\n\n"
                    "ကျေးဇူးပြု၍ Admin ထံ တိုက်ရိုက် ဆက်သွယ်စုံစမ်းပေးပါခင်ဗျာ။ 🙏",
                    parse_mode="HTML"
                )
            except Exception:
                logger.exception("Rejection notification failed.")
            bot.send_message(chat_id, f"❌ User <code>{target_id}</code> ၏ Payment ကို ပယ်ဖျက်ပြီးပါပြီ။", parse_mode="HTML")

        if call.message:
            try:
                bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
        return

    # All regular user-facing callbacks require channel subscription.
    if not is_admin(user_id) and not check_user_subscription(user_id):
        bot.answer_callback_query(call.id, "Channel ကို Join ပေးပါ။", show_alert=True)
        bot.send_message(chat_id, "⚠️ Channel Join လုပ်ရန် လိုအပ်ပါသည်။", reply_markup=subscription_keyboard())
        return

    if data == "about_joe":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, FAQ_ANSWERS["faq_story"], parse_mode="HTML", reply_markup=faq_keyboard())
    elif data == "payment_info":
        bot.answer_callback_query(call.id)
        payment_menu(chat_id)
    elif data == "pay_direct":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            payment_information() + "\n\n"
            "📷 ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ Admin ထံ တိုက်ရိုက်ပေးပို့ပါ။\n"
            "Owner: @Nazzpar\nAdmin: @hikarikenn",
            parse_mode="HTML"
        )
    elif data == "pay_bot":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            payment_information() + "\n\n"
            "📸 ငွေလွှဲပြီးပါက ပြေစာ Screenshot ကို ဤ Bot ထဲသို့ ပေးပို့ပေးပါ။\n"
            "Admin မှ စစ်ဆေးပြီး ပြန်လည်အကြောင်းကြားပေးပါမည်။",
            parse_mode="HTML"
        )
    elif data == "premium_info":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            "👑 <b>Nasspar's Premium Channel</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💌လက်ရှိတွင် Premium Channel သီးသန့် ဖွင့်လှစ်ထားခြင်းမရှိသေးပါ။ "
            "ဝန်ဆောင်မှုအသစ်များ ထွက်ရှိလာပါက ဤ Bot မှတစ်ဆင့် "
            "အကြောင်းကြားပေးသွားပါမည်။ 🌟\n"
            "(အားပေးလျက်ရှိသေး Subscribers တစ်ဦး ချင်းစီကို "
            "ကျေးဇူးအထူးတင်ရှိပါတယ် ခင်ဗျာ။💘)",
            parse_mode="HTML"
        )
    elif data in FAQ_ANSWERS:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, FAQ_ANSWERS[data], parse_mode="HTML", reply_markup=faq_keyboard())
    elif data == "main_menu":
        bot.answer_callback_query(call.id)
        show_main_menu(chat_id)
    else:
        bot.answer_callback_query(call.id)

# =========================================================
# 10. PAYMENT SCREENSHOT SYSTEM
# =========================================================

@bot.message_handler(content_types=["photo"])
def handle_user_screenshot(message):
    user = message.from_user
    user_id = user.id

    if is_banned(user_id):
        bot.reply_to(message, "❌ Bot အသုံးပြုခွင့် ပိတ်ထားပါသည်။")
        return
    if not require_subscription(message):
        return

    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or ""
    photo_file_id = message.photo[-1].file_id

    try:
        with get_db() as conn:
            existing = conn.execute(
                "SELECT payment_id FROM payments WHERE screenshot_file_id=?",
                (photo_file_id,)
            ).fetchone()
            if existing:
                bot.reply_to(message, "⚠️ ဤ Screenshot ကို ယခင်က ပေးပို့ထားပြီးဖြစ်ပါသည်။")
                return
            cursor = conn.execute("""
                INSERT INTO payments (user_id, screenshot_file_id, status, submitted_at)
                VALUES (?, ?, 'pending', ?)
            """, (user_id, photo_file_id, current_time()))
            payment_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        bot.reply_to(message, "⚠️ ဤ Screenshot ကို ထပ်မံလက်ခံ၍ မရပါ။")
        return
    except Exception:
        logger.exception("Could not save payment record.")
        bot.reply_to(message, "❌ ပြေစာသိမ်းဆည်းရာတွင် အမှားဖြစ်နေပါသည်။ Admin ကို ဆက်သွယ်ပါ။")
        return

    bot.reply_to(
        message,
        "✅ <b>ငွေလွှဲပြေစာ ပေးပို့ပြီးပါပြီ။</b>\n\n"
        "Admin မှ စစ်ဆေးပြီး ၂၄ နာရီအတွင်း ပြန်လည်အကြောင်းကြားပေးသွားပါမည်။\n\n"
        "အားပေးမှုအတွက် ကျေးဇူးတင်ရှိပါတယ်။ 🙏",
        parse_mode="HTML"
    )
    log_user_activity(message, "Payment Screenshot ပေးပို့ခြင်း")

    caption_text = (
        "📥 <b>New Payment Screenshot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: {html.escape(name)}\n"
        f"🔗 Username: {html.escape('@' + username if username else 'None')}\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"🧾 Payment ID: <code>{payment_id}</code>\n"
        "⏳ Status: Pending\n"
        f"🕒 Time: {current_time()}"
    )
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{payment_id}_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{payment_id}_{user_id}")
    )
    try:
        bot.send_photo(
            CREATOR_ID, photo_file_id, caption=caption_text,
            parse_mode="HTML", reply_markup=admin_markup
        )
    except Exception:
        logger.exception("Could not send payment screenshot to Creator.")
        bot.send_message(
            user_id,
            "⚠️ Admin ထံ Screenshot ပို့ရာတွင် အခက်အခဲရှိနေပါသည်။ "
            "ကျေးဇူးပြု၍ @Nazzpar သို့ ဆက်သွယ်ပေးပါ။"
        )

# =========================================================
# 11. TEXT AUTO-REPLY HANDLER (NO AI / NO GROQ)
# =========================================================

@bot.message_handler(content_types=["text"], func=lambda message: True)
def handle_auto_reply(message):
    user_id = message.from_user.id
    user_text = (message.text or "").strip()

    if not user_text or user_text.startswith("/"):
        return
    if is_banned(user_id):
        return
    if not require_subscription(message):
        return

    reply_text, keyboard = auto_reply_for_text(user_text)
    bot.reply_to(
        message,
        reply_text,
        parse_mode="HTML" if "<b>" in reply_text or "<code>" in reply_text else None,
        reply_markup=keyboard
    )

# =========================================================
# 12. START BOT
# =========================================================

if __name__ == "__main__":
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Nasspar's Bot is starting...")
    logger.info("Keyword Auto Reply: Enabled")
    logger.info("Groq / AI integration: Removed")
    logger.info("SQLite Database: Enabled")
    logger.info("Payment System: Enabled")
    logger.info("Admin Security: Enabled")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    try:
        bot.remove_webhook()
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception:
        logger.exception("Bot polling stopped unexpectedly.")
