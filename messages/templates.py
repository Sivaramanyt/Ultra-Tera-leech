"""
Message templates
"""
import config

class MessageTemplates:
    def welcome_message(self, user_name: str) -> str:
        """Welcome message"""
        return f"""
🎉 <b>Welcome {user_name}!</b>

I'm <b>{config.BOT_NAME}</b> - your Terabox file downloader!

<b>📥 How to use:</b>
1. Send me any Terabox link
2. I'll download and send it to you
3. {f"Complete verification after {config.FREE_LEECH_COUNT} free downloads" if config.VERIFICATION_ENABLED else "Unlimited downloads!"}

<b>🔗 Supported links:</b>
• terabox.com
• 1024tera.com  
• 4funbox.com
• mirrobox.com
• nephobox.com

<b>⚡ Features:</b>
• Fast downloads
• Progress tracking
• Auto-forwarding
• Queue management

Send me a link to get started! 🚀
"""

    def help_message(self) -> str:
        """Help message"""
        return f"""
<b>📋 {config.BOT_NAME} Commands:</b>

<b>🤖 Commands:</b>
/start - Start the bot
/help - Show this help message
/stats - Bot statistics (owner only)

<b>📥 How to download:</b>
1. Copy any Terabox share link
2. Send it to me
3. Wait for download to complete
4. Enjoy your file! 

<b>🔐 Verification System:</b>
{"✅ Enabled" if config.VERIFICATION_ENABLED else "❌ Disabled"}
{f"• {config.FREE_LEECH_COUNT} free downloads per user" if config.VERIFICATION_ENABLED else ""}
{f"• Verification valid for {config.VERIFY_VALIDITY_TIME//3600} hours" if config.VERIFICATION_ENABLED else ""}

<b>⚙️ Settings:</b>
• Max file size: {config.LEECH_SPLIT_SIZE // (1024*1024*1024)}GB
• Queue limit: {config.QUEUE_ALL} concurrent downloads
• Auto-forward: {"✅ Enabled" if config.AUTO_FORWARD_ENABLED else "❌ Disabled"}

<b>🆘 Need help?</b>
Contact: @YourUsername
"""

    def stats_message(self, stats: dict) -> str:
        """Stats message for owner"""
        return f"""
<b>📊 {config.BOT_NAME} Statistics</b>

<b>👥 Users:</b>
• Total users: {stats.get('total_users', 0)}
• Active downloads: {stats.get('active_downloads', 0)}

<b>⚙️ Settings:</b>
• Verification: {"✅ On" if config.VERIFICATION_ENABLED else "❌ Off"}
• Free downloads: {config.FREE_LEECH_COUNT}
• Auto-forward: {"✅ On" if config.AUTO_FORWARD_ENABLED else "❌ Off"}
• Queue limit: {config.QUEUE_ALL}

<b>🔧 System:</b>
• Bot name: {config.BOT_NAME}
• Database: {"✅ Connected" if config.DATABASE_URL else "❌ Not configured"}
"""

    def verification_required_message(self, downloads_used: int) -> str:
        """Verification required message"""
        return f"""
🔐 <b>Verification Required</b>

You've used <b>{downloads_used}/{config.FREE_LEECH_COUNT}</b> free downloads.

To continue downloading, please complete verification by clicking the button below.

⏰ <i>Verification is valid for {config.VERIFY_VALIDITY_TIME//3600} hours</i>
"""

    def download_progress_message(self, filename: str, progress: float, speed: str, eta: str) -> str:
        """Download progress message"""
        bar_length = 10
        filled = int(progress / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"""
{config.PROGRESS_PREFIX}

<b>📄 File:</b> <code>{filename[:30]}...</code>
<b>📊 Progress:</b> {progress:.1f}%
<code>[{bar}]</code>
<b>⚡ Speed:</b> {speed}
<b>⏱️ ETA:</b> {eta}
"""

    def upload_progress_message(self, filename: str) -> str:
        """Upload progress message"""
        return f"""
{config.UPLOAD_PREFIX}

<b>📄 File:</b> <code>{filename}</code>
<b>📤 Status:</b> Uploading to Telegram...

<i>Please wait, this may take a moment...</i>
"""

    def success_message(self, filename: str, file_size: str) -> str:
        """Success message"""
        return f"""
{config.SUCCESS_PREFIX}

<b>📄 File:</b> <code>{filename}</code>
<b>💾 Size:</b> {file_size}
<b>⏱️ Status:</b> Ready!

<i>Downloaded by {config.BOT_NAME}</i>
"""

    def error_message(self, error: str) -> str:
        """Error message"""
        return f"""
{config.ERROR_PREFIX}

<b>❌ Download Failed</b>

<b>Reason:</b> {error}

<i>Please try again or contact support if the problem persists.</i>
"""
