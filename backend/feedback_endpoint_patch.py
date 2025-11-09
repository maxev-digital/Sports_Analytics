# ========== FEEDBACK ENDPOINTS ==========
# Add this after line 807 in main.py (after password change endpoint, before Stripe)

from storage.feedback_storage import feedback_storage

class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    type: str  # bug, feature, general
    comment: str
    page: str
    timestamp: str

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    """Submit user feedback (bugs, features, general comments)"""
    try:
        # Get user_id from auth token if available, otherwise use 'anonymous'
        username = 'anonymous'
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # Decode token to get user_id
            try:
                user_data = auth.decode_token(token)
                username = user_data.get('user_id', 'anonymous')
            except:
                pass  # Keep as anonymous if token decode fails

        # Store feedback
        feedback_entry = feedback_storage.add_feedback(
            username=username,
            feedback_type=feedback.type,
            comment=feedback.comment,
            page=feedback.page,
            timestamp=feedback.timestamp
        )

        logger.info(f"Feedback received from {username}: {feedback.type} on {feedback.page}")

        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback_entry['id']
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@app.get("/api/feedback/all")
async def get_all_feedback(status: Optional[str] = None):
    """Get all feedback (admin only)"""
    try:
        feedback_list = feedback_storage.get_all_feedback(status=status)
        stats = feedback_storage.get_stats()

        return {
            "feedback": feedback_list,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")
