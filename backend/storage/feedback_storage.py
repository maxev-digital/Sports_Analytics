"""
Feedback storage module for user feedback and bug reports
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Setup paths
FEEDBACK_DIR = Path(__file__).parent.parent / 'data' / 'feedback'
FEEDBACK_FILE = FEEDBACK_DIR / 'user_feedback.json'

# Ensure directory exists
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

# Initialize file if it doesn't exist
if not FEEDBACK_FILE.exists():
    FEEDBACK_FILE.write_text('[]')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackStorage:
    """Handles storage and retrieval of user feedback"""

    def __init__(self):
        self.feedback_file = FEEDBACK_FILE

    def add_feedback(
        self,
        username: str,
        feedback_type: str,
        comment: str,
        page: str,
        timestamp: Optional[str] = None
    ) -> Dict:
        """Add new feedback entry"""
        try:
            # Load existing feedback
            feedback_list = self._load_feedback()

            # Create new feedback entry
            feedback_entry = {
                'id': self._generate_id(),
                'username': username,
                'type': feedback_type,  # bug, feature, general
                'comment': comment,
                'page': page,
                'timestamp': timestamp or datetime.now().isoformat(),
                'status': 'new',  # new, reviewed, resolved
                'admin_notes': ''
            }

            # Add to list
            feedback_list.append(feedback_entry)

            # Save
            self._save_feedback(feedback_list)

            logger.info(f"Feedback added: {feedback_entry['id']} from {username} ({feedback_type})")
            return feedback_entry

        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            raise

    def get_all_feedback(self, status: Optional[str] = None) -> List[Dict]:
        """Get all feedback, optionally filtered by status"""
        try:
            feedback_list = self._load_feedback()

            if status:
                feedback_list = [f for f in feedback_list if f.get('status') == status]

            # Sort by timestamp (newest first)
            feedback_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return feedback_list

        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            return []

    def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """Get specific feedback entry by ID"""
        try:
            feedback_list = self._load_feedback()
            for feedback in feedback_list:
                if feedback.get('id') == feedback_id:
                    return feedback
            return None
        except Exception as e:
            logger.error(f"Error retrieving feedback {feedback_id}: {e}")
            return None

    def update_feedback_status(
        self,
        feedback_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update feedback status and optionally add admin notes"""
        try:
            feedback_list = self._load_feedback()

            for feedback in feedback_list:
                if feedback.get('id') == feedback_id:
                    feedback['status'] = status
                    if admin_notes:
                        feedback['admin_notes'] = admin_notes
                    feedback['updated_at'] = datetime.now().isoformat()

                    self._save_feedback(feedback_list)
                    logger.info(f"Feedback {feedback_id} updated to status: {status}")
                    return True

            logger.warning(f"Feedback {feedback_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error updating feedback {feedback_id}: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get feedback statistics"""
        try:
            feedback_list = self._load_feedback()

            total = len(feedback_list)
            by_type = {}
            by_status = {}

            for feedback in feedback_list:
                # Count by type
                feedback_type = feedback.get('type', 'unknown')
                by_type[feedback_type] = by_type.get(feedback_type, 0) + 1

                # Count by status
                status = feedback.get('status', 'new')
                by_status[status] = by_status.get(status, 0) + 1

            return {
                'total': total,
                'by_type': by_type,
                'by_status': by_status
            }

        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {'total': 0, 'by_type': {}, 'by_status': {}}

    def _load_feedback(self) -> List[Dict]:
        """Load feedback from JSON file"""
        try:
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Feedback file corrupted, resetting...")
            return []
        except Exception as e:
            logger.error(f"Error loading feedback: {e}")
            return []

    def _save_feedback(self, feedback_list: List[Dict]):
        """Save feedback to JSON file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(feedback_list, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise

    def _generate_id(self) -> str:
        """Generate unique feedback ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"feedback_{timestamp}"


# Global instance
feedback_storage = FeedbackStorage()
