"""
Configuration for Terabox Leech Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Required Settings
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
TELEGRAM_API = int(os.environ.get('TELEGRAM_API', '0'))
TELEGRAM_HASH = os.environ.get('TELEGRAM_HASH', '')

# Basic Settings
DOWNLOAD_DIR = '/usr/src/app/downloads/'
AUTHORIZED_CHATS = os.environ.get('AUTHORIZED_CHATS', '')
SUDO_USERS = os.environ.get('SUDO_USERS', '')

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Leech Settings
LEECH_SPLIT_SIZE = int(os.environ.get('LEECH_SPLIT_SIZE', '2147483648'))
AS_DOCUMENT = os.environ.get('AS_DOCUMENT', 'False').lower() == 'true'
QUEUE_ALL = int(os.environ.get('QUEUE_ALL', '4'))

# Verification System
VERIFICATION_ENABLED = os.environ.get('VERIFICATION_ENABLED', 'True').lower() == 'true'
FREE_LEECH_COUNT = int(os.environ.get('FREE_LEECH_COUNT', '3'))
VERIFY_VALIDITY_TIME = int(os.environ.get('VERIFY_VALIDITY_TIME', '3600'))

# Shortlink Configuration
SHORTLINK_API = os.environ.get('SHORTLINK_API', '')
SHORTLINK_URL = os.environ.get('SHORTLINK_URL', '')
SHORTLINK_TYPE = os.environ.get('SHORTLINK_TYPE', 'shorte.st')

# Auto-Forward
AUTO_FORWARD_ENABLED = os.environ.get('AUTO_FORWARD_ENABLED', 'True').lower() == 'true'
LEECH_LOG_CHANNEL = os.environ.get('LEECH_LOG_CHANNEL', '')
FORWARD_TAGS = os.environ.get('FORWARD_TAGS', 'True').lower() == 'true'

# Custom Messages
PROGRESS_PREFIX = os.environ.get('PROGRESS_PREFIX', '📥 Downloading')
UPLOAD_PREFIX = os.environ.get('UPLOAD_PREFIX', '📤 Uploading')
SUCCESS_PREFIX = os.environ.get('SUCCESS_PREFIX', '✅ Successfully Leeched')
ERROR_PREFIX = os.environ.get('ERROR_PREFIX', '❌ Error')
BOT_NAME = os.environ.get('BOT_NAME', 'Terabox Leech Bot')

# Verification Messages
VERIFY_MSG = os.environ.get('VERIFY_MSG', '🔐 Please complete verification to continue')
VERIFY_SUCCESS_MSG = os.environ.get('VERIFY_SUCCESS_MSG', '✅ Verification successful!')
VERIFY_EXPIRED_MSG = os.environ.get('VERIFY_EXPIRED_MSG', '⏰ Verification expired.')

# Terabox APIs
TERABOX_API_ENDPOINTS = [
    "https://wdzone-terabox-api.vercel.app/api/download",
    "https://api.teradownloader.com/v1/download",
    "https://terabox-dl.qtcloud.workers.dev/",
]

# Debug
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required!")
if not OWNER_ID:
    raise ValueError("OWNER_ID is required!")
