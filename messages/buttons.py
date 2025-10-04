"""
Inline keyboard buttons
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class ButtonLayouts:
    @staticmethod
    def verification_button(verification_url: str) -> InlineKeyboardMarkup:
        """Verification button"""
        keyboard = [[
            InlineKeyboardButton("🔐 Complete Verification", url=verification_url)
        ]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cancel_download_button(user_id: int) -> InlineKeyboardMarkup:
        """Cancel download button"""
        keyboard = [[
            InlineKeyboardButton("❌ Cancel Download", callback_data=f"cancel_{user_id}")
        ]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def help_buttons() -> InlineKeyboardMarkup:
        """Help navigation buttons"""
        keyboard = [
            [InlineKeyboardButton("📥 How to Download", callback_data="help_download")],
            [InlineKeyboardButton("🔐 Verification Info", callback_data="help_verify")],
            [InlineKeyboardButton("❓ FAQ", callback_data="help_faq")]
        ]
        return InlineKeyboardMarkup(keyboard)
