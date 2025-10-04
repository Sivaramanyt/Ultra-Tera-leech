"""
Callback handlers for inline buttons
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
            # Create a mock update object for the subscription check
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
        
        elif query.data.startswith("no_link_"):
            # Handle channels without accessible links
            await query.answer(
                "Please contact admin to get access to this channel.",
                show_alert=True
            )
        
        else:
            # Handle unknown callback data
            await query.answer("Unknown action", show_alert=True)
                
