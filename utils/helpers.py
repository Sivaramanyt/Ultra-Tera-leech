"""
Helper functions - FIXED
"""
import re
import config

def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    return user_id == config.OWNER_ID

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    return True  # Allow everyone for now

def extract_terabox_url(text: str) -> str:
    """Extract Terabox URL from text - FIXED"""
    if not text:
        return ""
    
    # Simple approach - just return the text if it contains terabox domains
    text_lower = text.lower()
    terabox_domains = [
        'terabox.com',
        '1024terabox.com', 
        'teraboxurl.com',
        '4funbox.com',
        'mirrobox.com',
        'nephobox.com',
        '1024tera.com'
    ]
    
    for domain in terabox_domains:
        if domain in text_lower and 'http' in text_lower:
            return text.strip()  # Return the full text as URL
    
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
        
