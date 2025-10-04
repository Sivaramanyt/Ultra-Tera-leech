"""
Verification manager for user verification
"""
import time
import hashlib
from loguru import logger
from typing import Dict, Optional, Tuple

from .shortlink import ShortlinkGenerator
from database.operations import UserOperations
import config

class VerificationManager:
    def __init__(self):
        self.shortlink = ShortlinkGenerator()
        self.user_ops = UserOperations() if config.DATABASE_URL else None
        self.memory_store = {}  # Fallback if no database
    
    async def need_verification(self, user_id: int) -> bool:
        """Check if user needs verification"""
        try:
            if self.user_ops:
                user_data = await self.user_ops.get_user(user_id)
                downloads = user_data.get('downloads', 0) if user_data else 0
                last_verify = user_data.get('last_verify', 0) if user_data else 0
            else:
                user_data = self.memory_store.get(user_id, {})
                downloads = user_data.get('downloads', 0)
                last_verify = user_data.get('last_verify', 0)
            
            current_time = int(time.time())
            
            # Need verification if exceeded free count and verification expired
            if downloads >= config.FREE_LEECH_COUNT:
                if current_time - last_verify > config.VERIFY_VALIDITY_TIME:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Verification check error: {e}")
            return False
    
    async def generate_verification(self, user_id: int) -> Optional[Dict]:
        """Generate verification link"""
        try:
            # Create token
            timestamp = int(time.time())
            raw_data = f"{user_id}:{timestamp}:{config.SHORTLINK_API}"
            token = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
            verification_token = f"{user_id}_{timestamp}_{token}"
            
            # Create verification URL
            verify_url = f"https://your-domain.com/verify/{verification_token}"
            
            # Generate shortlink
            short_url = await self.shortlink.create_shortlink(verify_url)
            
            if short_url:
                return {
                    'token': verification_token,
                    'verify_url': verify_url,
                    'short_url': short_url,
                    'expires_at': timestamp + config.VERIFY_VALIDITY_TIME
                }
            
        except Exception as e:
            logger.error(f"Verification generation error: {e}")
        
        return None
    
    async def verify_token(self, token: str, user_id: int) -> Tuple[bool, str]:
        """Verify token and update user"""
        try:
            parts = token.split('_')
            if len(parts) != 3:
                return False, "Invalid token format"
            
            token_user_id, timestamp, hash_part = parts
            
            # Check if token is for this user
            if int(token_user_id) != user_id:
                return False, "Token mismatch"
            
            # Check expiration
            current_time = int(time.time())
            token_time = int(timestamp)
            
            if current_time - token_time > config.VERIFY_VALIDITY_TIME:
                return False, "Token expired"
            
            # Verify hash
            raw_data = f"{user_id}:{timestamp}:{config.SHORTLINK_API}"
            expected_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
            
            if hash_part != expected_hash:
                return False, "Invalid token"
            
            # Update user verification time
            if self.user_ops:
                await self.user_ops.update_user(user_id, {'last_verify': current_time})
            else:
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = {}
                self.memory_store[user_id]['last_verify'] = current_time
            
            return True, "Verification successful"
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, "Verification error"
    
    async def get_user_downloads(self, user_id: int) -> int:
        """Get user download count"""
        try:
            if self.user_ops:
                user_data = await self.user_ops.get_user(user_id)
                return user_data.get('downloads', 0) if user_data else 0
            else:
                return self.memory_store.get(user_id, {}).get('downloads', 0)
        except:
            return 0
    
    async def increment_user_downloads(self, user_id: int):
        """Increment user download count"""
        try:
            if self.user_ops:
                user_data = await self.user_ops.get_user(user_id)
                current_downloads = user_data.get('downloads', 0) if user_data else 0
                await self.user_ops.update_user(user_id, {'downloads': current_downloads + 1})
            else:
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = {}
                current = self.memory_store[user_id].get('downloads', 0)
                self.memory_store[user_id]['downloads'] = current + 1
                
        except Exception as e:
            logger.error(f"Download increment error: {e}")
