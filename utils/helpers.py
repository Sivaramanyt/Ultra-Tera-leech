"""
Helper functions
"""
import re
import config

def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    return user_id == config.OWNER_ID

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    if is_owner(user_id):
        return True
    
    if not config.AUTHORIZED_CHATS:
        return True  # Public bot
    
    authorized = config.AUTHORIZED_CHATS.split()
    return str(user_id) in authorized

def extract_terabox_url(text: str) -> str:
    """Extract Terabox URL from text - SIMPLIFIED"""
    
    # Simple approach - find any URL with terabox-like domains
    text_lower = text.lower()
    
    # Split by spaces and find URL
    words = text.split()
    
    for word in words:
        word_lower = word.lower()
        # Check if it contains terabox patterns and /s/
        if any(domain in word_lower for domain in ['terabox', '1024tera', 'teraboxurl', '4funbox', 'mirrobox', 'nephobox']) and '/s/' in word:
            return word  # Return the original case URL
    
    return ""

def format_bytes(bytes_count: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

def calculate_eta(downloaded: int, total: int, speed: float) -> str:
    """Calculate ETA"""
    if speed <= 0 or total <= downloaded:
        return "Unknown"
    
    remaining = total - downloaded
    eta_seconds = remaining / speed
    
    if eta_seconds < 60:
        return f"{int(eta_seconds)}s"
    elif eta_seconds < 3600:
        return f"{int(eta_seconds/60)}m {int(eta_seconds%60)}s"
    else:
        hours = int(eta_seconds / 3600)
        minutes = int((eta_seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    
