from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException
from livekit import api
from livekit.protocol import webhook as lk_webhook
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel


app = FastAPI()
load_dotenv()
# Load environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
# Инициализация Webhook Receiver для валидации LiveKit событий
token_verifier = lk_webhook.TokenVerifier(
    api_key=os.getenv("LIVEKIT_API_KEY"), 
    api_secret=os.getenv("LIVEKIT_API_SECRET")
)
webhook_receiver = lk_webhook.WebhookReceiver(token_verifier)

@app.post("/livekit/webhook")
async def livekit_webhook(request: Request):
    """ЛОВИТ РЕАЛЬНЫЕ LiveKit события (room_created, participant_connected)"""
    body = await request.body()
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization")
    
    try:
        # ✅ ВАЛИДИРУЕМ LiveKit webhook
        event = webhook_receiver.receive(body.decode(), auth_header)
        print(f"🔥 LIVEKIT EVENT: {event.event}")
        
        if event.event == "room_started":
            # 📞 НОВЫЙ ЗВОНок! Комната создана SIP dispatch
            room_name = event.room.name
            print(f"📞 SIP CALL STARTED → Room: {room_name}")
            
            # Генерируем токен для этого звонка
            token_data = generate_token_for_room(room_name)
            print(f"✅ TOKEN: {token_data}")
            
            # Сохрани в Redis/DB для frontend/agent
            await save_call_info(room_name, token_data)
            
        elif event.event == "participant_connected":
            # SIP участник подключился
            if "sip" in event.participant.identity:
                print(f"📞 SIP CONNECTED: {event.participant.identity}")
                
        elif event.event == "room_finished":
            print(f"📞 CALL ENDED: {event.room.name}")
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"status": "ok"}

def generate_token_for_room(room_name: str):
    """Генерирует токен для существующей SIP комнаты"""
    token = (
        api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
        .with_identity(f"web_{uuid.uuid4().hex[:8]}")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,  # ← ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩУЮ комнату
                can_publish=True,
                can_subscribe=True,
            )
        )
    ).to_jwt()
    
    return {
        "token": token,
        "room_name": room_name,
        "participant_identity": f"web_{uuid.uuid4().hex[:8]}",
    }

# Твой оригинальный SIP setup endpoint
@app.post("/setup-sip")
async def setup_sip():
    """ОДИН РАЗ создаёт trunks + dispatch rule"""
    lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    # Твой код создания inbound trunk + dispatch rule
    # webhook_url="https://your-domain/livekit/webhook" ← указать здесь!
    
    await lkapi.aclose()
    return {"status": "sip_configured"}

