"""
Callback handlers for inline buttons - Private Channel Support
"""
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .force_sub import force_subscription

class CallbackHandlers:
    def __init__(self):
        pass
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "check_subscription":
            # Re-check subscription
            mock_update = type('MockUpdate', (), {
                'effective_user': update.effective_user,
                'message': query.message
            })()
            
            if await force_subscription.check_subscription(mock_update, context):
                await query.edit_message_text(
                    "✅ **Subscription Verified!**\n\n"
                    "Thank you for joining our channel(s)!\n"
                    "You can now use the bot freely.\n\n"
                    "Send /start to begin!",
                    parse_mode='Markdown'
                )
            # If not subscribed, the check function will send the force sub message again
        
        elif query.data.startswith("no_access_"):
            # Handle private channels without accessible invite links
            await query.answer(
                "This is a private channel. Please contact the admin to get access.",
                show_alert=True
            )
        
        else:
            # Handle unknown callback data
            await query.answer("Unknown action", show_alert=True)
            
