"""
Database models and schemas
"""
from datetime import datetime
from typing import Dict, Optional

class UserModel:
    """User data model"""
    
    @staticmethod
    def create_user_doc(user_id: int, **kwargs) -> Dict:
        """Create user document"""
        return {
            'user_id': user_id,
            'downloads': kwargs.get('downloads', 0),
            'last_verify': kwargs.get('last_verify', 0),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_banned': kwargs.get('is_banned', False),
            'total_size': kwargs.get('total_size', 0)
        }
    
    @staticmethod
    def update_user_doc(**kwargs) -> Dict:
        """Create update document"""
        update_doc = {
            'updated_at': datetime.utcnow()
        }
        
        for key, value in kwargs.items():
            if key in ['downloads', 'last_verify', 'is_banned', 'total_size']:
                update_doc[key] = value
        
        return {'$set': update_doc}

class StatsModel:
    """Bot statistics model"""
    
    @staticmethod
    def create_stats_doc() -> Dict:
        """Create stats document"""
        return {
            'total_users': 0,
            'total_downloads': 0,
            'total_size': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
