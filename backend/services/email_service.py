"""
Email Service — direct SMTP via Outlook/Microsoft 365.

Usage:
    from services.email_service import send_email, send_welcome, send_admin_alert

Fire-and-forget: never throws to callers, always logs.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "info@max-ev-sports.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "info@max-ev-sports.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Max EV Sports")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "gte.apw@gmail.com")
SITE_URL = os.getenv("WEBSITE_URL", "https://max-ev-sports.com")


def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    from_name: Optional[str] = None,
) -> bool:
    """Send a single email via SMTP. Returns True on success, False on failure."""
    if not SMTP_PASS:
        logger.warning("SMTP_PASS not set — email disabled")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name or SMTP_FROM_NAME} <{SMTP_FROM}>"
        msg["To"] = to

        if text:
            msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Email failed to %s: %s", to, exc)
        return False


# ── Brand styles ─────────────────────────────────────────────────────────────

_WRAPPER = """
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
            max-width:600px;margin:0 auto;padding:0;background:#0f172a;color:#e2e8f0">
  <div style="padding:24px 32px;border-bottom:2px solid #1e40af">
    <img src="{site}/3DMaxLogo.png" alt="Max EV Sports" style="height:48px" />
  </div>
  <div style="padding:32px">
    {body}
  </div>
  <div style="padding:16px 32px;border-top:1px solid #1e293b;font-size:12px;color:#64748b;text-align:center">
    Max EV Sports · max-ev-sports.com
  </div>
</div>
""".replace("{site}", SITE_URL)

_BTN = (
    '<a href="{url}" style="display:inline-block;background:#2563eb;color:#fff;'
    'padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;'
    'font-size:15px;margin:16px 0">{label}</a>'
)


# ── Template builders ────────────────────────────────────────────────────────

def send_welcome(email: str, full_name: str, username: str) -> bool:
    """Welcome email on signup."""
    first = full_name.split()[0] if full_name else "there"
    body = f"""
    <h2 style="color:#fff;margin:0 0 16px">Welcome to Max EV Sports, {first}!</h2>
    <p style="color:#94a3b8;line-height:1.7">
      Your account <strong style="color:#fff">{username}</strong> is ready.
      You have full access to live odds, matchup analysis, power ratings, and AI-powered insights
      across NFL, CFB, MLB, NBA, and NHL.
    </p>
    {_BTN.format(url=SITE_URL + '/#/live-games', label='Open Your Dashboard')}
    <p style="color:#64748b;font-size:13px;margin-top:24px">
      Questions? Reply to this email — we read every one.
    </p>
    """
    return send_email(
        to=email,
        subject="Welcome to Max EV Sports",
        html=_WRAPPER.replace("{body}", body),
        text=f"Hi {first}, welcome to Max EV Sports! Your username is {username}. "
             f"Access your dashboard at {SITE_URL}",
    )


def send_trial_reminder(email: str, full_name: str, days_left: int) -> bool:
    """Trial expiry reminder."""
    first = full_name.split()[0] if full_name else "there"
    urgency = "expires tomorrow" if days_left <= 1 else f"expires in {days_left} days"
    body = f"""
    <h2 style="color:#fff;margin:0 0 16px">Your trial {urgency}</h2>
    <p style="color:#94a3b8;line-height:1.7">
      Hi {first}, your Max EV Sports trial {urgency}.
      Upgrade now to keep access to AI analysis, power ratings, injury intelligence,
      and all pro features.
    </p>
    {_BTN.format(url=SITE_URL + '/#/pricing', label='View Plans')}
    <p style="color:#64748b;font-size:13px;margin-top:24px">
      Have questions about which plan is right for you? Just reply to this email.
    </p>
    """
    return send_email(
        to=email,
        subject=f"Your Max EV Sports trial {urgency}",
        html=_WRAPPER.replace("{body}", body),
    )


def send_password_reset(email: str, reset_token: str) -> bool:
    """Password reset link."""
    reset_url = f"{SITE_URL}/#/reset-password?token={reset_token}"
    body = f"""
    <h2 style="color:#fff;margin:0 0 16px">Reset Your Password</h2>
    <p style="color:#94a3b8;line-height:1.7">
      We received a request to reset your password. Click below to set a new one.
      This link expires in 1 hour.
    </p>
    {_BTN.format(url=reset_url, label='Reset Password')}
    <p style="color:#64748b;font-size:13px;margin-top:24px">
      If you didn't request this, ignore this email — your password won't change.
    </p>
    """
    return send_email(
        to=email,
        subject="Reset your Max EV Sports password",
        html=_WRAPPER.replace("{body}", body),
    )


def send_admin_alert(alert_type: str, details: dict) -> bool:
    """Send admin notification (signup, payment, etc.)."""
    if alert_type == "signup":
        subject = f"New Signup: {details.get('username', '?')}"
        body = f"""
        <h2 style="color:#fff;margin:0 0 16px">New User Signup</h2>
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:8px;color:#64748b">Name</td>
              <td style="padding:8px;color:#fff;font-weight:600">{details.get('full_name', '?')}</td></tr>
          <tr><td style="padding:8px;color:#64748b">Email</td>
              <td style="padding:8px;color:#fff">{details.get('email', '?')}</td></tr>
          <tr><td style="padding:8px;color:#64748b">Username</td>
              <td style="padding:8px;color:#fff">{details.get('username', '?')}</td></tr>
          <tr><td style="padding:8px;color:#64748b">Referral</td>
              <td style="padding:8px;color:#fff">{details.get('referral_code', 'none')}</td></tr>
        </table>
        """
    elif alert_type == "payment":
        subject = f"Payment: ${details.get('amount', 0):.2f} from {details.get('email', '?')}"
        body = f"""
        <h2 style="color:#22c55e;margin:0 0 16px">Payment Received</h2>
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:8px;color:#64748b">Email</td>
              <td style="padding:8px;color:#fff">{details.get('email', '?')}</td></tr>
          <tr><td style="padding:8px;color:#64748b">Tier</td>
              <td style="padding:8px;color:#22c55e;font-weight:700">{details.get('tier', '?')}</td></tr>
          <tr><td style="padding:8px;color:#64748b">Amount</td>
              <td style="padding:8px;color:#22c55e;font-weight:700">${details.get('amount', 0):.2f}</td></tr>
        </table>
        """
    else:
        subject = f"Admin Alert: {alert_type}"
        body = f"<pre style='color:#e2e8f0'>{details}</pre>"

    return send_email(
        to=ADMIN_EMAIL,
        subject=subject,
        html=_WRAPPER.replace("{body}", body),
    )


def send_custom(to: str, subject: str, body_html: str) -> bool:
    """Send a custom email from admin panel compose."""
    return send_email(
        to=to,
        subject=subject,
        html=_WRAPPER.replace("{body}", body_html),
    )
