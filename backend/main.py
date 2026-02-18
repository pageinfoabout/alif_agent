# provisioning.py
import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")


async def ensure_sip_setup():
    lkapi = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    # Get or create inbound trunk
    trunks = await lkapi.sip.list_inbound_trunk(api.ListSIPInboundTrunkRequest())
    print(f"Trunks: {trunks}")

    if trunks.items:
        in_trunk = trunks.items[0]
        in_trunk_id = in_trunk.sip_trunk_id
        print(f"Using existing inbound trunk: {in_trunk_id}")
    else:
        in_trunk = api.SIPInboundTrunkInfo(
            name="inbound_call",
            numbers=["+74992130459"],
            krisp_enabled=True,
        )
        request = api.CreateSIPInboundTrunkRequest(trunk=in_trunk)
        inbound_trunk = await lkapi.sip.create_sip_inbound_trunk(request)
        in_trunk_id = inbound_trunk.sip_trunk_id
        print(f"Created inbound trunk: {in_trunk_id}")

    # Get or create dispatch rule
    rules = await lkapi.sip.list_dispatch_rule(api.ListSIPDispatchRuleRequest())
    print(f"Rules: {rules}")

    if not rules.items:
        rule = api.SIPDispatchRule(
            dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                room_prefix="call-"
            )
        )

        request = api.CreateSIPDispatchRuleRequest(
            dispatch_rule=api.SIPDispatchRuleInfo(
                rule=rule,
                name="My dispatch rule",
                trunk_ids=[in_trunk_id],
                room_config=api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name="assistant")]
                ),
            )
        )

        dispatch = await lkapi.sip.create_sip_dispatch_rule(request)
        print("Created dispatch:", dispatch)
    else:
        print("Dispatch rule already exists")

    await lkapi.aclose()


async def periodic_provisioning(interval_seconds: int = 6 * 60 * 60):
    """
    Run ensure_sip_setup() every interval_seconds in an infinite loop.
    Default: every 6 hours, with console countdown.
    """
    while True:
        try:
            print("Running SIP provisioning...")
            await ensure_sip_setup()
            print("SIP provisioning finished.")
        except Exception as e:
            print(f"SIP provisioning failed: {e}")

        remaining = interval_seconds
        while remaining > 0:
            minutes, seconds = divmod(remaining, 60)
            # \r – перезаписываем строку, end="" – без переноса
            print(
                f"Next SIP provisioning in {minutes:02d}:{seconds:02d} (mm:ss)...",
                end="\r",
                flush=True,
            )
            await asyncio.sleep(1)
            remaining -= 1

        # Чистый перенос строки после окончания отсчёта
        print()


if __name__ == "__main__":
    # Запуск: python provisioning.py
    # Скрипт будет крутиться вечно и вызывать ensure_sip_setup() раз в 6 часов.
    asyncio.run(periodic_provisioning())
