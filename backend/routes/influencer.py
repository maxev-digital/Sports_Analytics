"""
API Routes for Influencer Referral System
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import secrets

from influencer_system import (
    register_influencer,
    verify_influencer_credentials,
    get_influencer_by_username,
    get_influencer_referrals,
    calculate_influencer_earnings,
    validate_referral_code,
    get_all_influencers,
    update_influencer_status,
    get_influencer_by_code
)
from auth import verify_session, load_users

router = APIRouter(prefix="/api/influencer", tags=["influencer"])

# Sessions for influencer logins
influencer_sessions = {}


# ==================== REQUEST MODELS ====================

class InfluencerRegistrationRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    social_media_handle: str
    platform: str  # Twitter, Instagram, YouTube, TikTok, etc.
    follower_count: int
    custom_code: Optional[str] = None
    payment_email: Optional[EmailStr] = None


class InfluencerLoginRequest(BaseModel):
    username: str
    password: str


class ReferralCodeValidationRequest(BaseModel):
    code: str


class UpdateInfluencerStatusRequest(BaseModel):
    username: str
    status: str  # active, paused, suspended


class PartnerApplicationRequest(BaseModel):
    name: str
    email: EmailStr
    handle: str
    followers: int
    platform: str
    niche: str


# ==================== AUTH HELPERS ====================

def get_influencer_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Get influencer username from authorization token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")

    if token not in influencer_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return influencer_sessions[token]


def require_admin(authorization: Optional[str] = Header(None)) -> str:
    """Require admin authentication"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    username = verify_session(token)

    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Check if user is admin
    users = load_users()
    if username not in users or users[username].get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    return username


# ==================== PUBLIC ENDPOINTS ====================

@router.post("/register")
async def influencer_register(request: InfluencerRegistrationRequest):
    """Register a new influencer"""
    try:
        influencer_data = register_influencer(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            social_media_handle=request.social_media_handle,
            platform=request.platform,
            follower_count=request.follower_count,
            custom_code=request.custom_code,
            payment_email=request.payment_email
        )

        # Remove password hash from response
        influencer_data.pop('password_hash', None)

        return {
            "success": True,
            "message": "Influencer registered successfully",
            "data": influencer_data
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
async def influencer_login(request: InfluencerLoginRequest):
    """Login for influencers"""
    try:
        # Verify credentials
        if not verify_influencer_credentials(request.username, request.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Get influencer data
        influencer = get_influencer_by_username(request.username)
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")

        # Check if account is active
        if influencer['status'] != 'active':
            raise HTTPException(
                status_code=403,
                detail=f"Account is {influencer['status']}. Please contact support."
            )

        # Create session token
        token = secrets.token_urlsafe(32)
        influencer_sessions[token] = request.username

        # Remove sensitive data
        influencer.pop('password_hash', None)

        return {
            "success": True,
            "token": token,
            "influencer": influencer
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/logout")
async def influencer_logout(influencer_username: str = Depends(get_influencer_from_token)):
    """Logout influencer"""
    # Find and remove token
    tokens_to_remove = [
        token for token, username in influencer_sessions.items()
        if username == influencer_username
    ]

    for token in tokens_to_remove:
        del influencer_sessions[token]

    return {"success": True, "message": "Logged out successfully"}


@router.post("/validate-code")
async def validate_code(request: ReferralCodeValidationRequest):
    """Validate a referral code (public endpoint for signup page)"""
    try:
        result = validate_referral_code(request.code)
        return result

    except Exception as e:
        return {
            "valid": False,
            "message": f"Error validating code: {str(e)}"
        }


@router.post("/apply")
async def partner_apply(request: PartnerApplicationRequest):
    """Quick partner application (auto-generates account and referral code)"""
    try:
        # Generate username from email
        username = request.email.split('@')[0].lower().replace('.', '_')

        # Generate temporary password (user will reset via email)
        temp_password = secrets.token_urlsafe(16)

        # Register influencer
        influencer_data = register_influencer(
            username=username,
            email=request.email,
            password=temp_password,
            full_name=request.name,
            social_media_handle=request.handle,
            platform=request.platform,
            follower_count=request.followers,
            custom_code=None,  # Auto-generate
            payment_email=request.email
        )

        # TODO: Send welcome email with login info and referral code

        return {
            "success": True,
            "message": "Partner application received! Check your email for login details.",
            "referral_code": influencer_data['referral_code'],
            "username": username
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")


# ==================== PROTECTED ENDPOINTS (Influencer) ====================

@router.get("/dashboard")
async def get_dashboard(influencer_username: str = Depends(get_influencer_from_token)):
    """Get influencer dashboard data"""
    try:
        # Get influencer profile
        influencer = get_influencer_by_username(influencer_username)
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")

        # Get referrals
        referrals = get_influencer_referrals(influencer_username)

        # Calculate earnings
        earnings = calculate_influencer_earnings(influencer_username)

        # Remove sensitive data
        influencer.pop('password_hash', None)

        return {
            "success": True,
            "influencer": influencer,
            "referrals": referrals,
            "earnings": earnings
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dashboard: {str(e)}")


@router.get("/referrals")
async def get_referrals(influencer_username: str = Depends(get_influencer_from_token)):
    """Get list of all referrals for this influencer"""
    try:
        referrals = get_influencer_referrals(influencer_username)

        return {
            "success": True,
            "referrals": referrals,
            "total": len(referrals)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading referrals: {str(e)}")


@router.get("/earnings")
async def get_earnings(influencer_username: str = Depends(get_influencer_from_token)):
    """Get earnings breakdown for this influencer"""
    try:
        earnings = calculate_influencer_earnings(influencer_username)

        return {
            "success": True,
            "earnings": earnings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating earnings: {str(e)}")


@router.get("/profile")
async def get_profile(influencer_username: str = Depends(get_influencer_from_token)):
    """Get influencer profile"""
    try:
        influencer = get_influencer_by_username(influencer_username)
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")

        # Remove sensitive data
        influencer.pop('password_hash', None)

        return {
            "success": True,
            "influencer": influencer
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading profile: {str(e)}")


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/all")
async def get_all_influencers_admin(admin_username: str = Depends(require_admin)):
    """Get list of all influencers (admin only)"""
    try:
        influencers = get_all_influencers()

        # Calculate earnings for each
        for influencer in influencers:
            earnings = calculate_influencer_earnings(influencer['username'])
            influencer['earnings'] = earnings
            # Remove password hash
            influencer.pop('password_hash', None)

        return {
            "success": True,
            "influencers": influencers,
            "total": len(influencers)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading influencers: {str(e)}")


@router.put("/admin/status")
async def update_status_admin(
    request: UpdateInfluencerStatusRequest,
    admin_username: str = Depends(require_admin)
):
    """Update influencer status (admin only)"""
    try:
        success = update_influencer_status(request.username, request.status)

        if not success:
            raise HTTPException(status_code=404, detail="Influencer not found")

        return {
            "success": True,
            "message": f"Influencer status updated to {request.status}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.get("/admin/referral/{username}")
async def get_user_referral_info(
    username: str,
    admin_username: str = Depends(require_admin)
):
    """Get referral information for a specific user (admin only)"""
    try:
        from influencer_system import load_referrals
        referrals = load_referrals()

        if username not in referrals:
            return {
                "success": True,
                "has_referral": False,
                "message": "User did not use a referral code"
            }

        referral_data = referrals[username]

        return {
            "success": True,
            "has_referral": True,
            "referral": referral_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading referral info: {str(e)}")
