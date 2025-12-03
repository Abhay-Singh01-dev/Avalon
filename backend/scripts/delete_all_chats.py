"""Delete all conversations via API"""
import requests
import sys

def delete_all_chats():
    """Delete all chats by fetching list and deleting each one"""
    base_url = "http://localhost:8000/api"
    
    try:
        # Get all chats
        response = requests.get(f"{base_url}/chats")
        if response.status_code != 200:
            print(f"❌ Failed to fetch chats: {response.status_code}")
            return
        
        chats = response.json()
        print(f"Found {len(chats)} chats")
        
        # Delete each chat
        deleted_count = 0
        for chat in chats:
            chat_id = chat.get('id')
            if chat_id:
                del_response = requests.delete(f"{base_url}/chats/{chat_id}")
                if del_response.status_code in [200, 204]:
                    deleted_count += 1
                    print(f"✅ Deleted chat: {chat.get('title', chat_id)}")
                else:
                    print(f"❌ Failed to delete {chat_id}: {del_response.status_code}")
        
        print(f"\n✅ Successfully deleted {deleted_count} conversations")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure the backend is running at http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    delete_all_chats()
