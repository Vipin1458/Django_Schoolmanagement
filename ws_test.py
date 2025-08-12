import asyncio
import websockets
import json

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU0OTkzMzM1LCJpYXQiOjE3NTQ5NzUzMzUsImp0aSI6ImQwMTRkM2I0YjViYzRjMjNiODgyMzViODBiZWMzMjU4IiwidXNlcl9pZCI6MzcsInVzZXJuYW1lIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.nXwjHgPKfmm8Nucs124Dr5UgYyzPQqpIrRHwtgOOZq0"
CONVERSATION_ID = 1  # Replace with an actual conversation ID in your DB

async def test_ws():
    url = f"ws://localhost:8000/ws/chat/{CONVERSATION_ID}/?token={ACCESS_TOKEN}"
    async with websockets.connect(url) as ws:
        print("✅ Connected!")

        # Send a test message
        await ws.send(json.dumps({"message": "Hello from test client"}))
        print("📤 Sent: Hello from test client")

        # Listen for incoming messages
        while True:
            msg = await ws.recv()
            print("📥 Received:", msg)

asyncio.run(test_ws())
