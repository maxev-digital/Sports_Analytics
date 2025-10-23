"""Test script to verify Stripe integration"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_stripe_imports():
    """Test that Stripe modules can be imported"""
    print("Testing Stripe imports...")
    try:
        from stripe_service import StripeService
        from subscription_db import SubscriptionDB
        print("✅ Stripe imports successful!")
        return True
    except Exception as e:
        print(f"❌ Stripe import failed: {e}")
        return False

def test_stripe_service():
    """Test that Stripe service can be initialized"""
    print("\nTesting Stripe service initialization...")
    try:
        from stripe_service import StripeService
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Check if Stripe keys are set
        stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
        if not stripe_key or stripe_key == 'your_stripe_secret_key_here':
            print("⚠️  Stripe secret key not configured in .env")
            return False
        
        print(f"✅ Stripe secret key configured (starts with: {stripe_key[:15]}...)")
        
        # Test creating a customer (this will fail if keys are invalid)
        print("\nTesting Stripe API connection...")
        try:
            import stripe
            stripe.api_key = stripe_key
            # Just verify the key works by listing a balance transaction
            stripe.Customer.list(limit=1)
            print("✅ Stripe API connection successful!")
            return True
        except stripe.error.AuthenticationError:
            print("❌ Stripe API key is invalid")
            return False
        except Exception as e:
            print(f"⚠️  Stripe API test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Stripe service test failed: {e}")
        return False

def test_subscription_db():
    """Test that subscription database can be initialized"""
    print("\nTesting subscription database...")
    try:
        from subscription_db import SubscriptionDB
        
        # Try to initialize tables
        SubscriptionDB.initialize_tables()
        print("✅ Subscription database initialized!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("STRIPE INTEGRATION TEST")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_stripe_imports()))
    results.append(("Service", test_stripe_service()))
    results.append(("Database", test_subscription_db()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nStripe integration is working correctly.")
        print("\nNext steps:")
        print("1. Start the backend server: cd backend\\scrapers\\nba\\backend && python main.py")
        print("2. Test the checkout endpoint with:")
        print('   Invoke-WebRequest -Uri http://localhost:8000/api/stripe/create-checkout-session -Method POST -Headers @{"Content-Type"="application/json"} -Body \'{"price_id":"price_1QR5WiGp5HWb2tPk7YVf5xHa","user_id":"test_user_123","user_email":"test@example.com"}\'')
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease review the errors above and fix the issues.")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
