#!/usr/bin/env python
"""Test script to check if influencer router can be imported"""

try:
    print("Testing influencer_system import...")
    from influencer_system import register_influencer
    print("[OK] influencer_system imported successfully")
except Exception as e:
    print(f"[ERROR] Error importing influencer_system: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting routes.influencer import...")
    from routes.influencer import router
    print(f"[OK] Influencer router imported successfully")
    print(f"  Router prefix: {router.prefix}")
    print(f"  Router tags: {router.tags}")
    print(f"  Number of routes: {len(router.routes)}")
except Exception as e:
    print(f"[ERROR] Error importing routes.influencer: {e}")
    import traceback
    traceback.print_exc()

print("\n[TEST COMPLETE]")
