import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Wait for initial messages
            for i in range(3):
                message = await websocket.recv()
                data = json.loads(message)
                print(f"\n📨 Message {i+1}:")
                print(f"  Type: {data.get('type')}")
                if data.get('type') == 'opportunities_update':
                    print(f"  Opportunities: {len(data.get('opportunities', []))}")

            print("\n✅ WebSocket test passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())
