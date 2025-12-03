"""
Test MongoDB connection for Avalon Pharma AI Platform
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongo import mongodb_manager, MongoDBConnectionError
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  MONGO_URI: {settings.MONGO_URI}")
    print(f"  DATABASE_NAME: {settings.DATABASE_NAME}")
    print()
    
    try:
        # Test connection
        print("Testing connection...")
        is_connected = await mongodb_manager.is_connected()
        
        if is_connected:
            print("✅ MongoDB connection successful!")
            
            # Get database info
            db = mongodb_manager.get_database()
            print(f"✅ Database '{settings.DATABASE_NAME}' accessible")
            
            # List collections
            collections = await db.list_collection_names()
            print(f"\n📊 Collections in database: {len(collections)}")
            if collections:
                for col in collections:
                    count = await db[col].count_documents({})
                    print(f"   - {col}: {count} documents")
            else:
                print("   (No collections yet - database is empty)")
            
            # Test a simple operation
            print("\n🔍 Testing database operations...")
            test_collection = db["test_connection"]
            test_doc = {"test": True, "timestamp": "2024-01-01"}
            result = await test_collection.insert_one(test_doc)
            print(f"✅ Insert test: Document ID {result.inserted_id}")
            
            # Clean up test document
            await test_collection.delete_one({"_id": result.inserted_id})
            print("✅ Delete test: Test document removed")
            
            print("\n" + "=" * 60)
            print("✅ All tests passed! MongoDB is working correctly.")
            print("=" * 60)
            return True
            
        else:
            print("❌ MongoDB connection failed!")
            print("\nTroubleshooting:")
            print("1. Make sure MongoDB is running:")
            print("   - Windows: Check Services (services.msc) for 'MongoDB'")
            print("   - Or run: net start MongoDB")
            print("2. Check if MongoDB is listening on port 27017:")
            print("   - Run: netstat -an | findstr 27017")
            print("3. Verify MONGO_URI in .env file or environment variables")
            return False
            
    except MongoDBConnectionError as e:
        print(f"❌ MongoDB Connection Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if MongoDB service is running")
        print("2. Verify MONGO_URI is correct in .env file")
        print("3. Check MongoDB logs for errors")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

