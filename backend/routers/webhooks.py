# routers/webhooks.py
from fastapi import APIRouter, Request
from livekit.api import webhook as lk_webhook
import os

router = APIRouter(tags=["webhooks"])

# Загружаем .env ГЛОБАЛЬНО (или передай через main.py)
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

token_verifier = lk_webhook.TokenVerifier(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
webhook_receiver = lk_webhook.WebhookReceiver(token_verifier)

@router.post("/webhooks/caller")
async def livekit_webhook(request: Request):
    print("🔥 WEBHOOK HIT!")
    
    # LiveKit webhook ТРЕБУЕТ 2 параметра!
    body = await request.body()
    auth_header = request.headers.get("Authorization")
    
    print(f"📦 Body size: {len(body)} bytes")
    print(f"🔑 Auth header: {auth_header[:50]}...")
    
    try:
        # ✅ ПРАВИЛЬНЫЙ вызов с auth_token!
        event = webhook_receiver.receive(body, auth_header)
        room_name = event.room.name if event.room else None
        
        print(f"📡 EVENT: {event.event} | Room: {room_name}")
        return {"status": "ok", "event": event.event, "room": room_name}
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {"error": str(e)}



