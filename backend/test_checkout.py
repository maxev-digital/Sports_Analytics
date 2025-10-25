"""Test script for Stripe checkout endpoint"""
import requests
import json

def test_checkout():
    """Test the Stripe checkout endpoint"""
    
    url = "http://localhost:8000/api/stripe/create-checkout-session"
    data = {
        "price_id": "price_1QR5WiGp5HWb2tPk7YVf5xHa",
        "user_id": "test_user",
        "user_email": "test@example.com"
    }

    print("=" * 60)
    print("TESTING STRIPE CHECKOUT ENDPOINT")
    print("=" * 60)
    print(f"\nURL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(url, json=data)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 60)
            print("✅ SUCCESS!")
            print("=" * 60)
            print(f"\nSession ID: {result['session_id']}")
            print(f"\nCheckout URL:")
            print(result['url'])
            print("\n📋 Copy the URL above and open it in your browser!")
            print("You'll see the Stripe checkout page for the Pro subscription.")
            print("\nTest with card: 4242 4242 4242 4242")
            print("Any future date, any CVC")
            print("=" * 60)
            return True
        else:
            print("\n❌ Request failed!")
            print("Check the error message above.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR!")
        print("\nThe server is not running at http://localhost:8000")
        print("\nTo fix this:")
        print("1. Open a new terminal window")
        print("2. Run: cd backend\\scrapers\\nba\\backend")
        print("3. Run: python main.py")
        print("4. Wait for 'Uvicorn running on http://0.0.0.0:8000'")
        print("5. Run this test script again")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("1. The server is running")
        print("2. You have 'requests' installed: pip install requests")
        return False

if __name__ == "__main__":
    success = test_checkout()
    exit(0 if success else 1)
