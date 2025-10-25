# 🚀 How to Start and Test the Stripe Integration

## Problem
The server keeps getting stopped before it can accept requests.

## Solution
You need to **let the server run** and test from a **separate terminal window**.

---

## Step 1: Start the Server (Keep This Window Open!)

```powershell
cd backend\scrapers\nba\backend
python main.py
```

You should see:
```
✅ Subscription database tables initialized
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**⚠️ IMPORTANT: DO NOT press Ctrl+C! Leave this window open and running!**

---

## Step 2: Open a NEW Terminal Window

Press `Win + R`, type `cmd`, press Enter (or open a new PowerShell window)

---

## Step 3: Test the Stripe Endpoint

In the NEW terminal window, run:

```powershell
curl -X POST http://localhost:8000/api/stripe/create-checkout-session ^
-H "Content-Type: application/json" ^
-d "{\"price_id\":\"price_1QR5WiGp5HWb2tPk7YVf5xHa\",\"user_id\":\"test_user\",\"user_email\":\"test@example.com\"}"
```

Or use PowerShell:

```powershell
$body = @{
    price_id = "price_1QR5WiGp5HWb2tPk7YVf5xHa"
    user_id = "test_user"
    user_email = "test@example.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/stripe/create-checkout-session" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

---

## Expected Result

You should get a JSON response like:

```json
{
  "success": true,
  "session_id": "cs_test_a1B2c3D4e5F6g7H8i9J0...",
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

**Copy the URL** and open it in your browser to see the Stripe checkout page!

---

## Troubleshooting

### "Method Not Allowed" Error
- This means the server hasn't fully started yet
- Wait 5-10 more seconds and try again
- Make sure you see "Uvicorn running on http://0.0.0.0:8000" in the server window

### Connection Refused
- The server isn't running
- Go back to Step 1 and start the server
- Make sure the server window is still open

### Server Won't Start
- Check if port 8000 is already in use:
  ```powershell
  netstat -ano | findstr :8000
  ```
- If you see a PID, kill it:
  ```powershell
  taskkill /F /PID <pid_number>
  ```

---

## Quick Test Script

Save this as `test_checkout.py` in the backend folder:

```python
import requests
import json

url = "http://localhost:8000/api/stripe/create-checkout-session"
data = {
    "price_id": "price_1QR5WiGp5HWb2tPk7YVf5xHa",
    "user_id": "test_user",
    "user_email": "test@example.com"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"\nCheckout URL:")
        print(result['url'])
        print(f"\nOpen this URL in your browser to test Stripe checkout!")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure the server is running at http://localhost:8000")
```

Then run it from a new terminal:
```powershell
python backend\scrapers\nba\backend\test_checkout.py
```

---

## 🎯 Summary

1. **Terminal 1**: Start server, leave it running
2. **Terminal 2**: Test the endpoint
3. **Browser**: Open the checkout URL you receive

That's it! The Stripe integration is ready to use. 🎉
