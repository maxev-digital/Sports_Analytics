"""
X API Client
Handles authentication and API calls for DM sending
Requires Elevated Access (https://developer.x.com/en/portal/dashboard)
"""
import sys
from pathlib import Path
from datetime import datetime

# Handle both direct execution and module import
try:
    from .config import (
        X_API_KEY,
        X_API_SECRET,
        X_ACCESS_TOKEN,
        X_ACCESS_SECRET,
        X_BEARER_TOKEN
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from x_campaign.config import (
        X_API_KEY,
        X_API_SECRET,
        X_ACCESS_TOKEN,
        X_ACCESS_SECRET,
        X_BEARER_TOKEN
    )

try:
    import tweepy
except ImportError:
    tweepy = None
    print("[WARN] tweepy not installed. Run: pip install tweepy")

class XClient:
    """Wrapper for X API v2 with Tweepy"""

    def __init__(self):
        """Initialize Tweepy client with OAuth 1.0a credentials"""
        if tweepy is None:
            raise ImportError("tweepy package required. Run: pip install tweepy")

        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
            raise ValueError(
                "Missing X API credentials. Please add to backend/.env:\n"
                "X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET"
            )

        # OAuth 1.0a authentication (required for DMs)
        self.client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        print("[OK] X API client initialized")

    def send_dm(self, recipient_handle, message):
        """
        Send a direct message to a user

        Args:
            recipient_handle: X handle (with or without @)
            message: Text to send

        Returns:
            dict: {success: bool, dm_id: str, error: str}
        """
        try:
            # Clean handle
            handle = recipient_handle.replace('@', '')

            # Get user ID from handle
            user = self.client.get_user(username=handle)
            if not user or not user.data:
                return {
                    'success': False,
                    'error': f"User @{handle} not found"
                }

            recipient_id = user.data.id

            # Send DM via API v2
            response = self.client.create_direct_message(
                participant_id=recipient_id,
                text=message
            )

            dm_id = response.data['dm_event_id'] if response.data else None

            return {
                'success': True,
                'dm_id': dm_id,
                'sent_at': datetime.utcnow().isoformat()
            }

        except tweepy.TweepyException as e:
            error_msg = str(e)

            # Handle specific errors
            if '403' in error_msg:
                error_msg = "Cannot send DM - user may have DMs disabled or blocked you"
            elif '429' in error_msg:
                error_msg = "Rate limit exceeded - wait before sending more DMs"
            elif '401' in error_msg:
                error_msg = "Authentication failed - check API credentials"

            return {
                'success': False,
                'error': error_msg
            }

    def get_dms(self, max_results=50):
        """
        Get recent DMs
        Used to check for replies from partners

        Returns:
            list: Recent DM conversations
        """
        try:
            # Get DM events
            response = self.client.get_direct_message_events(
                max_results=max_results
            )

            if not response or not response.data:
                return []

            dms = []
            for dm in response.data:
                dms.append({
                    'id': dm.id,
                    'text': dm.text,
                    'sender_id': dm.sender_id,
                    'created_at': dm.created_at
                })

            return dms

        except tweepy.TweepyException as e:
            print(f"❌ Error fetching DMs: {e}")
            return []

    def get_user_info(self, handle):
        """
        Get user profile information
        Useful for verifying follower count and engagement

        Args:
            handle: X handle (with or without @)

        Returns:
            dict: User profile data
        """
        try:
            handle = handle.replace('@', '')

            user = self.client.get_user(
                username=handle,
                user_fields=['public_metrics', 'description', 'verified']
            )

            if not user or not user.data:
                return None

            metrics = user.data.public_metrics

            return {
                'id': user.data.id,
                'handle': user.data.username,
                'name': user.data.name,
                'followers': metrics['followers_count'],
                'following': metrics['following_count'],
                'tweets': metrics['tweet_count'],
                'verified': user.data.verified,
                'bio': user.data.description
            }

        except tweepy.TweepyException as e:
            print(f"❌ Error fetching user info: {e}")
            return None

    def verify_credentials(self):
        """Test API credentials"""
        try:
            # Get authenticated user info
            me = self.client.get_me()
            if me and me.data:
                print(f"[OK] Authenticated as: @{me.data.username}")
                return True
            return False
        except tweepy.TweepyException as e:
            print(f"[ERROR] Authentication failed: {e}")
            return False

# Singleton instance
_client_instance = None

def get_client():
    """Get or create X API client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = XClient()
    return _client_instance

if __name__ == "__main__":
    print("X API Client Test")
    print("=" * 50)

    try:
        client = XClient()

        # Test authentication
        print("\nTesting authentication...")
        if client.verify_credentials():
            print("[OK] Authentication successful")
        else:
            print("[ERROR] Authentication failed")
            exit(1)

        # Test getting user info
        print("\nFetching test user info...")
        user_info = client.get_user_info("elonmusk")
        if user_info:
            print(f"[OK] User: @{user_info['handle']}")
            print(f"   Followers: {user_info['followers']:,}")
            print(f"   Verified: {user_info['verified']}")

    except (ValueError, ImportError) as e:
        print(f"\n[WARN] {e}")
        print("\nTo test the X client:")
        print("1. Apply for X API Elevated Access")
        print("2. Add credentials to backend/.env")
        print("3. Run this test again")
