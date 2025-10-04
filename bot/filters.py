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
        
        patterns = [
            r'https?://(?:www\.)?terabox\.com/s/[A-Za-z0-9_-]+',
            r'https?://(?:www\.)?1024tera\.com/s/[A-Za-z0-9_-]+',
            r'https?://(?:www\.)?4funbox\.com/s/[A-Za-z0-9_-]+',
            r'https?://(?:www\.)?mirrobox\.com/s/[A-Za-z0-9_-]+',
            r'https?://(?:www\.)?nephobox\.com/s/[A-Za-z0-9_-]+',
        ]
        
        for pattern in patterns:
            if re.search(pattern, message.text, re.IGNORECASE):
                return True
        
        return False
