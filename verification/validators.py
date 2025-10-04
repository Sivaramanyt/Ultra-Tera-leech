"""
Token validation utilities
"""
import re
import time
from typing import Tuple

def validate_token_format(token: str) -> bool:
    """Validate token format"""
    pattern = r'^\d+_\d+_[a-f0-9]{16}$'
    return bool(re.match(pattern, token))

def is_token_expired(timestamp: int, validity_time: int) -> bool:
    """Check if token is expired"""
    current_time = int(time.time())
    return (current_time - timestamp) > validity_time

def extract_token_parts(token: str) -> Tuple[int, int, str]:
    """Extract parts from token"""
    parts = token.split('_')
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    
    user_id = int(parts[0])
    timestamp = int(parts[1])
    hash_part = parts[2]
    
    return user_id, timestamp, hash_part
