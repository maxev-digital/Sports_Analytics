"""
Add /upgrade endpoint to main.py for email trial reminder flow
This endpoint receives tier selection from email and redirects to Stripe checkout
"""

UPGRADE_ENDPOINT = '''
@app.get("/upgrade")
async def upgrade_from_email(tier: str, email: str, username: str):
    """
    Upgrade endpoint for email trial reminder links
    Redirects user to Stripe checkout for selected tier

    Query params:
        - tier: starter, semipro, professional, elite, elitepro
        - email: user email
        - username: user username
    """
    try:
        # Map tier to Stripe price IDs
        STRIPE_PRICE_IDS = {
            'starter': 'price_1SNuPeR1TzxiBDhG2poLUgpO',
            'semipro': 'price_1SNuQhR1TzxiBDhG1Qe8ZwGN',
            'professional': 'price_1SNuRQR1TzxiBDhGo6UuEf6f',
            'elite': 'price_1SNuRrR1TzxiBDhG2sGWFocn',
            'elitepro': 'price_1SNuSRR1TzxiBDhGaBhjKZXJ',
        }

        tier_lower = tier.lower()

        if tier_lower not in STRIPE_PRICE_IDS:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")

        price_id = STRIPE_PRICE_IDS[tier_lower]

        # Create Stripe checkout session
        checkout_session = StripeService.create_checkout_session(
            price_id=price_id,
            user_id=username,
            user_email=email,
            success_url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/#/pricing",
            apply_beta_discount=True  # Apply EARLY50 promo code (50% OFF FOR LIFE)
        )

        # Redirect to Stripe checkout
        return RedirectResponse(url=checkout_session['url'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating upgrade checkout: {str(e)}")
        # Fallback: redirect to pricing page
        return RedirectResponse(url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/#/pricing")
'''

print("=" * 80)
print("UPGRADE ENDPOINT CODE")
print("=" * 80)
print("\nAdd this code to backend/main.py after the other subscription endpoints:")
print("\n" + UPGRADE_ENDPOINT)
print("\n" + "=" * 80)
print("IMPORTANT: Make sure to add this import at the top:")
print("from fastapi.responses import RedirectResponse")
print("=" * 80)
