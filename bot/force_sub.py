"""
Force subscription functionality - Full Private Channel Support
"""
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
import config

class ForceSubscription:
    def __init__(self):
        self.channel_cache = {}  # Cache channel info for performance
    
    async def check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if user is subscribed to required channels"""
        user_id = update.effective_user.id
        
        # Skip check for owner
        if user_id == config.OWNER_ID:
            return True
        
        # Skip if disabled or not configured
        if (not hasattr(config, 'FORCE_SUB_CHANNELS') or 
            not config.FORCE_SUB_CHANNELS or 
            not getattr(config, 'ENABLE_FORCE_SUB', True)):
            return True
        
        try:
            channels = config.FORCE_SUB_CHANNELS.split()
            not_subscribed = []
            channel_info = {}
            
            for channel in channels:
                try:
                    # Parse channel (username or ID)
                    chat_id, channel_data = await self._parse_channel(channel, context)
                    
                    if not chat_id:
                        continue
                    
                    # Check membership
                    member = await context.bot.get_chat_member(chat_id, user_id)
                    
                    if member.status in ['left', 'kicked']:
                        not_subscribed.append(channel)
                        channel_info[channel] = channel_data
                        
                except Exception as e:
                    logger.warning(f"Could not check subscription for {channel}: {e}")
                    # For private channels that we can't check, assume not subscribed
                    not_subscribed.append(channel)
                    channel_info[channel] = {
                        'name': f"Private Channel {channel}",
                        'invite_link': None,
                        'is_private': True
                    }
            
            if not_subscribed:
                await self._send_force_sub_message(update, not_subscribed, channel_info)
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Force subscription check error: {e}")
            return True  # Allow access if check fails
    
    async def _parse_channel(self, channel: str, context: ContextTypes.DEFAULT_TYPE):
        """Parse channel and get info"""
        try:
            # Check cache first
            if channel in self.channel_cache:
                cached = self.channel_cache[channel]
                return cached['chat_id'], cached['data']
            
            chat_id = None
            channel_data = {}
            
            if channel.startswith('@'):
                # Public channel
                chat_id = channel
                channel_username = channel.replace('@', '')
                
                try:
                    chat = await context.bot.get_chat(chat_id)
                    channel_data = {
                        'name': chat.title or channel_username,
                        'invite_link': f"https://t.me/{channel_username}",
                        'is_private': False
                    }
                except:
                    channel_data = {
                        'name': channel_username,
                        'invite_link': f"https://t.me/{channel_username}",
                        'is_private': False
                    }
                    
            elif channel.startswith('-'):
                # Private channel (ID)
                chat_id = int(channel)
                
                try:
                    chat = await context.bot.get_chat(chat_id)
                    
                    # Try to get invite link
                    invite_link = None
                    try:
                        invite_link = await context.bot.export_chat_invite_link(chat_id)
                    except (BadRequest, Forbidden):
                        # Bot doesn't have permission to export invite link
                        logger.warning(f"Cannot export invite link for {chat_id}")
                    
                    channel_data = {
                        'name': chat.title or f"Private Channel {chat_id}",
                        'invite_link': invite_link,
                        'is_private': True
                    }
                    
                except Exception as e:
                    logger.warning(f"Cannot get info for private channel {chat_id}: {e}")
                    channel_data = {
                        'name': f"Private Channel {chat_id}",
                        'invite_link': None,
                        'is_private': True
                    }
            else:
                # Assume username without @
                chat_id = f"@{channel}"
                channel_data = {
                    'name': channel,
                    'invite_link': f"https://t.me/{channel}",
                    'is_private': False
                }
            
            # Cache the result
            self.channel_cache[channel] = {
                'chat_id': chat_id,
                'data': channel_data
            }
            
            return chat_id, channel_data
            
        except Exception as e:
            logger.error(f"Error parsing channel {channel}: {e}")
            return None, {}
    
    async def _send_force_sub_message(self, update: Update, channels, channel_info):
        """Send force subscription message with private channel support"""
        try:
            keyboard = []
            channel_list = []
            
            for channel in channels:
                info = channel_info.get(channel, {})
                channel_name = info.get('name', channel)
                invite_link = info.get('invite_link')
                is_private = info.get('is_private', False)
                
                # Add to display list
                channel_list.append(f"• {channel_name}")
                
                # Create button
                if invite_link:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📢 Join {channel_name[:20]}{'...' if len(channel_name) > 20 else ''}",
                            url=invite_link
                        )
                    ])
                else:
                    # For private channels without invite link
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🔒 {channel_name[:20]}{'...' if len(channel_name) > 20 else ''} (Contact Admin)",
                            callback_data=f"no_access_{channel[:10]}"
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
            
            channel_list_str = '\n'.join(channel_list)
            
            message = (
                f"🔒 **Subscription Required**\n\n"
                f"To use this bot, you must join our channel(s):\n\n"
                f"{channel_list_str}\n\n"
                f"**Steps:**\n"
                f"1. Click the button(s) below to join\n"
                f"2. For private channels, contact admin if needed\n"
                f"3. Click '✅ Check Subscription' when done\n"
                f"4. Start using the bot!\n\n"
                f"🎯 This helps us grow our community!"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Force sub message error: {e}")
            # Fallback message
            await update.message.reply_text(
                "🔒 **Subscription Required**\n\n"
                "Please join our required channels to use this bot.\n"
                "Contact admin for more information.",
                parse_mode='Markdown'
            )

# Global instance
force_subscription = ForceSubscription()
                        
