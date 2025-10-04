"""
Database CRUD operations
"""
from typing import Dict, Optional
from loguru import logger

from .connection import db_manager
from .models import UserModel, StatsModel

class UserOperations:
    def __init__(self):
        self.collection_name = 'users'
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                return await collection.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Get user error: {e}")
        return None
    
    async def create_user(self, user_id: int, **kwargs) -> bool:
        """Create new user"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                user_doc = UserModel.create_user_doc(user_id, **kwargs)
                await collection.insert_one(user_doc)
                return True
        except Exception as e:
            logger.error(f"Create user error: {e}")
        return False
    
    async def update_user(self, user_id: int, data: Dict) -> bool:
        """Update user data"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                update_doc = UserModel.update_user_doc(**data)
                result = await collection.update_one(
                    {'user_id': user_id},
                    update_doc,
                    upsert=True
                )
                return result.acknowledged
        except Exception as e:
            logger.error(f"Update user error: {e}")
        return False
    
    async def get_user_count(self) -> int:
        """Get total user count"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                return await collection.count_documents({})
        except Exception as e:
            logger.error(f"User count error: {e}")
        return 0

class StatsOperations:
    def __init__(self):
        self.collection_name = 'stats'
    
    async def get_stats(self) -> Optional[Dict]:
        """Get bot statistics"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                return await collection.find_one()
        except Exception as e:
            logger.error(f"Get stats error: {e}")
        return None
    
    async def update_stats(self, data: Dict) -> bool:
        """Update statistics"""
        try:
            collection = db_manager.get_collection(self.collection_name)
            if collection:
                await collection.update_one(
                    {},
                    {'$set': data},
                    upsert=True
                )
                return True
        except Exception as e:
            logger.error(f"Update stats error: {e}")
        return False
