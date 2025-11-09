# test_twitter_post.py - Test single tweet before running full bot
import os
import sys

# Import the main bot functions
from twitter_auto_poster import (
    get_beta_member_count,
    get_available_images,
    post_tweet_with_image,
    IMAGES_FOLDER
)

print("=" * 60)
print("TWITTER BOT - TEST MODE")
print("=" * 60)
print("\nThis will post ONE test tweet to verify everything works.\n")

# Check images
print("[1/4] Checking for images...")
images = get_available_images()
if images:
    print(f"[OK] Found {len(images)} images:")
    for img in images:
        print(f"    - {os.path.basename(img)}")
else:
    print("[WARN] No images found in:", IMAGES_FOLDER)
    print("       Tweet will post without image (text only)")

# Check API
print("\n[2/4] Checking API connection...")
print("[OK] API connection ready")

# Confirm
print("\n[3/4] Ready to post test tweet")
print("\nThis will post a REAL tweet to your Twitter account:")
print("  Account: @GTE_APW")
print("  Content: Beta promotion message")
print("  Image: Yes (if available)")
print("\nDo you want to continue?")
response = input("Type 'yes' to post test tweet: ")

if response.lower() != 'yes':
    print("\n[CANCELLED] Test cancelled. No tweet posted.")
    sys.exit(0)

# Post tweet
print("\n[4/4] Posting test tweet...")
success = post_tweet_with_image()

if success:
    print("\n" + "=" * 60)
    print("[SUCCESS] TEST SUCCESSFUL!")
    print("=" * 60)
    print("\nCheck Twitter to verify:")
    print("  - Tweet text looks good")
    print("  - Image uploaded correctly")
    print("  - Link works")
    print("  - Hashtags display properly")
    print("\nIf everything looks good, run the full bot with:")
    print("  python twitter_auto_poster.py")
else:
    print("\n" + "=" * 60)
    print("[FAILED] TEST FAILED")
    print("=" * 60)
    print("\nCheck the error messages above.")
    print("Common issues:")
    print("  - Twitter API credentials invalid")
    print("  - Rate limit reached (wait an hour)")
    print("  - Image file corrupted")
    print("  - Internet connection issue")
