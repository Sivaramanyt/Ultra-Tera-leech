"""
Terabox utility functions
"""
import re
from typing import Optional

def is_terabox_url(url: str) -> bool:
    """Check if URL is a valid Terabox URL"""
    patterns = [
        r'https?://(?:www\.)?terabox\.com/s/[A-Za-z0-9_-]+',
        r'https?://(?:www\.)?1024tera\.com/s/[A-Za-z0-9_-]+',
        r'https?://(?:www\.)?4funbox\.com/s/[A-Za-z0-9_-]+',
        r'https?://(?:www\.)?mirrobox\.com/s/[A-Za-z0-9_-]+',
        r'https?://(?:www\.)?nephobox\.com/s/[A-Za-z0-9_-]+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False

def extract_share_id(url: str) -> Optional[str]:
    """Extract share ID from Terabox URL"""
    match = re.search(r'/s/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def normalize_filename(filename: str) -> str:
    """Normalize filename for safe storage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
    
    return filename
