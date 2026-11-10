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
from groq import Groq


# =========================================================
# 1. CONFIGURATION
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Set BOT_TOKEN in Railway Variables."
    )

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
MODEL_NAME = "llama-3.3-70b-versatile"

MAX_HISTORY_MESSAGES = 12
MAX_MESSAGE_LENGTH = 3900

# =========================================================
# 2. LOGGING AND CLIENTS
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("NassparBot")

bot = telebot.TeleBot(TOKEN)
groq_client = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq API initialized successfully.")
    except Exception:
        logger.exception("Groq initialization failed.")
else:
    logger.warning("GROQ_API_KEY is missing. AI replies are disabled.")


def current_time():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# 3. DATABASE
# =========================================================

@contextmanager
def get_db():
    """Open, commit/rollback, and always close an SQLite connection."""
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
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_user
            ON chat_history(user_id, id)
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
    name = (
        f"{user.first_name or ''} "
        f"{user.last_name or ''}"
    ).strip()
    username = user.username or ""

    with get_db() as conn:
        result = conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, first_name, username, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user.id, name, username, current_time()))

        is_new = result.rowcount > 0

        conn.execute("""
            UPDATE users
            SET first_name = ?, username = ?
            WHERE user_id = ?
        """, (name, username, user.id))

        total_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

    return total_users, is_new


def is_banned(user_id):
    with get_db() as conn:
        result = conn.execute("""
            SELECT user_id
            FROM banned_users
            WHERE user_id = ?
        """, (user_id,)).fetchone()
    return result is not None


def is_verified_member(user_id):
    with get_db() as conn:
        result = conn.execute("""
            SELECT user_id
            FROM members
            WHERE user_id = ?
        """, (user_id,)).fetchone()
    return result is not None


def save_member_record(user_id, name, username):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO members
            (user_id, name, username, approved_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                name = excluded.name,
                username = excluded.username,
                approved_at = excluded.approved_at
        """, (user_id, name, username or "", current_time()))


def log_user_activity(message, action):
    try:
        user = message.from_user
        name = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()
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

        if (
            member.status == "restricted"
            and getattr(member, "is_member", False)
        ):
            return True

        return False
    except Exception:
        logger.exception("Subscription check failed.")
        return False


def subscription_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📢 Channel သို့ Join ရန်",
        url=CHANNEL_LINK
    ))
    markup.add(types.InlineKeyboardButton(
        "🔄 Join ပြီးပြီ (စစ်ဆေးရန်)",
        callback_data="check_sub"
    ))
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
        f"ကျေးဇူးပြု၍ {html.escape(CHANNEL_USERNAME)} "
        "သို့ ဦးစွာ Join ပေးပါခင်ဗျာ။",
        parse_mode="HTML",
        reply_markup=subscription_keyboard()
    )
    return False


# =========================================================
# 6. MESSAGE UTILITIES
# =========================================================

def send_long_message(chat_id, text, reply_to=None):
    """
    AI response ကို plain text အဖြစ်ပို့သည်။
    HTML escape လုပ်ပြီး tag တွေကို literal ပြသသွားခြင်း မဖြစ်စေရန်
    parse_mode မသုံးထားပါ။
    """
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


def send_ai_fallback(message):
    bot.reply_to(
        message,
        "🤖 Nasspar's Bot AI Assistant\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "လက်ရှိတွင် AI တုံ့ပြန်မှု အနည်းငယ်နှေးကွေးနေပါသည်။\n\n"
        "အသေးစိတ်သိရှိလိုပါက Admin များဖြစ်သော "
        "@Nazzpar နှင့် @hikarikenn ထံ "
        "တိုက်ရိုက်ဆက်သွယ်နိုင်ပါတယ်ခင်ဗျာ။ 🙏"
    )


# =========================================================
# 7. MAIN MENU
# =========================================================

def show_main_menu(chat_id):
    welcome_text = (
        "✨ <b>မင်္ဂလာပါ မိတ်ဆွေ...</b> 👋\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 ကျွန်တော်ကတော့ <b>Nasspar's Bot</b> "
        "ရဲ့ AI Assistant ဖြစ်ပါတယ်ခင်ဗျာ။\n\n"
        "🎬 အောက်ပါ Menu ခလုတ်များကို အသုံးပြု၍ "
        "လိုအပ်သည်များကို လေ့လာနိုင်ပါတယ်။\n\n"
        "💬 <b>Ashita No Joe</b> အကြောင်းကိုလည်း "
        "AI နဲ့ လွတ်လပ်စွာ မေးမြန်းနိုင်ပါတယ်။ 🧠✨"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "🥊 Ashita No Joe Series အကြောင်း",
            callback_data="about_joe"
        ),
        types.InlineKeyboardButton(
            "💳 Member ကြေး ငွေပေးချေရန်",
            callback_data="payment_info"
        ),
        types.InlineKeyboardButton(
            "🎬 Ashita No Joe အစမ်းကြည့်ရန်",
            url=FREE_CHANNEL_LINK
        ),
        types.InlineKeyboardButton(
            "💬 Admin (1) @Nazzpar",
            url="https://t.me/Nazzpar"
        ),
        types.InlineKeyboardButton(
            "💬 Admin (2) @hikarikenn",
            url="https://t.me/hikarikenn"
        ),
        types.InlineKeyboardButton(
            "👑 Premium Channel အကြောင်း",
            callback_data="premium_info"
        )
    )

    bot.send_message(
        chat_id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# 8. COMMAND: START
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


# =========================================================
# 9. COMMAND: STATS
# =========================================================

@bot.message_handler(commands=["stats"])
def show_stats(message):
    if not is_admin(message.from_user.id):
        return

    with get_db() as conn:
        total_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        total_members = conn.execute(
            "SELECT COUNT(*) FROM members"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM payments WHERE status = 'pending'"
        ).fetchone()[0]
        approved = conn.execute(
            "SELECT COUNT(*) FROM payments WHERE status = 'approved'"
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM payments WHERE status = 'rejected'"
        ).fetchone()[0]
        banned = conn.execute(
            "SELECT COUNT(*) FROM banned_users"
        ).fetchone()[0]

    response = (
        "📊 <b>Nasspar's Bot Dashboard</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <code>{total_users}</code>\n"
        f"👑 Total Members: <code>{total_members}</code>\n"
        f"⏳ Pending Payments: <code>{pending}</code>\n"
        f"✅ Approved Payments: <code>{approved}</code>\n"
        f"❌ Rejected Payments: <code>{rejected}</code>\n"
        f"🚫 Banned Users: <code>{banned}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {current_time()}"
    )
    bot.reply_to(message, response, parse_mode="HTML")


# =========================================================
# 10. COMMAND: MEMBERS
# =========================================================

@bot.message_handler(commands=["members"])
def show_members_list(message):
    if not is_admin(message.from_user.id):
        return

    with get_db() as conn:
        members = conn.execute("""
            SELECT *
            FROM members
            ORDER BY approved_at DESC
        """).fetchall()

    if not members:
        bot.reply_to(message, "📭 Member စာရင်း မရှိသေးပါ။")
        return

    bot.reply_to(
        message,
        f"👑 <b>Verified Members: {len(members)}</b>",
        parse_mode="HTML"
    )

    output = ""
    for index, member in enumerate(members, 1):
        name = html.escape(member["name"] or "Unknown")
        username = member["username"] or ""
        username_text = html.escape(
            f"@{username}" if username else "None"
        )
        approved_at = html.escape(member["approved_at"] or "")

        line = (
            f"{index}. {name}\n"
            f"   Username: {username_text}\n"
            f"   ID: <code>{member['user_id']}</code>\n"
            f"   Date: {approved_at}\n\n"
        )

        if output and len(output) + len(line) > 3500:
            bot.send_message(message.chat.id, output, parse_mode="HTML")
            output = ""

        output += line

    if output:
        bot.send_message(message.chat.id, output, parse_mode="HTML")


# =========================================================
# 11. COMMAND: CHECK
# =========================================================

@bot.message_handler(commands=["check"])
def check_specific_user(message):
    if not is_admin(message.from_user.id):
        return

    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(
            message,
            "အသုံးပြုပုံ:\n/check USER_ID\n\nဥပမာ: /check 5188275898"
        )
        return

    try:
        target_id = int(args[1])

        is_sub = check_user_subscription(target_id)

        with get_db() as conn:
            member = conn.execute(
                "SELECT user_id FROM members WHERE user_id = ?",
                (target_id,)
            ).fetchone()
            payment = conn.execute("""
                SELECT status
                FROM payments
                WHERE user_id = ?
                ORDER BY payment_id DESC
                LIMIT 1
            """, (target_id,)).fetchone()

        response = (
            f"🆔 User ID: <code>{target_id}</code>\n"
            f"📢 Channel: {'✅ Joined' if is_sub else '❌ Not Joined'}\n"
            f"👑 Member: {'✅ Verified' if member else '❌ Not Verified'}\n"
            f"💳 Latest Payment: "
            f"{html.escape(payment['status'] if payment else 'No payment')}"
        )
        bot.reply_to(message, response, parse_mode="HTML")

    except ValueError:
        bot.reply_to(message, "❌ User ID ကို ဂဏန်းများဖြင့်သာ ရိုက်ထည့်ပါ။")


# =========================================================
# 12. COMMAND: BAN / UNBAN
# =========================================================

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
            conn.execute("""
                INSERT OR IGNORE INTO banned_users
                (user_id, banned_at)
                VALUES (?, ?)
            """, (target_id, current_time()))

        bot.reply_to(
            message,
            f"🚫 User <code>{target_id}</code> ကို Ban လုပ်ပြီးပါပြီ။",
            parse_mode="HTML"
        )
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
            result = conn.execute(
                "DELETE FROM banned_users WHERE user_id = ?",
                (target_id,)
            )

        if result.rowcount:
            bot.reply_to(
                message,
                f"✅ User {target_id} ကို Unban လုပ်ပြီးပါပြီ။"
            )
        else:
            bot.reply_to(message, "ဒီ User ကို Ban မထားပါ။")

    except ValueError:
        bot.reply_to(message, "မှန်ကန်သော User ID ထည့်ပါ။")


# =========================================================
# 13. COMMAND: BROADCAST
# =========================================================

@bot.message_handler(commands=["broadcast"])
def broadcast_message(message):
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(
            message,
            "အသုံးပြုပုံ:\n/broadcast သင့်ကြေညာချက်"
        )
        return

    announcement = parts[1]

    with get_db() as conn:
        users = conn.execute(
            "SELECT user_id FROM users"
        ).fetchall()

    success = 0
    failed = 0

    for user in users:
        uid = user["user_id"]

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
        "📊 <b>Broadcast Completed</b>\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}",
        parse_mode="HTML"
    )


# =========================================================
# 14. PAYMENT INFORMATION
# =========================================================

def payment_information():
    return (
        "💳 <b>Member ကြေး ပေးချေရန်</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💸 KBZ Pay:\n<code>{html.escape(KAY_PHONE)}</code>\n\n"
        f"💸 Wave Pay:\n<code>{html.escape(WAVE_PHONE)}</code>\n\n"
        f"👤 Account Name:\n"
        f"<code>{html.escape(ACCOUNT_NAME)}</code>\n\n"
        f"💵 ကျသင့်ငွေ: <b>{MEMBER_PRICE:,} ကျပ်</b>\n"
        "⚠️ Ashita No Joe Series တစ်ခုတည်းအတွက် သီးသန့်ဖြစ်သည်။"
    )


def payment_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "👤 Admin ထံ တိုက်ရိုက်ပေးချေရန်",
            callback_data="pay_direct"
        ),
        types.InlineKeyboardButton(
            "🤖 Bot ထဲသို့ Screenshot ပို့ရန်",
            callback_data="pay_bot"
        )
    )

    bot.send_message(
        chat_id,
        "💳 <b>ငွေပေးချေမှုနည်းလမ်း ရွေးချယ်ပါ။</b>",
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# 15. CALLBACK HANDLER
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id if call.message else user_id
    data = call.data or ""

    if is_banned(user_id) and not is_admin(user_id):
        bot.answer_callback_query(
            call.id,
            "အသုံးပြုခွင့် ပိတ်ထားပါသည်။",
            show_alert=True
        )
        return

    # Channel membership check
    if data == "check_sub":
        if check_user_subscription(user_id):
            bot.answer_callback_query(
                call.id,
                "✅ Channel Join ပြီးပါပြီ!"
            )
            if call.message:
                try:
                    bot.delete_message(chat_id, call.message.message_id)
                except Exception:
                    pass
            show_main_menu(chat_id)
        else:
            bot.answer_callback_query(
                call.id,
                "❌ Channel ကို ဦးစွာ Join ပေးပါ။",
                show_alert=True
            )
        return

    # Admin payment approval / rejection
    if data.startswith(("approve_", "reject_")):
        if not is_admin(user_id):
            bot.answer_callback_query(
                call.id,
                "⛔ Admin Only!",
                show_alert=True
            )
            return

        try:
            action, payment_id_text, target_id_text = data.split("_")
            payment_id = int(payment_id_text)
            target_id = int(target_id_text)
        except (ValueError, IndexError):
            bot.answer_callback_query(
                call.id,
                "Invalid payment information.",
                show_alert=True
            )
            return

        with get_db() as conn:
            payment = conn.execute("""
                SELECT *
                FROM payments
                WHERE payment_id = ?
                  AND user_id = ?
                  AND status = 'pending'
            """, (payment_id, target_id)).fetchone()

            if not payment:
                bot.answer_callback_query(
                    call.id,
                    "ဒီ Payment ကို အရင်က စစ်ဆေးပြီးဖြစ်သည်။",
                    show_alert=True
                )
                return

            new_status = "approved" if action == "approve" else "rejected"

            result = conn.execute("""
                UPDATE payments
                SET status = ?, reviewed_at = ?
                WHERE payment_id = ?
                  AND status = 'pending'
            """, (new_status, current_time(), payment_id))

            if result.rowcount != 1:
                bot.answer_callback_query(
                    call.id,
                    "Payment ကို စစ်ဆေးပြီးပါပြီ။",
                    show_alert=True
                )
                return

            if action == "approve":
                user_row = conn.execute("""
                    SELECT first_name, username
                    FROM users
                    WHERE user_id = ?
                """, (target_id,)).fetchone()

                name = user_row["first_name"] if user_row else "Unknown User"
                username = user_row["username"] if user_row else ""

                conn.execute("""
                    INSERT INTO members
                    (user_id, name, username, approved_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id)
                    DO UPDATE SET
                        name = excluded.name,
                        username = excluded.username,
                        approved_at = excluded.approved_at
                """, (target_id, name, username, current_time()))

        bot.answer_callback_query(
            call.id,
            "အောင်မြင်စွာ ဆောင်ရွက်ပြီးပါပြီ။"
        )

        if action == "approve":
            success_text = (
                "🎉 <b>ဂုဏ်ယူပါတယ်!</b> 👏\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "မိတ်ဆွေသည် Ashita No Joe Series "
                "အတွက် Member ဖြစ်သွားပါပြီ။ 👑\n\n"
                "ဝယ်ယူအားပေးမှုအတွက် "
                "အထူးကျေးဇူးတင်ရှိပါတယ်ခင်ဗျာ။ ✨"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "👑 Premium Channel ထဲသို့ ဝင်ရန်",
                url=PREMIUM_CHANNEL_LINK
            ))

            try:
                bot.send_message(
                    target_id,
                    success_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )
            except Exception:
                logger.exception("Approval notification failed.")

            bot.send_message(
                chat_id,
                f"✅ User <code>{target_id}</code> "
                "အား Member အဖြစ် အတည်ပြုပြီးပါပြီ။",
                parse_mode="HTML"
            )
        else:
            try:
                bot.send_message(
                    target_id,
                    "❌ <b>Payment Rejected</b>\n\n"
                    "တင်ပြလာသော ငွေလွှဲပြေစာကို "
                    "အတည်မပြုနိုင်ပါ။\n\n"
                    "ကျေးဇူးပြု၍ Admin ထံ တိုက်ရိုက် "
                    "ဆက်သွယ်စုံစမ်းပေးပါခင်ဗျာ။ 🙏",
                    parse_mode="HTML"
                )
            except Exception:
                logger.exception("Rejection notification failed.")

            bot.send_message(
                chat_id,
                f"❌ User <code>{target_id}</code> "
                "၏ Payment ကို ပယ်ဖျက်ပြီးပါပြီ။",
                parse_mode="HTML"
            )

        if call.message:
            try:
                bot.edit_message_reply_markup(
                    chat_id,
                    call.message.message_id,
                    reply_markup=None
                )
            except Exception:
                pass
        return

    # Normal user callbacks must be subscribed
    if not is_admin(user_id):
        if not check_user_subscription(user_id):
            bot.answer_callback_query(
                call.id,
                "Channel ကို Join ပေးပါ။",
                show_alert=True
            )
            bot.send_message(
                chat_id,
                "⚠️ Channel Join လုပ်ရန် လိုအပ်ပါသည်။",
                reply_markup=subscription_keyboard()
            )
            return

    if data == "about_joe":
        bot.answer_callback_query(call.id)
        joe_text = (
            "🥊 <b>Ashita No Joe (Tomorrow's Joe)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "ဂန္ထဝင်လက်ဝှေ့ အန်နီမေးရှင်းတစ်ခုဖြစ်ပြီး "
            "လူငယ်ဘဝ၏ ရုန်းကန်လှုပ်ရှားမှုများကို "
            "ဖော်ပြထားသော လက်ရာတစ်ခုဖြစ်ပါတယ်။\n\n"
            "📺 <b>Season Information</b>\n"
            "• Season 1 - 79 Episodes\n"
            "• Season 2 - 47 Episodes\n"
            "• Total - 126 Episodes\n\n"
            "📅 Released: 1970 - 1981\n"
            "⭐ IMDb: 8.2 / 10\n\n"
            f"💰 Member Fee: <b>{MEMBER_PRICE:,} ကျပ်</b>\n"
            "⚠️ Ashita No Joe Series တစ်ခုတည်းအတွက် ဖြစ်သည်။"
        )
        bot.send_message(chat_id, joe_text, parse_mode="HTML")

    elif data == "payment_info":
        bot.answer_callback_query(call.id)
        payment_menu(chat_id)

    elif data == "pay_direct":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            payment_information()
            + "\n\n"
            "📷 ငွေလွှဲပြီးပါက Screenshot နှင့်တကွ "
            "Admin ထံ တိုက်ရိုက်ပေးပို့ပါ။\n\n"
            "Owner: @Nazzpar\n"
            "Admin: @hikarikenn",
            parse_mode="HTML"
        )

    elif data == "pay_bot":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            payment_information()
            + "\n\n"
            "📸 ငွေလွှဲပြီးပါက ပြေစာ Screenshot ကို "
            "ဤ Bot ထဲသို့ ပေးပို့ပေးပါ။\n\n"
            "Admin မှ စစ်ဆေးပြီး ပြန်လည်အကြောင်းကြားပေးပါမည်။",
            parse_mode="HTML"
        )

    elif data == "premium_info":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            "👑 <b>Nasspar's Premium Channel</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "လက်ရှိတွင် Premium Channel ဝန်ဆောင်မှုအသစ်များ "
            "ထွက်ရှိလာပါက ဤ Bot မှတစ်ဆင့် "
            "အကြောင်းကြားပေးသွားပါမည်။ 🌟",
            parse_mode="HTML"
        )
    else:
        bot.answer_callback_query(call.id)


# =========================================================
# 16. PAYMENT SCREENSHOT SYSTEM
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

    name = (
        f"{user.first_name or ''} "
        f"{user.last_name or ''}"
    ).strip()
    username = user.username or ""
    photo_file_id = message.photo[-1].file_id

    try:
        with get_db() as conn:
            existing = conn.execute("""
                SELECT payment_id
                FROM payments
                WHERE screenshot_file_id = ?
            """, (photo_file_id,)).fetchone()

            if existing:
                bot.reply_to(
                    message,
                    "⚠️ ဤ Screenshot ကို ယခင်က ပေးပို့ထားပြီးဖြစ်ပါသည်။"
                )
                return

            cursor = conn.execute("""
                INSERT INTO payments
                (user_id, screenshot_file_id, status, submitted_at)
                VALUES (?, ?, 'pending', ?)
            """, (user_id, photo_file_id, current_time()))

            payment_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        bot.reply_to(
            message,
            "⚠️ ဤ Screenshot ကို ထပ်မံလက်ခံ၍ မရပါ။"
        )
        return
    except Exception:
        logger.exception("Could not save payment record.")
        bot.reply_to(
            message,
            "❌ ပြေစာသိမ်းဆည်းရာတွင် အမှားဖြစ်နေပါသည်။ Admin ကို ဆက်သွယ်ပါ။"
        )
        return

    bot.reply_to(
        message,
        "✅ <b>ငွေလွှဲပြေစာ ပေးပို့ပြီးပါပြီ။</b>\n\n"
        "Admin မှ စစ်ဆေးပြီး ၂၄ နာရီအတွင်း "
        "ပြန်လည်အကြောင်းကြားပေးသွားပါမည်။\n\n"
        "အားပေးမှုအတွက် ကျေးဇူးတင်ရှိပါတယ်။ 🙏",
        parse_mode="HTML"
    )

    log_user_activity(message, "Payment Screenshot ပေးပို့ခြင်း")

    caption_text = (
        "📥 <b>New Payment Screenshot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: {html.escape(name)}\n"
        f"🔗 Username: "
        f"{html.escape('@' + username if username else 'None')}\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"🧾 Payment ID: <code>{payment_id}</code>\n"
        "⏳ Status: Pending\n"
        f"🕒 Time: {current_time()}"
    )

    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve_{payment_id}_{user_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{payment_id}_{user_id}"
        )
    )

    try:
        bot.send_photo(
            CREATOR_ID,
            photo_file_id,
            caption=caption_text,
            parse_mode="HTML",
            reply_markup=admin_markup
        )
    except Exception:
        logger.exception("Could not send payment screenshot to Creator.")
        bot.send_message(
            user_id,
            "⚠️ Admin ထံ Screenshot ပို့ရာတွင် အခက်အခဲရှိနေပါသည်။ "
            "ကျေးဇူးပြု၍ @Nazzpar သို့ ဆက်သွယ်ပေးပါ။"
        )


# =========================================================
# 17. AI SYSTEM PROMPT AND CHAT MEMORY
# =========================================================

SYSTEM_PROMPT = f"""
သင်သည် Nasspar's Bot ၏ AI Assistant ဖြစ်သည်။

သင်သည် Telegram Channel {CHANNEL_USERNAME}
နှင့် ဆက်စပ်သော Ashita No Joe Series အတွက်
အသုံးပြုသူများကို ကူညီဖြေကြားပေးရမည်။

အဓိက အချက်အလက်များ:
1. Series: Ashita No Joe (Tomorrow's Joe)
2. Season 1: 79 Episodes
3. Season 2: 47 Episodes
4. Total: 126 Episodes
5. IMDb: 8.2/10
6. Released: 1970 - 1981
7. Member Fee: 5,000 MMK
8. Payment: KBZ Pay / Wave Pay
9. Account Name: {ACCOUNT_NAME}
10. KBZ Pay: {KAY_PHONE}
11. Wave Pay: {WAVE_PHONE}

Admin:
- @Nazzpar
- @hikarikenn

စည်းမျဉ်းများ:
- မြန်မာဘာသာဖြင့် သဘာဝကျကျ ဖြေကြားပါ။
- ဖော်ရွေပြီး ယဉ်ကျေးသော စကားပြောပုံကို အသုံးပြုပါ။
- မသိသောအချက်အလက်များကို မဖန်တီးပါနှင့်။
- Payment အတည်ပြုပြီးပြီဟု ကိုယ်တိုင် မကြေညာပါနှင့်။
- Payment Screenshot ကို Admin ကသာ အတည်ပြုနိုင်သည်။
- ယခင်စကားဝိုင်းကို Chat History မှ အသုံးပြုပါ။
- မသေချာသော ကိစ္စများကို Admin ထံ ဆက်သွယ်ရန် ညွှန်ကြားပါ။
- User ကို အခြားမေးခွန်းများ မေးမြန်းခွင့်လည်း ပေးပါ။
"""


def get_chat_history(user_id):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT role, content
            FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, MAX_HISTORY_MESSAGES)).fetchall()

    return [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]


def save_chat_history(user_id, role, content):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_history
            (user_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, current_time()))

        conn.execute("""
            DELETE FROM chat_history
            WHERE user_id = ?
              AND id NOT IN (
                  SELECT id
                  FROM chat_history
                  WHERE user_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
        """, (user_id, user_id, MAX_HISTORY_MESSAGES))


def clear_chat_history(user_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ?",
            (user_id,)
        )


# =========================================================
# 18. COMMAND: CLEAR MEMORY
# =========================================================

@bot.message_handler(commands=["clear"])
def clear_memory(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        return

    if not require_subscription(message):
        return

    clear_chat_history(user_id)

    bot.reply_to(
        message,
        "🧠 Conversation Memory ကို ရှင်းလင်းပြီးပါပြီ။\n"
        "ယခုမှစပြီး စကားဝိုင်းအသစ်အဖြစ် စတင်နိုင်ပါတယ်။"
    )


# =========================================================
# 19. GROQ AI CHAT HANDLER
# =========================================================

@bot.message_handler(
    func=lambda message: True,
    content_types=["text"]
)
def handle_groq_chat(message):
    user_id = message.from_user.id
    user_text = (message.text or "").strip()

    if not user_text:
        return

    if is_banned(user_id):
        return

    if not require_subscription(message):
        return

    if not groq_client:
        send_ai_fallback(message)
        return

    try:
        history = get_chat_history(user_id)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=700,
            timeout=30
        )

        ai_reply = (
            completion.choices[0].message.content
            or "တောင်းပန်ပါတယ်။ အဖြေထုတ်မပေးနိုင်သေးပါ။"
        )

        save_chat_history(user_id, "user", user_text)
        save_chat_history(user_id, "assistant", ai_reply)

        final_reply = (
            "🤖 Nasspar's Bot AI Assistant\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{ai_reply}"
        )

        send_long_message(
            message.chat.id,
            final_reply,
            reply_to=message
        )

    except Exception:
        logger.exception("Groq API Error")
        send_ai_fallback(message)


# =========================================================
# 20. START BOT
# =========================================================

if __name__ == "__main__":
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Nasspar's Bot is starting...")
    logger.info(
        "AI Assistant: %s",
        "Enabled" if groq_client else "Disabled"
    )
    logger.info("SQLite Database: Enabled")
    logger.info("Payment System: Enabled")
    logger.info("Admin Security: Enabled")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        # Webhook ကိုဖယ်ရှားပြီး polling စတင်မည်။
        # skip_pending_updates argument မသုံးထားသဖြင့်
        # pyTelegramBotAPI version ကွာခြားမှုကြောင့် error မတက်စေပါ။
        bot.remove_webhook()

        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")

    except Exception:
        logger.exception("Bot polling stopped unexpectedly.")
