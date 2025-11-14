#!/usr/bin/env python
"""Check what routes are registered in the FastAPI app"""
import sys
sys.path.insert(0, '.')

try:
    from main import app

    print("Checking influencer routes:")
    print("=" * 60)

    for route in app.routes:
        if hasattr(route, 'path') and 'influencer' in route.path:
            print(f"Path: {route.path}")
            if hasattr(route, 'methods'):
                print(f"  Methods: {route.methods}")
            if hasattr(route, 'endpoint'):
                print(f"  Endpoint: {route.endpoint.__name__}")
            print()

    print("\nTotal routes in app:", len(app.routes))

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
