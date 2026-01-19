import os
import time
import json
from livekit import api
from livekit.api import webhook as lk_webhook
from fastapi import Request, APIRouter

router = APIRouter(tags=["webhooks"])

# LiveKit ключи
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://livekit.alifdent.online")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

token_verifier = lk_webhook.TokenVerifier(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
webhook_receiver = lk_webhook.WebhookReceiver(token_verifier)

@router.post("/webhooks/caller")
async def sip_caller_webhook(request: Request):
    try:
        event = await webhook_receiver.receive(request)
        
        if event.event == "sip_participant_created":
            caller_number = event.sip_participant.identity  # "79853841837"
            
            print(f"📞 CALLER: +7{caller_number}")
            
            # ✅ Создаём SIP trunk ТОЛЬКО для этого caller'а
            trunk_id = await create_caller_sip_trunk(caller_number)
            
            room_name = f"call-{caller_number}"
            print(f"✅ Trunk: {trunk_id} → Room: {room_name}")
            
        return {"status": "caller_trunk_created"}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

async def create_caller_sip_trunk(caller: str) -> str:
    """Создаёт SIP inbound trunk с allowed_numbers=[caller]"""
    lkapi = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET
    )
    
    try:
        # ✅ SIP TRUNK с allowed_numbers=[caller]
        trunk_info = api.SIPInboundTrunkInfo(
            name=f"trunk-{caller}",
            numbers=["+74992130459"],        # Твой номер (куда звонят)
            allowed_numbers=[f"+7{caller}"], # ✅ ТОЛЬКО этот caller!
            krisp_enabled=True
        )
        
        request = api.CreateSIPInboundTrunkRequest(trunk=trunk_info)
        trunk = await lkapi.sip.create_inbound_trunk(request)
        
        print(f"✅ SIP Trunk создан: {trunk.sip_trunk_id}")
        print(f"   allowed_numbers: +7{caller}")
        
        # ✅ Создаём dispatch rule для этого trunk
        await create_dispatch_for_trunk(trunk.sip_trunk_id, caller)
        
        return trunk.sip_trunk_id
        
    finally:
        await lkapi.aclose()

async def create_dispatch_for_trunk(trunk_id: str, caller: str):
    """Dispatch rule для нового trunk"""
    lkapi = api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
    
    try:
        dispatch = await lkapi.sip.create_sip_dispatch_rule(
            api.CreateSIPDispatchRuleRequest(
                trunk_ids=[trunk_id],
                rule=api.SIPDispatchRule(
                    dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                        room_prefix=f"call-{caller}-"
                    )
                ),
                name=f"dispatch-{caller}",
                room_config=api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name="livekit-agent")]
                )
            )
        )
        print(f"✅ {dispatch} rule для {trunk_id}")
        
    finally:
        await lkapi.aclose()

# Health check
@router.get("/health")
async def health():
    return {"status": "ok", "caller_webhook": "ready"}
