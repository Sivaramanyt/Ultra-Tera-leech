"""
Database connection management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import config

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            if config.DATABASE_URL:
                self.client = AsyncIOMotorClient(config.DATABASE_URL)
                self.db = self.client.terabox_bot
                
                # Test connection
                await self.client.admin.command('ping')
                logger.info("✅ Database connected")
            else:
                logger.warning("No database URL configured")
                
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            self.client = None
            self.db = None
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
    
    def get_collection(self, name: str):
        """Get collection"""
        if self.db:
            return self.db[name]
        return None

# Global database manager
db_manager = DatabaseManager()
