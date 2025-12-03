from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError, DuplicateKeyError
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from app.config import settings
import logging
from contextlib import asynccontextmanager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection errors"""
    pass

class MongoDBManager:
    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection - LOCAL ONLY (no cloud/Atlas)"""
        if not settings.MONGO_URI:
            raise ConfigurationError("MONGO_URI is not configured")
        
        # Validate that we're using local MongoDB, not Atlas/cloud
        mongo_uri_lower = settings.MONGO_URI.lower().strip()
        if mongo_uri_lower.startswith("mongodb+srv://") or "mongodb.net" in mongo_uri_lower or "atlas" in mongo_uri_lower:
            error_msg = (
                "MongoDB Atlas/cloud connections are not allowed. "
                "Please use local MongoDB: mongodb://localhost:27017"
            )
            logger.error(error_msg)
            raise MongoDBConnectionError(error_msg)
        
        # Ensure we're using local MongoDB
        if not mongo_uri_lower.startswith("mongodb://"):
            error_msg = (
                f"Invalid MongoDB URI format: {settings.MONGO_URI}. "
                "Expected format: mongodb://localhost:27017"
            )
            logger.error(error_msg)
            raise MongoDBConnectionError(error_msg)
            
        try:
            # Configure connection with timeout and retry settings for LOCAL MongoDB
            self._client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,        # 10 second connection timeout
                socketTimeoutMS=30000,          # 30 second socket timeout
                maxPoolSize=100,                # Maximum number of connections
                minPoolSize=10,                 # Minimum number of connections
                retryWrites=True,
                retryReads=True
            )
            self._db = self._client[settings.DATABASE_NAME]
            logger.info(f"MongoDB LOCAL connection initialized for database: {settings.DATABASE_NAME}")
            logger.info(f"Using MongoDB URI: {settings.MONGO_URI}")
        except ConfigurationError as e:
            logger.error(f"MongoDB configuration error: {e}")
            raise MongoDBConnectionError(f"MongoDB configuration error: {e}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise MongoDBConnectionError(f"Failed to connect to MongoDB: {e}")
    
    async def is_connected(self) -> bool:
        """Check if the database is connected"""
        try:
            if not self._client:
                return False
            # The ismaster command is cheap and does not require auth
            await self._client.admin.command('ismaster')
            return True
        except (ServerSelectionTimeoutError, ConnectionFailure):
            return False
        except Exception as e:
            logger.error(f"Error checking MongoDB connection: {e}")
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        if self._db is None:
            self._initialize()
        return self._db
    
    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get a collection from the database"""
        if self._db is None:
            raise MongoDBConnectionError("Database not initialized")
        return self._db[name]
        
    def get_internal_docs_collection(self) -> AsyncIOMotorCollection:
        """Get the internal documents collection"""
        return self.get_collection("internal_docs")
    
    async def close(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed.")

    async def _ensure_indexes(self):
        """Create necessary indexes for collections"""
        try:
            # Users collection indexes
            await self._db["users"].create_indexes([
                IndexModel([("email", ASCENDING)], unique=True),
                IndexModel([("role", ASCENDING)]),
                IndexModel([("is_active", ASCENDING)]),
                IndexModel([("api_keys.key", ASCENDING)], unique=True, sparse=True)
            ])
            
            # Conversations collection indexes
            await self._db["conversations"].create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("is_active", ASCENDING)])
            ])
            
            # Messages collection indexes
            await self._db["messages"].create_indexes([
                IndexModel([("conversation_id", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # Documents collection indexes
            await self._db["documents"].create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("file_type", ASCENDING)])
            ])
            
            # User-related collections and indexes
            await self._db["user_profiles"].create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("full_name", ASCENDING)])
            ])
            
            await self._db["user_settings"].create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("theme", ASCENDING)])
            ])
            
            await self._db["user_notifications"].create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("notification_type", ASCENDING)])
            ])
            
            # Create text index for search
            await self._db["users"].create_index([("email", TEXT), ("full_name", TEXT)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise
            
    async def create_initial_admin(self):
        """No longer creates admin user (authentication removed)"""
        logger.info("Skipping admin user creation - authentication disabled")
        try:
            # Keep method for backward compatibility but do nothing
            pass
        except Exception as e:
                logger.error(f"Error creating admin user: {e}")

# Create a singleton instance
mongodb_manager = MongoDBManager()

def get_db() -> AsyncIOMotorDatabase:
    """Get the database instance"""
    return mongodb_manager.get_database()

# Collection accessors
def get_users_collection() -> AsyncIOMotorCollection:
    """Get the users collection"""
    return mongodb_manager.get_collection("users")

def get_conversations_collection() -> AsyncIOMotorCollection:
    """Get the conversations collection"""
    return mongodb_manager.get_collection("conversations")

def get_messages_collection() -> AsyncIOMotorCollection:
    """Get the messages collection"""
    return mongodb_manager.get_collection("messages")

def get_documents_collection() -> AsyncIOMotorCollection:
    """Get the documents collection"""
    return mongodb_manager.get_collection("documents")

def get_user_profiles_collection() -> AsyncIOMotorCollection:
    """Get the user profiles collection"""
    return mongodb_manager.get_collection("user_profiles")

def get_user_settings_collection() -> AsyncIOMotorCollection:
    """Get the user settings collection"""
    return mongodb_manager.get_collection("user_settings")

def get_user_notifications_collection() -> AsyncIOMotorCollection:
    """Get the user notifications collection"""
    return mongodb_manager.get_collection("user_notifications")

# Initialize database connection and indexes
async def init_db():
    """Initialize the database connection and create indexes"""
    try:
        # This will initialize the connection if not already done
        db = get_db()
        await mongodb_manager._ensure_indexes()
        await mongodb_manager.create_initial_admin()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Helper functions for easier access
def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance"""
    return mongodb_manager.get_database()

def get_collection(name: str) -> AsyncIOMotorCollection:
    """Get a collection from the database"""
    return mongodb_manager.get_collection(name)

async def close_connection():
    """Close the MongoDB connection"""
    await mongodb_manager.close()

@asynccontextmanager
async def get_db_session():
    """Async context manager for database sessions"""
    try:
        db = get_database()
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
