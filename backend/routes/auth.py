"""Authentication routes — register, login, logout, verify, change-password"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import logging

import auth
import blocklist_check

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ========== REQUEST MODELS ==========

class LoginRequest(BaseModel):
    username: str
    password: str


class LogoutRequest(BaseModel):
    token: str


class ChangePasswordWithTokenRequest(BaseModel):
    token: str
    old_password: str
    new_password: str


# ========== ENDPOINTS ==========

@router.post("/register")
async def register(request: Request):
    """
    User registration endpoint.
    Creates new user with 14-day free trial (Semi Pro tier access).
    Optional: accepts referral code for 50% discount on first 2 months.
    """
    # Import here to avoid circular dependency at module load time
    from subscription_db import SubscriptionDB

    try:
        data = await request.json()
        full_name = data.get('full_name')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        referral_code = data.get('referral_code', '').strip()

        if not all([full_name, email, username, password]):
            raise HTTPException(status_code=400, detail="All fields required")

        if blocklist_check.is_email_blocked(email):
            logger.warning(f"Blocked email attempted registration: {email}")
            raise HTTPException(status_code=403, detail="This email is not eligible for registration")

        users = auth.load_users()
        if username in users:
            raise HTTPException(status_code=400, detail="Username already exists")

        influencer_code_valid = False
        influencer_username = None
        if referral_code:
            try:
                from influencer_system import validate_referral_code, get_influencer_by_code
                validation = validate_referral_code(referral_code)
                if validation['valid']:
                    influencer_code_valid = True
                    influencer = get_influencer_by_code(referral_code)
                    if influencer:
                        influencer_username = influencer['username']
                        logger.info(f"Valid referral code used: {referral_code} (influencer: {influencer_username})")
            except Exception as ref_error:
                logger.warning(f"Error validating referral code: {ref_error}")

        users[username] = {
            "password_hash": auth.hash_password(password),
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "full_name": full_name,
            "email": email,
            "trial_start": datetime.now().isoformat(),
            "trial_days": 14,
            "referral_code": referral_code if influencer_code_valid else None,
            "has_referral_discount": influencer_code_valid
        }
        auth.save_users(users)

        token = auth.create_session(username)

        SubscriptionDB.create_subscription(
            user_id=username,
            stripe_subscription_id=None,
            stripe_customer_id=None,
            tier="semipro",
            status="trialing"
        )

        if influencer_code_valid and influencer_username:
            try:
                from influencer_system import track_referral
                success = track_referral(
                    username=username,
                    referral_code=referral_code,
                    subscription_tier="free_trial"
                )
                if success:
                    logger.info(f"Referral tracked: {username} referred by {influencer_username}")
                else:
                    logger.warning(f"Failed to track referral for {username}")
            except Exception as track_error:
                logger.error(f"Error tracking referral: {track_error}")

        return {
            "success": True,
            "message": "Registration successful",
            "token": token,
            "username": username,
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/signup")
async def signup_email_only(request: Request):
    """
    Lightweight signup endpoint for Pricing page email capture.
    Validates email and checks if it already exists.
    """
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        if '@' not in email or '.' not in email.split('@')[1]:
            raise HTTPException(status_code=400, detail="Invalid email format")

        if blocklist_check.is_email_blocked(email):
            logger.warning(f"Blocked email attempted signup: {email}")
            raise HTTPException(status_code=403, detail="This email is not eligible for registration")

        users = auth.load_users()
        for _, user_data in users.items():
            if user_data.get('email', '').lower() == email.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered. Please log in instead."
                )

        if username and username in users:
            raise HTTPException(
                status_code=400,
                detail="Username already exists. Please choose another."
            )

        return {
            "success": True,
            "message": "Email validated successfully",
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Signup validation failed")


@router.post("/login")
async def login(request: LoginRequest):
    """User login — returns session token on success."""
    try:
        if not auth.verify_password(request.username, request.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = auth.create_session(request.username)

        users = auth.load_users()
        user_data = users.get(request.username, {})
        user_email = user_data.get('email', f"{request.username}@max-ev-sports.com")
        user_role = user_data.get('role', 'user')

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "username": request.username,
            "email": user_email,
            "role": user_role
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/logout")
async def logout(request: LogoutRequest):
    """Invalidates session token."""
    try:
        auth.delete_session(request.token)
        return {"success": True, "message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/verify")
async def verify_session(token: str):
    """Verify session token — returns username if valid, 401 if not."""
    try:
        username = auth.verify_session(token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return {"success": True, "valid": True, "username": username}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/change-password")
async def change_password(request: ChangePasswordWithTokenRequest):
    """Change user password — requires valid session token."""
    try:
        username = auth.verify_session(request.token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        success = auth.change_password(username, request.old_password, request.new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        return {"success": True, "message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password change failed")
