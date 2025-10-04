"""
Configuration file for Terabox Leech Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_NAME = os.getenv("BOT_NAME", "Terabox Leech Bot")

# Owner Configuration
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Download Configuration
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# Database Configuration (optional)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Channel Configuration
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")  # Optional: Channel to log activities
DUMP_CHANNEL = os.getenv("DUMP_CHANNEL", "")  # Optional: Channel to forward files

# Force Subscription Configuration
FORCE_SUB_CHANNELS = os.getenv("FORCE_SUB_CHANNELS", "")
# Examples:
# Public channels: "@channel1 @channel2"  
# Private channels: "-1001234567890 -1009876543210"
# Mixed: "@publicchannel -1001234567890"

# Authorization Configuration (optional)
AUTHORIZED_CHATS = os.getenv("AUTHORIZED_CHATS", "")  # Space-separated user IDs

# API Configuration (optional - for future features)
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")

# Webhook Configuration (for production)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8000"))

# Feature Flags
ENABLE_FORCE_SUB = os.getenv("ENABLE_FORCE_SUB", "true").lower() == "true"
ENABLE_CANCEL_COMMAND = os.getenv("ENABLE_CANCEL_COMMAND", "true").lower() == "true"

# File Size Limits (in bytes)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB default

# Rate Limiting (optional)
MAX_DOWNLOADS_PER_USER = int(os.getenv("MAX_DOWNLOADS_PER_USER", "5"))  # Per hour

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

if not OWNER_ID:
    raise ValueError("OWNER_ID is required")

print(f"✅ Config loaded - Bot: {BOT_NAME}")
if FORCE_SUB_CHANNELS:
    print(f"🔒 Force subscription enabled for: {FORCE_SUB_CHANNELS}")
else:
    print("🔓 Force subscription disabled")
