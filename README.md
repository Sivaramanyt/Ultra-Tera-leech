# 🚀 Terabox Leech Bot

A powerful Telegram bot to download files from Terabox links with verification system and auto-forwarding.

## ✨ Features
- 📥 Download from Terabox, 1024tera, 4funbox, mirrobox
- 🔐 Shortlink verification system (configurable)
- 📤 Auto-forward to your channel
- 🎨 Custom progress messages
- ⚡ Multiple API endpoints for reliability
- 💾 User tracking with MongoDB

## 🚀 Quick Deploy to Koyeb

1. Fork this repository
2. Connect to Koyeb
3. Set environment variables:
   - `BOT_TOKEN` = Your bot token
   - `OWNER_ID` = Your Telegram user ID
   - `TELEGRAM_API` = From my.telegram.org
   - `TELEGRAM_HASH` = From my.telegram.org
4. Deploy!

## 📋 Commands
- `/start` - Start the bot
- `/help` - Help message
- `/stats` - Statistics (owner only)
- Send Terabox link - Download file

## 🔧 Optional Settings
- `VERIFICATION_ENABLED=True` - Enable verification
- `FREE_LEECH_COUNT=3` - Free downloads before verification
- `SHORTLINK_API=your_key` - Shortlink API key
- `LEECH_LOG_CHANNEL=-100xxx` - Auto-forward channel

Made with ❤️ for Koyeb deployment
