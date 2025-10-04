"""
Custom filters for message detection
"""
import re
from telegram.ext import filters

class TeraboxFilter(filters.MessageFilter):
    """Filter for Terabox links"""
    
    def filter(self, message):
        if not message.text:
            return False
        
        text = message.text.lower()
        
        # Check for any terabox-related domain
        terabox_keywords = [
            'terabox.com',
            '1024tera',
            'teraboxurl',
            '4funbox',
            'mirrobox',
            'nephobox'
        ]
        
        for keyword in terabox_keywords:
            if keyword in text and '/s/' in text:
                return True
        
        return False
        
