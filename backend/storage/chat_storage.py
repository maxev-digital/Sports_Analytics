"""
Live chat storage module for user support conversations
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Setup paths
CHAT_DIR = Path(__file__).parent.parent / 'data' / 'chat'
CHAT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatStorage:
    """Handles storage and retrieval of chat conversations"""

    def __init__(self):
        self.chat_dir = CHAT_DIR

    def _get_user_chat_file(self, username: str) -> Path:
        """Get the chat file path for a specific user"""
        safe_username = username.replace('/', '_').replace('\\', '_')
        chat_file = self.chat_dir / f"{safe_username}_chat.json"

        # Initialize file if it doesn't exist
        if not chat_file.exists():
            chat_file.write_text(json.dumps({
                'username': username,
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'last_message_at': None
            }, indent=2))

        return chat_file

    def add_message(
        self,
        username: str,
        sender: str,  # 'user' or 'admin'
        message: str,
        timestamp: Optional[str] = None
    ) -> Dict:
        """Add a new message to user's chat"""
        try:
            chat_file = self._get_user_chat_file(username)

            # Load existing chat
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)

            # Create new message entry
            message_entry = {
                'id': self._generate_message_id(),
                'sender': sender,
                'message': message,
                'timestamp': timestamp or datetime.now().isoformat()
            }

            # Add to messages
            chat_data['messages'].append(message_entry)
            chat_data['last_message_at'] = message_entry['timestamp']

            # Save
            with open(chat_file, 'w') as f:
                json.dump(chat_data, f, indent=2)

            logger.info(f"Chat message added for {username} from {sender}")
            return message_entry

        except Exception as e:
            logger.error(f"Error adding chat message for {username}: {e}")
            raise

    def get_messages(self, username: str) -> List[Dict]:
        """Get all messages for a user"""
        try:
            chat_file = self._get_user_chat_file(username)

            with open(chat_file, 'r') as f:
                chat_data = json.load(f)

            return chat_data.get('messages', [])

        except Exception as e:
            logger.error(f"Error retrieving messages for {username}: {e}")
            return []

    def get_all_conversations(self) -> List[Dict]:
        """Get all active conversations (Admin view)"""
        try:
            conversations = []

            for chat_file in self.chat_dir.glob('*_chat.json'):
                try:
                    with open(chat_file, 'r') as f:
                        chat_data = json.load(f)

                    # Get last message info
                    messages = chat_data.get('messages', [])
                    last_message = messages[-1] if messages else None

                    # Count unread messages (messages from user since last admin response)
                    unread_count = 0
                    for msg in reversed(messages):
                        if msg['sender'] == 'admin':
                            break
                        if msg['sender'] == 'user':
                            unread_count += 1

                    conversations.append({
                        'username': chat_data['username'],
                        'message_count': len(messages),
                        'last_message': last_message,
                        'last_message_at': chat_data.get('last_message_at'),
                        'unread_count': unread_count,
                        'created_at': chat_data.get('created_at')
                    })

                except Exception as e:
                    logger.error(f"Error reading chat file {chat_file}: {e}")
                    continue

            # Sort by last message time (newest first)
            conversations.sort(key=lambda x: x.get('last_message_at', ''), reverse=True)

            return conversations

        except Exception as e:
            logger.error(f"Error getting all conversations: {e}")
            return []

    def get_conversation(self, username: str) -> Dict:
        """Get full conversation for a specific user (Admin view)"""
        try:
            chat_file = self._get_user_chat_file(username)

            with open(chat_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error getting conversation for {username}: {e}")
            return {'username': username, 'messages': []}

    def mark_as_read(self, username: str) -> bool:
        """Mark conversation as read by admin"""
        try:
            # This could be extended to track read status
            # For now, just log it
            logger.info(f"Conversation with {username} marked as read")
            return True

        except Exception as e:
            logger.error(f"Error marking conversation as read: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get chat statistics"""
        try:
            conversations = self.get_all_conversations()

            total_conversations = len(conversations)
            total_messages = sum(c.get('message_count', 0) for c in conversations)
            total_unread = sum(c.get('unread_count', 0) for c in conversations)

            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_unread': total_unread,
                'active_conversations': len([c for c in conversations if c.get('unread_count', 0) > 0])
            }

        except Exception as e:
            logger.error(f"Error getting chat stats: {e}")
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'total_unread': 0,
                'active_conversations': 0
            }

    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"msg_{timestamp}"


# Global instance
chat_storage = ChatStorage()
