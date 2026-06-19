import telebot
from telebot import types
import sqlite3
import threading
import time
import datetime
import random
import shutil
import os
import io
import requests
import json
import re
import subprocess
import tempfile

# ========== استيراد المكتبات الاختيارية ==========
try:
    from gtts import gTTS
except:
    print("⚠️ gtts غير مثبتة")

try:
    from googletrans import Translator
    translator = Translator()
except:
    translator = None
    print("⚠️ googletrans غير مثبتة")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False
    print("⚠️ Pillow غير مثبتة")

try:
    import yt_dlp
except:
    print("⚠️ yt-dlp غير مثبتة")

try:
    import google.generativeai as genai
    GEMINI_API_KEY = ""  # ضع مفتاحك هنا
    model = genai.GenerativeModel('gemini-pro') if GEMINI_API_KEY else None
except:
    model = None
    print("⚠️ google-generativeai غير مثبتة")

# ===================================================================
# 🔧 إعدادات البوت
# ===================================================================
TOKEN = "8734066588:AAFDQf29RiDD2z07iBK8ryWWtO9EVMEuKuo"
ADMIN_ID = 8803139060
CONTACT_USERNAME = "xziiro"

bot = telebot.TeleBot(TOKEN)

# ===================================================================
# قاعدة البيانات
# ===================================================================
conn = sqlite3.connect("data.db", check_same_thread=False)

# إنشاء الجداول
conn.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    last_daily TEXT,
    joined_date TEXT,
    is_verified INTEGER DEFAULT 0
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    description TEXT,
    category TEXT DEFAULT 'عام',
    discount INTEGER DEFAULT 0,
    stock INTEGER DEFAULT 5
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS referrals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    date TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS transfers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user INTEGER,
    to_user INTEGER,
    amount INTEGER,
    date TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS coupons(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    discount INTEGER,
    used_by TEXT DEFAULT '',
    is_used INTEGER DEFAULT 0,
    created_at TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS bots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    token TEXT,
    status TEXT DEFAULT 'stopped',
    created_at TEXT,
    bot_type TEXT DEFAULT 'default'
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS bot_tokens(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    token TEXT,
    bot_name TEXT,
    created_at TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS scheduled_posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT,
    text TEXT,
    send_time TEXT,
    is_sent INTEGER DEFAULT 0
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS proxies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    port TEXT,
    country TEXT DEFAULT 'غير معروف'
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS store_settings(
    key TEXT PRIMARY KEY,
    value TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS shortened_links(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT,
    short_code TEXT,
    user_id INTEGER,
    created_at TEXT,
    clicks INTEGER DEFAULT 0
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS bot_stats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT,
    new_users INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    sessions INTEGER DEFAULT 0
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS linked_bots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    main_bot_id INTEGER,
    linked_bot_token TEXT,
    linked_bot_name TEXT,
    created_at TEXT
)""")

conn.execute("""CREATE TABLE IF NOT EXISTS daily_gifts_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    gift_date TEXT,
    amount INTEGER
)""")

# إضافة بروكسيات افتراضية
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM proxies")
if c.fetchone()[0] == 0:
    proxies = [
        ("192.168.1.1", "8080", "محلي"),
        ("8.8.8.8", "3128", "USA"),
        ("1.1.1.1", "80", "USA"),
        ("203.0.113.1", "9999", "UK"),
    ]
    for proxy in proxies:
        c.execute("INSERT INTO proxies (ip, port, country) VALUES (?, ?, ?)", proxy)
    conn.commit()
c.close()

# إعدادات المتجر الافتراضية
c = conn.cursor()
c.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('display_mode', 'كلاسيكي')")
c.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('verify_fake', 'تفعيل')")
c.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('shorten_api', 'isgd')")
c.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('show_daily_discounts', 'تفعيل')")
c.execute("INSERT OR IGNORE INTO store_settings (key, value) VALUES ('product_stock_display', 'تفعيل')")
conn.commit()
c.close()

# إضافة منتجات افتراضية
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM products")
if c.fetchone()[0] == 0:
    products = [
        ("🎁 كود خصم 50%", 100, "كود خصم فعال لمتجرك", "كوبونات", 10, 10),
        ("📱 حساب مميز", 500, "حساب مع مزايا حصرية", "حسابات", 20, 5),
        ("🌟 عضوية VIP", 1000, "عضوية مدى الحياة", "عضوية", 0, 3),
        ("💰 1000 نقطة إضافية", 200, "أضف نقاط لحسابك", "نقاط", 5, 20),
        ("🎮 حساب ببجي موقف", 150, "حساب ببجي مع skins نادرة", "حسابات", 15, 4),
        ("📷 حساب انستقرام مميز", 300, "حساب انستقرام مع متابعين", "حسابات", 10, 3),
        ("🎵 اشتراك سبوتيفاي", 80, "اشتراك سبوتيفاي بريميوم لمدة شهر", "عضوية", 0, 8),
        ("📺 اشتراك نتفلكس", 120, "اشتراك نتفلكس لمدة شهر", "عضوية", 5, 6),
    ]
    for product in products:
        c.execute(
            "INSERT INTO products (name, price, description, category, discount, stock) VALUES (?, ?, ?, ?, ?, ?)",
            product
        )
    conn.commit()
c.close()

# ========== إعدادات افتراضية ==========
def init_settings():
    c = conn.cursor()
    settings = {
        "entry_points": "2",
        "daily_gift": "10",
        "transfer_commission": "0",
        "points_word": "نقطة",
        "referral_reward": "10",
        "referred_reward": "5",
        "proof_channel": "",
        "bot_profile_photo": ""
    }
    for key, value in settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    c.close()

init_settings()

# ===================================================================
# دوال مساعدة
# ===================================================================
def get_setting(key):
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    result = c.fetchone()
    c.close()
    return result[0] if result else None

def set_setting(key, value):
    c = conn.cursor()
    c.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    conn.commit()
    c.close()

def get_store_setting(key):
    c = conn.cursor()
    c.execute("SELECT value FROM store_settings WHERE key=?", (key,))
    result = c.fetchone()
    c.close()
    return result[0] if result else None

def set_store_setting(key, value):
    c = conn.cursor()
    c.execute("UPDATE store_settings SET value=? WHERE key=?", (value, key))
    conn.commit()
    c.close()

def get_user_points(user_id):
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    c.close()
    return result[0] if result else 0

def add_points(user_id, amount):
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.close()

def remove_points(user_id, amount):
    c = conn.cursor()
    c.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.close()

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_referral_link(user_id):
    bot_username = bot.get_me().username
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

def get_referral_count(user_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    result = c.fetchone()
    c.close()
    return result[0] if result else 0

def generate_coupon_code():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ===================================================================
# ميزة رفع وتشغيل بايثون (للمدير فقط)
# ===================================================================
FORBIDDEN_KEYWORDS = [
    "os.system", "subprocess", "eval", "exec", "__import__",
    "open(", "file(", "input(", "raw_input", "compile",
    "globals", "locals", "getattr", "setattr", "delattr"
]

def check_code_safety(code):
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in code:
            return False, f"❌ الكود يحتوي على كلمة ممنوعة: `{keyword}`"
    return True, "✅ الكود آمن"

@bot.message_handler(func=lambda m: m.text == "🐍 رفع وتشغيل بايثون")
def run_python_file(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "❌ هذه الخاصية للمدير فقط!")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(
        chat_id,
        "🐍 **رفع وتشغيل ملف بايثون**\n\n📤 أرسل ملف `.py` وسيتم تشغيله وعرض النتيجة.\n\n⚠️ **تنبيه:** هذه الخاصية خطيرة، استخدمها بحذر!",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['document'])
def handle_python_file(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "❌ هذه الخاصية للمدير فقط!")
        return
    if not message.document or not message.document.file_name.endswith('.py'):
        bot.send_message(chat_id, "❌ يرجى إرسال ملف بايثون بصيغة `.py`!")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        code = downloaded_file.decode('utf-8')
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ في تحميل الملف: {str(e)}")
        return
    is_safe, msg = check_code_safety(code)
    if not is_safe:
        bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, message.document.file_name)
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        bot.send_message(chat_id, "⏳ جاري تشغيل الملف...")
        result = subprocess.run(
            ['python3', temp_file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        output = result.stdout.strip() or "⚠️ لا يوجد مخرجات."
        error = result.stderr.strip()
        response = f"✅ **تم التشغيل بنجاح!**\n\n📤 **المخرجات:**\n```\n{output}\n```"
        if error:
            response += f"\n\n⚠️ **الأخطاء:**\n```\n{error}\n```"
        if len(response) > 4000:
            for part in [response[i:i+4000] for i in range(0, len(response), 4000)]:
                bot.send_message(chat_id, part, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, response, parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        bot.send_message(chat_id, "⏰ انتهى وقت التشغيل (أكثر من 60 ثانية)")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء التشغيل: {str(e)}")

# ===================================================================
# تعيين صورة الملف الشخصي للبوت (للمدير فقط)
# ===================================================================
@bot.message_handler(func=lambda m: m.text == "🖼 تعيين صورة البوت")
def set_bot_photo(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "❌ هذه الخاصية للمدير فقط!")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(
        chat_id,
        "🖼 **تعيين صورة الملف الشخصي للبوت**\n\n📤 أرسل صورة جديدة لتصبح صورة البوت الشخصية.\n\n⚠️ يجب أن تكون الصورة بصيغة JPEG أو PNG وبحجم أقل من 5 ميجابايت.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['photo'])
def handle_bot_photo(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "❌ هذه الخاصية للمدير فقط!")
        return
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        temp_path = f"temp_bot_photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        with open(temp_path, 'wb') as f:
            f.write(downloaded_file)
        
        with open(temp_path, 'rb') as f:
            bot.set_my_photo(f)
        
        os.remove(temp_path)
        set_setting("bot_profile_photo", file_id)
        bot.send_message(chat_id, "✅ **تم تعيين الصورة الجديدة للبوت بنجاح!**", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")

# ===================================================================
# القائمة الرئيسية
# ===================================================================
def main_menu(chat_id, message_id=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🎵 بوت صوتي"),
        types.KeyboardButton("🤖 صانع البوتات")
    )
    kb.add(
        types.KeyboardButton("📢 إدارة قناة"),
        types.KeyboardButton("🛍 المتجر")
    )
    kb.add(
        types.KeyboardButton("🎨 إنشاء لوجو"),
        types.KeyboardButton("📝 منشورات")
    )
    kb.add(
        types.KeyboardButton("🌐 بروكسي"),
        types.KeyboardButton("🌍 ترجمة")
    )
    kb.add(
        types.KeyboardButton("👥 زيادة أعضاء"),
        types.KeyboardButton("📥 تحميل")
    )
    kb.add(
        types.KeyboardButton("💻 سايت"),
        types.KeyboardButton("🧠 ذكاء اصطناعي")
    )
    kb.add(
        types.KeyboardButton("📋 عرض جميع البوتات"),
        types.KeyboardButton("💳 نقاطي")
    )
    kb.add(
        types.KeyboardButton("📊 معلومات حسابي")
    )
    if is_admin(chat_id):
        kb.add(types.KeyboardButton("⚙️ لوحة التحكم"))
        kb.add(types.KeyboardButton("🐍 رفع وتشغيل بايثون"))
        kb.add(types.KeyboardButton("🖼 تعيين صورة البوت"))
    points = get_user_points(chat_id)
    points_word = get_setting("points_word")
    text = f"""🌟 **RAVIYA IS BACK** 🌟

مرحباً بك في عالم التسوق المثير، عزيزي
RAVIYA IS BACK 😍😍😍

هنا، يمكنك أن تدخل في رحلة لاكتساب النقاط
واستبدالها بعروض خلاية! 😍😍😍

استعرض الأقسام المتاحة واختر ما يروق لك
لتبدأ مغامرتك التسوقية الآن من الكيبورد أدناه
استمتع! 😍😍😍

عجبك البوت؟ اصنع بوتك الخاص مجانا!
@xziiro

---

**العروض التي يقدمها البوت**

- رصيد حسابك: {points} {points_word}
- تحويل أموال
- معلومات حسابك"""
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

# ===================================================================
# /start
# ===================================================================
@bot.message_handler(commands=['start'])
def start(message):
    try:
        if len(message.text.split()) > 1:
            payload = message.text.split()[1]
            if payload.startswith("ref_"):
                referrer_id = int(payload.split("_")[1])
                if referrer_id != message.from_user.id:
                    c = conn.cursor()
                    c.execute("SELECT user_id FROM users WHERE user_id=?", (message.from_user.id,))
                    exists = c.fetchone()
                    c.close()
                    if not exists:
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)",
                            (referrer_id, message.from_user.id, str(datetime.datetime.now()))
                        )
                        conn.commit()
                        c.close()
                        reward = int(get_setting("referral_reward") or 10)
                        add_points(referrer_id, reward)
                        referred_reward = int(get_setting("referred_reward") or 5)
                        add_points(message.from_user.id, referred_reward)
                        try:
                            bot.send_message(referrer_id, f"🎉 تم دعوة مستخدم جديد عبر رابطك!\nلقد ربحت {reward} {get_setting('points_word')}.")
                        except:
                            pass
                        bot.send_message(message.chat.id, f"🎉 مرحباً بك! لقد تمت دعوتك بواسطة مستخدم آخر.\nلقد حصلت على {referred_reward} {get_setting('points_word')} كمكافأة ترحيبية!")
                    else:
                        bot.send_message(message.chat.id, "⚠️ أنت مسجل بالفعل، لا يمكن استخدام رابط الدعوة.")
                else:
                    bot.send_message(message.chat.id, "❌ لا يمكنك دعوة نفسك!")
            elif payload.startswith("gift_"):
                amount = int(payload.split("_")[1])
                add_points(message.from_user.id, amount)
                bot.send_message(message.chat.id, f"🎁 لقد حصلت على {amount} نقطة من رابط الهدية!")
            elif payload.startswith("fund_"):
                amount = int(payload.split("_")[1])
                add_points(message.from_user.id, amount)
                bot.send_message(message.chat.id, f"💰 تم إضافة {amount} نقطة إلى رصيدك عبر رابط التمويل!")
            elif payload.startswith("coupon_"):
                code = payload.split("_")[1]
                apply_coupon(message.from_user.id, code)
    except:
        pass
    try:
        entry_points = int(get_setting("entry_points") or 2)
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, points, joined_date) VALUES (?, ?, ?, ?)",
            (message.from_user.id, message.from_user.username, entry_points, str(datetime.datetime.now()))
        )
        conn.commit()
        c.close()
    except:
        pass
    main_menu(message.chat.id)

# ===================================================================
# المتجر
# ===================================================================
@bot.message_handler(func=lambda m: m.text == "🛍 المتجر")
def shop_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📦 جميع السلع", callback_data="all_products"),
        types.InlineKeyboardButton("📂 أقسام المتجر", callback_data="shop_categories"),
        types.InlineKeyboardButton("🎁 الهدية اليومية", callback_data="daily_gift"),
        types.InlineKeyboardButton("💸 تحويل نقاط", callback_data="transfer_points"),
        types.InlineKeyboardButton("🏷 كودات الخصم", callback_data="coupons_menu")
    )
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, "🛍 **المتجر**\n\nاختر ما تريد فعله:", reply_markup=kb, parse_mode="Markdown")

# ===================================================================
# كودات الخصم
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "coupons_menu")
def coupons_menu_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    kb = types.InlineKeyboardMarkup(row_width=2)
    if is_admin(chat_id):
        kb.add(
            types.InlineKeyboardButton("➕ إنشاء كود خصم", callback_data="create_coupon"),
            types.InlineKeyboardButton("📋 جميع الأكواد", callback_data="list_coupons")
        )
    kb.add(
        types.InlineKeyboardButton("🎫 استخدام كود", callback_data="use_coupon"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_shop")
    )
    bot.edit_message_text("🏷 **كودات الخصم**\n\nيمكنك إنشاء واستخدام أكواد الخصم للحصول على تخفيضات!", chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "create_coupon")
def create_coupon_callback(call):
    chat_id = call.message.chat.id
    if not is_admin(chat_id):
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمدير فقط!")
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, "🏷 **إنشاء كود خصم**\n\nأرسل نسبة الخصم (1-100):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_coupon_discount)

def get_coupon_discount(message):
    try:
        discount = int(message.text.strip())
        if discount < 1 or discount > 100:
            bot.send_message(message.chat.id, "❌ النسبة يجب أن تكون بين 1 و 100!")
            return
        code = generate_coupon_code()
        c = conn.cursor()
        c.execute(
            "INSERT INTO coupons (code, discount, created_at) VALUES (?, ?, ?)",
            (code, discount, str(datetime.datetime.now()))
        )
        conn.commit()
        c.close()
        bot.send_message(
            message.chat.id,
            f"✅ **تم إنشاء كود الخصم!**\n\n🎫 الكود: `{code}`\n🏷 الخصم: {discount}%\n\nشارك الكود مع المستخدمين ليستفيدوا!",
            parse_mode="Markdown"
        )
    except:
        bot.send_message(message.chat.id, "❌ يرجى إرسال رقم صحيح!")

@bot.callback_query_handler(func=lambda c: c.data == "list_coupons")
def list_coupons_callback(call):
    chat_id = call.message.chat.id
    if not is_admin(chat_id):
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمدير فقط!")
        return
    c = conn.cursor()
    c.execute("SELECT code, discount, is_used, used_by FROM coupons ORDER BY id DESC LIMIT 20")
    coupons = c.fetchall()
    c.close()
    if not coupons:
        bot.edit_message_text("📋 **كودات الخصم**\n\nلا توجد أكواد خصم حالياً.", chat_id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    text = "📋 **كودات الخصم**\n\n"
    for code, discount, is_used, used_by in coupons:
        status = "✅ مستخدم" if is_used else "🟢 متاح"
        text += f"🎫 `{code}` - {discount}% - {status}"
        if is_used and used_by:
            text += f" (استخدمه: {used_by})"
        text += "\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="coupons_menu"))
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "use_coupon")
def use_coupon_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, "🎫 **استخدام كود خصم**\n\nأرسل الكود الذي تريد استخدامه:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, apply_coupon_step)

def apply_coupon_step(message):
    code = message.text.strip().upper()
    apply_coupon(message.from_user.id, code)

def apply_coupon(user_id, code):
    c = conn.cursor()
    c.execute("SELECT id, discount, is_used FROM coupons WHERE code=? AND is_used=0", (code,))
    coupon = c.fetchone()
    if not coupon:
        bot.send_message(user_id, f"❌ الكود `{code}` غير صحيح أو مستخدم بالفعل!", parse_mode="Markdown")
        c.close()
        return
    coupon_id, discount, is_used = coupon
    points = get_user_points(user_id)
    bonus = int(points * discount / 100)
    add_points(user_id, bonus)
    c.execute("UPDATE coupons SET is_used=1, used_by=? WHERE id=?", (str(user_id), coupon_id))
    conn.commit()
    c.close()
    bot.send_message(
        user_id,
        f"✅ **تم استخدام الكود بنجاح!**\n\n🎫 الكود: `{code}`\n🏷 الخصم: {discount}%\n💰 النقاط المضافة: {bonus} نقطة\n💳 رصيدك الآن: {get_user_points(user_id)} نقطة",
        parse_mode="Markdown"
    )

# ===================================================================
# عرض جميع السلع
# ===================================================================
@bot.message_handler(func=lambda m: m.text == "📦 جميع السلع")
def all_products_button(message):
    show_all_products(message.chat.id, None)

def show_all_products(chat_id, message_id):
    c = conn.cursor()
    c.execute("SELECT id, name, price, description, category, discount, stock FROM products")
    products = c.fetchall()
    c.close()
    display_mode = get_store_setting("display_mode") or "كلاسيكي"
    show_stock = get_store_setting("product_stock_display") == "تفعيل"
    show_discounts = get_store_setting("show_daily_discounts") == "تفعيل"
    
    if not products:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        text = "📦 **جميع السلع**\n\nلا توجد منتجات حالياً."
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")
        return
    
    text = "📦 **جميع السلع**\n"
    if show_stock:
        text += f"📊 كمية السلع المتوفرة: {len([p for p in products if p[6] > 0])}\n"
    if show_discounts:
        discounted = [p for p in products if p[5] > 0]
        if discounted:
            text += f"🔥 تخفيضات اليوم: {len(discounted)} سلعة مخفضة\n"
    text += f"🔄 طريقة العرض: {display_mode}\n\n"
    
    points_word = get_setting("points_word")
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    for product in products:
        product_id, name, price, description, category, discount, stock = product
        stock_text = f"📦 {stock}" if show_stock else ""
        if discount > 0:
            new_price = price - (price * discount // 100)
            price_text = f"~~{price}~~ {new_price} {points_word} (خصم {discount}%)"
        else:
            price_text = f"{price} {points_word}"
        text += f"🆔 {product_id}\n📌 {name}\n💰 {price_text}\n📂 {category}\n📝 {description}\n{stock_text}\n\n"
        if stock > 0:
            kb.add(types.InlineKeyboardButton(f"شراء {name[:10]}", callback_data=f"buy_{product_id}"))
    
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

# ===================================================================
# أقسام المتجر
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "shop_categories")
def shop_categories_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM products")
    categories = c.fetchall()
    c.close()
    kb = types.InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        kb.add(types.InlineKeyboardButton(f"📂 {cat[0]}", callback_data=f"cat_{cat[0]}"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.edit_message_text("📂 **أقسام المتجر**\n\nاختر قسماً لعرض منتجاته:", chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat_"))
def category_products_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    category = call.data.split("_")[1]
    c = conn.cursor()
    c.execute("SELECT id, name, price, description, discount, stock FROM products WHERE category=?", (category,))
    products = c.fetchall()
    c.close()
    if not products:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="shop_categories"))
        bot.edit_message_text(f"📂 **{category}**\n\nلا توجد منتجات في هذا القسم.", chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    text = f"📂 **{category}**\n\n"
    points_word = get_setting("points_word")
    kb = types.InlineKeyboardMarkup(row_width=2)
    for product in products:
        product_id, name, price, description, discount, stock = product
        if discount > 0:
            new_price = price - (price * discount // 100)
            price_text = f"~~{price}~~ {new_price} {points_word} (خصم {discount}%)"
        else:
            price_text = f"{price} {points_word}"
        text += f"🆔 {product_id}\n📌 {name}\n💰 {price_text}\n📝 {description}\n📦 {stock}\n\n"
        if stock > 0:
            kb.add(types.InlineKeyboardButton(f"شراء {name[:10]}", callback_data=f"buy_{product_id}"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="shop_categories"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# ===================================================================
# شراء منتج
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_product_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    try:
        product_id = int(call.data.split("_")[1])
        c = conn.cursor()
        c.execute("SELECT name, price, discount, stock FROM products WHERE id=?", (product_id,))
        product = c.fetchone()
        c.close()
        if not product:
            bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
            return
        name, price, discount, stock = product
        if stock <= 0:
            bot.answer_callback_query(call.id, "❌ المنتج غير متوفر!")
            return
        final_price = price - (price * discount // 100) if discount > 0 else price
        points = get_user_points(chat_id)
        points_word = get_setting("points_word")
        if points < final_price:
            bot.answer_callback_query(call.id, f"❌ نقاطك غير كافية! لديك {points} {points_word}")
            return
        verify_fake = get_store_setting("verify_fake") == "تفعيل"
        if verify_fake:
            c = conn.cursor()
            c.execute("SELECT is_verified FROM users WHERE user_id=?", (chat_id,))
            user = c.fetchone()
            c.close()
            if not user or user[0] == 0:
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("✅ تأكيد الشراء", callback_data=f"confirm_buy_{product_id}"))
                kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="back_shop"))
                bot.edit_message_text(
                    f"⚠️ **تحقق من الوهمي**\n\nأنت بحاجة لتأكيد أنك لست حساباً وهمياً قبل الشراء.\nالمنتج: {name}\nالسعر: {final_price} {points_word}",
                    chat_id,
                    message_id,
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
                bot.answer_callback_query(call.id)
                return
        complete_purchase(chat_id, message_id, product_id, name, final_price)
        bot.answer_callback_query(call.id, "✅ تم الشراء بنجاح!")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ حدث خطأ: {str(e)}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_buy_"))
def confirm_buy_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    product_id = int(call.data.split("_")[2])
    c = conn.cursor()
    c.execute("SELECT name, price, discount, stock FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    c.close()
    if not product:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
        return
    name, price, discount, stock = product
    final_price = price - (price * discount // 100) if discount > 0 else price
    points = get_user_points(chat_id)
    if points < final_price:
        bot.answer_callback_query(call.id, "❌ نقاطك غير كافية!")
        return
    c = conn.cursor()
    c.execute("UPDATE users SET is_verified=1 WHERE user_id=?", (chat_id,))
    conn.commit()
    c.close()
    complete_purchase(chat_id, message_id, product_id, name, final_price)
    bot.answer_callback_query(call.id, "✅ تم التحقق والشراء بنجاح!")

def complete_purchase(chat_id, message_id, product_id, name, final_price):
    remove_points(chat_id, final_price)
    c = conn.cursor()
    c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (product_id,))
    conn.commit()
    c.close()
    bot.edit_message_text(
        f"✅ **تم الشراء بنجاح!**\n\n🛍 المنتج: {name}\n💰 السعر: {final_price} {get_setting('points_word')}\n💳 المتبقي: {get_user_points(chat_id)} {get_setting('points_word')}",
        chat_id,
        message_id,
        parse_mode="Markdown"
    )

# ===================================================================
# الهدية اليومية
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "daily_gift")
def daily_gift_callback(call):
    chat_id = call.message.chat.id
    today = str(datetime.datetime.now().date())
    c = conn.cursor()
    c.execute("SELECT last_daily FROM users WHERE user_id=?", (chat_id,))
    result = c.fetchone()
    c.close()
    if result and result[0] == today:
        bot.send_message(chat_id, "❌ لقد حصلت على الهدية اليومية بالفعل!")
        bot.answer_callback_query(call.id)
        return
    gift_amount = int(get_setting("daily_gift") or 10)
    add_points(chat_id, gift_amount)
    points_word = get_setting("points_word")
    c = conn.cursor()
    c.execute("UPDATE users SET last_daily=? WHERE user_id=?", (today, chat_id))
    c.execute("INSERT INTO daily_gifts_log (user_id, gift_date, amount) VALUES (?, ?, ?)",
              (chat_id, today, gift_amount))
    conn.commit()
    c.close()
    bot.send_message(
        chat_id,
        f"🎁 **الهدية اليومية**\n\nلقد حصلت على {gift_amount} {points_word}!\n💳 رصيدك الآن: {get_user_points(chat_id)} {points_word}",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# ===================================================================
# تحويل نقاط
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "transfer_points")
def transfer_points_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "💸 **تحويل نقاط**\n\n📝 أرسل معرف المستخدم (ID) ثم المبلغ\nمثال: `123456789 50`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_transfer)

def process_transfer(message):
    try:
        parts = message.text.split()
        to_user = int(parts[0])
        amount = int(parts[1])
        points_word = get_setting("points_word")
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ المبلغ يجب أن يكون أكبر من 0")
            return
        commission = int(get_setting("transfer_commission") or 0)
        total = amount + (amount * commission // 100)
        sender_points = get_user_points(message.from_user.id)
        if sender_points < total:
            bot.send_message(message.chat.id, f"❌ نقاطك غير كافية!\nلديك: {sender_points} {points_word}\nالمطلوب: {total} {points_word}")
            return
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE user_id=?", (to_user,))
        exists = c.fetchone()
        c.close()
        if not exists:
            bot.send_message(message.chat.id, "❌ المستخدم غير موجود")
            return
        remove_points(message.from_user.id, total)
        add_points(to_user, amount)
        c = conn.cursor()
        c.execute(
            "INSERT INTO transfers (from_user, to_user, amount, date) VALUES (?, ?, ?, ?)",
            (message.from_user.id, to_user, amount, str(datetime.datetime.now()))
        )
        conn.commit()
        c.close()
        bot.send_message(
            message.chat.id,
            f"✅ **تم التحويل بنجاح!**\n\n👤 إلى: `{to_user}`\n💰 المبلغ: {amount} {points_word}\n💳 المتبقي: {get_user_points(message.from_user.id)} {points_word}",
            parse_mode="Markdown"
        )
        try:
            bot.send_message(to_user, f"🎉 لقد استلمت {amount} {points_word} من @{message.from_user.username or message.from_user.id}")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ صيغة غير صحيحة!\nأرسل: `ايدي_المستخدم المبلغ`")

# ===================================================================
# صانع البوتات
# ===================================================================
@bot.message_handler(func=lambda m: m.text == "🤖 صانع البوتات")
def bot_maker(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ إنشاء بوت جديد", callback_data="create_bot"),
        types.InlineKeyboardButton("📋 بوتاتي", callback_data="my_bots"),
        types.InlineKeyboardButton("🔗 ربط بوت بنقاطي", callback_data="link_bot_points")
    )
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(
        message.chat.id,
        "🤖 **صانع البوتات**\n\n📝 أرسل توكن البوت لإنشائه.\n\n💰 سعر الإنشاء: 100 نقطة\n\nكيف تحصل على التوكن؟\n1️⃣ اذهب إلى @BotFather\n2️⃣ أرسل /newbot\n3️⃣ اختر اسم البوت\n4️⃣ اختر معرف البوت\n5️⃣ انسخ التوكن وأرسله هنا",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "create_bot")
def create_bot_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "🤖 **إنشاء بوت جديد**\n\n📝 أرسل توكن البوت:\n\n💰 سعر الإنشاء: 100 نقطة",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_bot_token)

def save_bot_token(message):
    try:
        token = message.text.strip()
        if not token:
            bot.send_message(message.chat.id, "❌ يرجى إرسال توكن صحيح!")
            return
        try:
            test_bot = telebot.TeleBot(token)
            bot_info = test_bot.get_me()
            bot_name = bot_info.username
        except:
            bot.send_message(message.chat.id, "❌ توكن غير صحيح!")
            return
        bot_price = 100
        points = get_user_points(message.from_user.id)
        if points < bot_price:
            bot.send_message(message.chat.id, f"❌ نقاطك غير كافية!\nلديك: {points} نقطة\nتحتاج: {bot_price} نقطة")
            return
        remove_points(message.from_user.id, bot_price)
        c = conn.cursor()
        c.execute(
            "INSERT INTO bots (user_id, username, token, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, bot_name, token, "stopped", str(datetime.datetime.now()))
        )
        conn.commit()
        c.close()
        bot.send_message(
            message.chat.id,
            f"✅ **تم إنشاء البوت بنجاح!**\n\n🤖 معرف البوت: @{bot_name}\n💳 تم خصم {bot_price} نقطة\n\nاستخدم 📋 بوتاتي لعرض بوتاتك.",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

# ===================================================================
# ربط نقاط البوت مع بوت ثاني
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "link_bot_points")
def link_bot_points_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "🔗 **ربط نقاط البوت مع بوت ثاني**\n\n📝 أرسل توكن البوت الثاني الذي تريد ربطه:\n\n📌 سيتم ربط نقاط البوتين معاً ليتمكن المستخدمون من استخدام نقاطهم في كلا البوتين.",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, link_bot_points_step)

def link_bot_points_step(message):
    token = message.text.strip()
    try:
        test_bot = telebot.TeleBot(token)
        bot_info = test_bot.get_me()
        bot_name = bot_info.username
        c = conn.cursor()
        c.execute(
            "INSERT INTO linked_bots (main_bot_id, linked_bot_token, linked_bot_name, created_at) VALUES (?, ?, ?, ?)",
            (ADMIN_ID, token, bot_name, str(datetime.datetime.now()))
        )
        conn.commit()
        c.close()
        bot.send_message(
            message.chat.id,
            f"✅ **تم ربط البوت بنجاح!**\n\n🔗 البوت المرتبط: @{bot_name}\n💳 سيتم مشاركة النقاط بين البوتين.",
            parse_mode="Markdown"
        )
    except:
        bot.send_message(message.chat.id, "❌ توكن غير صحيح!")

# ===================================================================
# بوتاتي
# ===================================================================
@bot.callback_query_handler(func=lambda c: c.data == "my_bots")
def my_bots_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    show_my_bots(chat_id, message_id)
    bot.answer_callback_query(call.id)

def show_my_bots(chat_id, message_id):
    c = conn.cursor()
    c.execute("SELECT id, username, status FROM bots WHERE user_id=?", (chat_id,))
    bots = c.fetchall()
    c.close()
    if not bots:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.edit_message_text(
            "📋 **بوتاتك**\n\nلا تمتلك أي بوتات حالياً.\nاستخدم '🤖 صانع البوتات' لإنشاء بوت جديد.",
            chat_id,
            message_id,
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return
    text = "📋 **بوتاتك**\n\n"
    kb = types.InlineKeyboardMarkup(row_width=2)
    for bot_id, username, status in bots:
        status_emoji = "🟢" if status == "running" else "🔴"
        text += f"{status_emoji} @{username} - {status}\n"
        kb.add(
            types.InlineKeyboardButton("▶️ تشغيل" if status != "running" else "⏸ إيقاف", callback_data=f"startbot_{bot_id}" if status != "running" else f"stopbot_{bot_id}"),
            types.InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{bot_id}")
        )
    kb.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="my_bots"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="Markdown")

# ===================================================================
# باقي الأزرار
# ===================================================================
@bot.message_handler(func=lambda m: m.text == "🎵 بوت صوتي")
def voice_bot(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    try:
        from gtts import gTTS
        msg = bot.send_message(message.chat.id, "🎵 **بوت صوتي**\n\n📝 أرسل النص الذي تريد تحويله إلى صوت:", reply_markup=kb, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_voice)
    except:
        bot.send_message(message.chat.id, "❌ **بوت صوتي غير متاح**\n\nمكتبة gTTS غير مثبتة.", reply_markup=kb, parse_mode="Markdown")

def process_voice(message):
    try:
        if not message.text:
            return
        from gtts import gTTS
        tts = gTTS(text=message.text, lang='ar')
        filename = f"voice_{message.from_user.id}.mp3"
        tts.save(filename)
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, caption="🎵 **تم تحويل النص إلى صوت!**", parse_mode="Markdown")
        os.remove(filename)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "📢 إدارة قناة")
def channel_manager(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, "📢 **إدارة قناة**\n\nهذه الميزة قيد التطوير...", reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎨 إنشاء لوجو")
def create_logo(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    if not PIL_AVAILABLE:
        bot.send_message(message.chat.id, "❌ Pillow غير مثبتة.", reply_markup=kb, parse_mode="Markdown")
        return
    msg = bot.send_message(message.chat.id, "🎨 **إنشاء لوجو**\n\nأرسل النص:", reply_markup=kb, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_logo)

def process_logo(message):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (600, 200), color='#2b2b2b')
        d = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        d.text((50, 75), message.text, fill='white', font=font)
        filename = f"logo_{message.from_user.id}.png"
        img.save(filename)
        with open(filename, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"🎨 **لوجو مخصص**\n\nالنص: {message.text}", parse_mode="Markdown")
        os.remove(filename)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "📝 منشورات")
def posts(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, "📝 **المنشورات**\n\nهذه الميزة قيد التطوير...", reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌐 بروكسي")
def proxy(message):
    c = conn.cursor()
    c.execute("SELECT ip, port, country FROM proxies")
    proxies = c.fetchall()
    c.close()
    if not proxies:
        bot.send_message(message.chat.id, "🌐 **بروكسي**\n\nلا توجد بروكسيات.", parse_mode="Markdown")
        return
    text = "🌐 **بروكسيات متاحة**\n\n" + "\n".join(f"🔹 {ip}:{port} - {country}" for ip, port, country in proxies)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_proxy"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌍 ترجمة")
def translate(message):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇸🇦 عربي", callback_data="lang_ar"),
        types.InlineKeyboardButton("🇬🇧 إنجليزي", callback_data="lang_en"),
        types.InlineKeyboardButton("🇫🇷 فرنسي", callback_data="lang_fr"),
        types.InlineKeyboardButton("🇹🇷 تركي", callback_data="lang_tr"),
        types.InlineKeyboardButton("🇩🇪 ألماني", callback_data="lang_de"),
        types.InlineKeyboardButton("🇪🇸 إسباني", callback_data="lang_es")
    )
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    if not translator:
        bot.send_message(message.chat.id, "❌ الترجمة غير متاحة.", reply_markup=kb, parse_mode="Markdown")
        return
    bot.send_message(message.chat.id, "🌍 **ترجمة**\n\nاختر اللغة ثم أرسل النص:", reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👥 زيادة أعضاء")
def increase_members(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔗 رابط الدعوة", callback_data="my_referral_link"),
        types.InlineKeyboardButton("📊 إحالاتي", callback_data="my_referrals"),
        types.InlineKeyboardButton("📤 دعوة أصدقاء", callback_data="invite_friends")
    )
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    count = get_referral_count(message.from_user.id)
    points = get_user_points(message.from_user.id)
    points_word = get_setting("points_word")
    bot.send_message(
        message.chat.id,
        f"👥 **زيادة أعضاء**\n\n📊 عدد إحالاتك: {count}\n💳 النقاط: {points} {points_word}\n\nادعُ أصدقائك واحصل على مكافآت!",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📥 تحميل")
def download(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    try:
        import yt_dlp
        msg = bot.send_message(message.chat.id, "📥 **تحميل**\n\nأرسل رابط الفيديو:", reply_markup=kb, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_download)
    except:
        bot.send_message(message.chat.id, "❌ yt-dlp غير مثبتة.", reply_markup=kb, parse_mode="Markdown")

def process_download(message):
    try:
        import yt_dlp
        url = message.text.strip()
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'download_%(id)s.%(ext)s',
        }
        bot.send_message(message.chat.id, "⏳ جاري التحميل... يرجى الانتظار.")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
