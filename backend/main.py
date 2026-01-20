import asyncio  
from livekit import api
import os

from dotenv import load_dotenv

load_dotenv()

async def main():
    lkapi = api.LiveKitAPI(
    url=os.getenv("LIVEKIT_URL"),
    api_key=os.getenv("LIVEKIT_API_KEY"),
    api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )
    
  
    rules = await lkapi.sip.list_dispatch_rule(
    api.ListSIPDispatchRuleRequest()
    )
    print(f"{rules}")

    trunks = await lkapi.sip.list_inbound_trunk(
    api.ListSIPInboundTrunkRequest()
    )
    print(f"{trunks}")

    if not rules.items:
        rule = api.SIPDispatchRule(
        dispatch_rule_individual = api.SIPDispatchRuleIndividual(
        room_prefix = 'call-',
        )
        )

        request = api.CreateSIPDispatchRuleRequest(
        dispatch_rule = api.SIPDispatchRuleInfo(
            rule = rule,
            name = 'My dispatch rule',
            trunk_ids = ["ST_cConhzScJvU2"],
            room_config=api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(
                    agent_name="assistant",
                )]
            )
        )
        )

        dispatch = await lkapi.sip.create_sip_dispatch_rule(request)

        
        print("created dispatch", dispatch)
        

        await lkapi.aclose()
            
   

  

 

asyncio.run(main())



    
