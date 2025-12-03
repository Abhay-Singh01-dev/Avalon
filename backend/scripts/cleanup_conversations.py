"""
Script to clean up test conversations named "New Conversation"
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pharma_ai_db")

async def cleanup_conversations():
    """Delete all conversations with title "New Conversation" """
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    conversations_collection = db["conversations"]
    messages_collection = db["messages"]
    
    try:
        # Find all conversations with "New Conversation" title
        conversations = await conversations_collection.find({
            "title": "New Conversation"
        }).to_list(length=None)
        
        print(f"Found {len(conversations)} conversations to delete")
        
        deleted_count = 0
        for conversation in conversations:
            conv_id = conversation["_id"]
            print(f"Deleting conversation: {conv_id}")
            
            # Delete associated messages
            if "messages" in conversation and conversation["messages"]:
                message_ids = []
                for msg in conversation["messages"]:
                    msg_id = msg.get("id") or msg.get("_id")
                    if msg_id:
                        message_ids.append(msg_id)
                
                if message_ids:
                    msg_result = await messages_collection.delete_many({
                        "_id": {"$in": message_ids}
                    })
                    print(f"  - Deleted {msg_result.deleted_count} messages")
            
            # Delete the conversation
            await conversations_collection.delete_one({"_id": conv_id})
            deleted_count += 1
        
        print(f"\n✅ Successfully deleted {deleted_count} conversations")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_conversations())
