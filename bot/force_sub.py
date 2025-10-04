"""
Force subscription functionality - Supports Private Channels
"""
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import config

class ForceSubscription:
    def __init__(self):
        pass
    
    async def check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if user is subscribed to required channels"""
        user_id = update.effective_user.id
        
        # Skip check for owner
        if user_id == config.OWNER_ID:
            return True
        
        # Skip if no force sub channels configured
        if not hasattr(config, 'FORCE_SUB_CHANNELS') or not config.FORCE_SUB_CHANNELS:
            return True
        
        channels = config.FORCE_SUB_CHANNELS.split()
        not_subscribed = []
        channel_links = {}
        
        for channel in channels:
            try:
                # Handle both username (@channel) and ID (-1001234567890)
                if channel.startswith('@'):
                    chat_id = channel
                    channel_username = channel.replace('@', '')
                    invite_link = f"https://t.me/{channel_username}"
                elif channel.startswith('-'):
                    # Private channel ID
                    chat_id = int(channel)
                    # Get invite link for private channel
                    try:
                        chat = await context.bot.get_chat(chat_id)
                        invite_link = await context.bot.export_chat_invite_link(chat_id)
                        channel_username = chat.title or f"Private Channel"
                    except Exception as e:
                        logger.error(f"Could not get invite link for {chat_id}: {e}")
                        invite_link = None
                        channel_username = f"Private Channel {chat_id}"
                else:
                    # Assume it's username without @
                    chat_id = f"@{channel}"
                    channel_username = channel
                    invite_link = f"https://t.me/{channel}"
                
                # Check membership
                member = await context.bot.get_chat_member(chat_id, user_id)
                
                if member.status in ['left', 'kicked']:
                    not_subscribed.append(channel_username)
                    if invite_link:
                        channel_links[channel_username] = invite_link
                    
            except BadRequest as e:
                logger.warning(f"Could not check subscription for {channel}: {e}")
                # If we can't check, assume not subscribed for safety
                channel_username = f"Channel {channel}"
                not_subscribed.append(channel_username)
                # For private channels, we might not be able to get invite link
                if not channel.startswith('-'):
                    channel_links[channel_username] = f"https://t.me/{channel.replace('@', '')}"
                    
            except Exception as e:
                logger.error(f"Subscription check error for {channel}: {e}")
                channel_username = f"Channel {channel}"
                not_subscribed.append(channel_username)
        
        if not_subscribed:
            await self._send_force_sub_message(update, not_subscribed, channel_links)
            return False
        
        return True
    
    async def _send_force_sub_message(self, update: Update, channels, channel_links):
        """Send force subscription message with buttons"""
        try:
            # Create buttons for each channel
            keyboard = []
            
            for channel in channels:
                if channel in channel_links:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📢 Join {channel}",
                            url=channel_links[channel]
                        )
                    ])
                else:
                    # For channels without links (might be private and we can't get invite link)
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📢 {channel}",
                            callback_data=f"no_link_{channel[:20]}"
                        )
                    ])
            
            # Add check subscription button
            keyboard.append([
                InlineKeyboardButton(
                    "✅ Check Subscription",
                    callback_data="check_subscription"
                )
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            channel_list = '\n'.join([f"• {ch}" for ch in channels])
            
            message = (
                f"🔒 **Subscription Required**\n\n"
                f"To use this bot, you must join our channel(s):\n\n"
                f"{channel_list}\n\n"
                f"**Steps:**\n"
                f"1. Click the button(s) below to join\n"
                f"2. Click '✅ Check Subscription' when done\n"
                f"3. Start using the bot!\n\n"
                f"🎯 This helps us grow our community!"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Force sub message error: {e}")
            await update.message.reply_text(
                "❌ **Subscription Required**\n\n"
                "Please join our channels to use this bot.\n"
                "Contact admin for more information.",
                parse_mode='Markdown'
            )

# Global instance
force_subscription = ForceSubscription()
