from pathlib import Path

from livekit import api
from livekit.api import DeleteRoomRequest
from livekit.agents.beta.workflows.dtmf_inputs import GetDtmfTask
import logging
import pytz
import datetime
import aiohttp
import json
from dataclasses import dataclass, field
from typing import Optional
from typing import List
from dotenv import load_dotenv
from livekit.protocol import sip as proto_sip

from livekit.agents import (
    Agent,
    function_tool,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    room_io,
)
from livekit.plugins import deepgram, openai, silero

from datetime import datetime
from tools import  get_date, get_services, get_time
from tts_silero import LocalSileroTTS 
import os


logger = logging.getLogger("agent")
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# check if storage already exists
THIS_DIR = Path(__file__).parent
# Load environment variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

server = AgentServer()

@dataclass
class UserData:
    
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    phone: str | None = None
    room: str | None = None
    participant_identity: str | None = None 

    def summarize(self) -> str:
        return "Пациент и информация о сессии."

RunContext_T = RunContext[UserData]

print(RunContext_T)

class Main_Agent(Agent):
    @function_tool
    async def end_call(self, ctx: RunContext[UserData]) -> None:
        
        """
        Вызывается если пациент сказал до свидания или хочет завершить звонок.
        
        """
        
        lkapi = api.LiveKitAPI(
                url=LIVEKIT_URL,
                api_key=LIVEKIT_API_KEY,
                api_secret=LIVEKIT_API_SECRET,
            )
        await self.session.generate_reply(user_input="До свидания!")
        await lkapi.room.delete_room(DeleteRoomRequest(
            
        room=ctx.userdata.room,
        
        ))
        print(f"🔔Звонок в комнате {ctx.userdata.room} завершен.")
     
    @function_tool
    async def transfer_call(self, ctx: RunContext[UserData]) -> None:
        """
        Вызывается для перевода звонка на менеджера.
        """
        userdata = ctx.userdata
        # парсим и сохраняем услугу в userdata
        participant_identity = userdata.participant_identity
        transfer_to = "sip:79150628917@sip.your-provider.com"
        room = userdata.room
        print(f"Transferring call for participant {participant_identity} to {transfer_to}")

        try:
           
            livekit_url = LIVEKIT_URL
            api_key = LIVEKIT_API_KEY
            api_secret = LIVEKIT_API_SECRET
            userdata.livekit_api = api.LiveKitAPI(
                url=livekit_url,
                api_key=api_key,
                api_secret=api_secret
            )
            transfer_request = proto_sip.TransferSIPParticipantRequest(
            participant_identity=participant_identity,
            room_name=room,
            transfer_to=transfer_to,  # ← строка "79150628917"
            play_dialtone=True
        )
            await self.session.generate_reply(user_input="Перевожу на менеджера")
            await userdata.livekit_api.sip.transfer_sip_participant(transfer_request) 
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {e}", exc_info=True)
            await self.session.generate_reply(user_input="Извините, cкорее всего все менеджеры заняты. Чем ещё могу помочь?")


    @function_tool
    async def create_booking(
        self, 
        ctx: RunContext[UserData],
        name: str,
        service_ids: List[int],
        date_and_time: str,
        resource_id: int = None
    ) -> str:
        
        """
            Ты вызываешь функцию создания записи только после того как пользователь подтвердил данные и сказал "да"
            если пользователь сказал "нет", то НЕ вызывай функцию.

            Перед вызовом функции ты ОБЯЗАН убедиться, что получены все обязательные данные.

            ---

            # Обязательные поля (без них функцию вызывать нельзя)

            1. name — имя пациента
            2. phone — sip_caller_phone
            3. date_and_time — дата и время приёма
            5. services_ids — номер услуги
            6. resource_id - номер врача
        ---

            # Формат услуги (services)
        
            В массиве services должна быть минимум одна услуга.

            ---

            # Логика работы

            1. Собери данные у пациента пошагово
            2. Повтори данные перед созданием записи
            3. Только после подтверждения пациента вызывай функцию
            4. Передай все данные строго в соответствии со схемой

            ---

            # Пример подтверждения перед вызовом функции

            "Подтверждаю запись:
            Имя - Анна  
            Дата - 15 января  
            Время - 14:00  
            Услуга - Лечение кариеса  
            Купон - без купона  

            Всё верно?"

            ---

        """
        userdata = ctx.userdata
      
        phone = userdata.phone

        print(f"телефон", phone)
        
        url = "https://crmexchange.1denta.ru/api/v2/visit"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjU1MjksImFwaUtleSI6InRuTUU1OHVNbXVZQjBUS01FN3JDIiwib3JnSWQiOjEwNDg0LCJuYW1lIjoi0KPQvNCw0YDQsdC10LrQvtCyINCa0LDQvdCw0YLQsdC10Log0KPQvNCw0YDQsdC10LrQvtCy0LjRhyIsInBob25lIjoiKzcoOTk5KTg1MS02Ni05MiIsImVtYWlsIjoiYWxpZmRlbnRtb3Njb3dAZ21haWwuY29tIiwiaWF0IjoxNzcxMjQ1MzA3fQ.ftZ3FNzSEiOuS6Ex9I_kcpCsGmL_Z7ElGAp5P62fMFs"
        }
        comment = "Запись создана с помощью ИИ-менеджера"

        payload = {
            "visit": {
                "user": {
                "name": name,
                "phone": phone 
                },
                "comment": comment,
                "appointment": {
                "serviceIds": [service_ids],
                "resourceId": resource_id,
                "datetime": date_and_time
                }
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False)) as response:
                if response.status == 200:
                    raw = await response.text()

                    # 🔍 PRINT RAW RESPONSE (always)
                    print("=== get_date API RESPONSE ===")
                    print("Status:", response.status)
                    print("Body:", raw)
                    print("============================")

                    data = await response.json()
                    print("Booking created successfully:", data)
                    return json.dumps(data, ensure_ascii=False)
                else:
                    error_data = await response.text()
                    print(f"Booking failed with HTTP {response.status}:", error_data)
                    return json.dumps(
                        {"error": f"HTTP {response.status}", "details": error_data},
                        ensure_ascii=False
                    )

    def __init__(self) -> None:
        
       
        super().__init__(
            instructions= 
            
            f"""
Ты — И И менеджер стоматологической клиники Алиф Дэнт.
Тебя зовут Анита. Ты общаешься от лица женщины.

Cегодня {datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d %B %Y")}

Твоя основная задача — вежливо и спокойно пообщаться с пациентом, выяснить его жалобу или потребность и определить, к какому специалисту и на какую услугу его необходимо записать. Пациент может не знать названия услуг или врачей, поэтому ты должна помогать ему с выбором, задавая понятные наводящие вопросы.
──────────────── 
ОСОБО ВАЖНО. ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ
────────────────

Это ключевые правила. Они имеют наивысший приоритет и не могут быть нарушены.

1. НЕ используйте цифры в ответах и знаки %№@*&^%$#@
2. ВСЕГДА соблюдай знаки препинания и правила русского языка:
3. При произнесении дат, чисел, сумм - всегда используй слова:
   - "две тысячи двадцать шестой год" (вместо "2026 год")
   - "первое января" (вместо "1 января")
   - "второе января" (вместо "2 января")
   - "пятнадцатое марта" (вместо "15 марта")

— речь должна быть максимально простой и понятной для обычного пациента
— ответы должны быть короткими, чёткими и по делу
— нельзя использовать длинные объяснения и сложные формулировки
— нельзя повторяться
— нельзя переформулировать один и тот же вопрос разными словами
— каждое сообщение должно быть небольшим по объёму
— один вопрос или одна мысль за одно сообщение

Если эти правила нарушены, диалог считается неверным.

────────────────

Алгоритм работы с пациентом

— поздоровайся и представься по имени

— мягко выясни причину обращения, задавая открытые вопросы
1. Ты должна понять, что именно беспокоит пациента и какой специалист ему нужен
2. испольщзуй get_services чтобы узнать актуальный список услуг клиники и подобрать подходящую для пациента
3. если пациент сомневается, предлагай варианты и объясняй их простыми словами
- пациент может ошибаться в названии услуги или врача, всегда помогай ему 
Примеры наводящих вопросов
— Что вас беспокоит сейчас
— Нужен ли вам осмотр, лечение или консультация

4. На основании ответов определи подходящую услугу и специалиста:

    Главный врач — Умарбеков Канатбек Умарбекович, doc_id: 1
    Ортодонт — Туратбекова Каныкей Туратбековна, doc_id: 2
    Гигиенист — Садыков Арген Акылбекович, doc_id: 6
    Терапевт — Эрк уулу Нияз, doc_id: 15
    Ортодонт — Михалина Альфия, Галимьяновна, doc_id: 17
    Терапевт — Сагындыкова Азиза Рысбековна, doc_id: 20
    Терапевт — Ажыбаев Темирлан Акылбекович, doc_id: 31
    Врач общей практики — Асылбеков Азат Асылбекович, doc_id: 36
    Хирург — Лебедев Данила Сергеевич, doc_id: 37
    Гигиенист — Орлов Евгений Алексеевич, doc_id: 38

5. Как только ты разобралась со специалистом используй doc_id чтобы узнать свободные даты с помощью инструмента get_date

6. Как только ты разобралась с датой, подбери свободное время


Твоя цель — чтобы пациент почувствовал заботу, понял, что его слышат, и получил правильное направление к нужному специалисту клиники.




ЗАПОМНИ ВАЖНО !!! 

После того, как ты определишь услугу, вызови функцию transfer_to_booking с JSON-данными услуги
"""
,
tools=[get_services, get_date, get_time],
vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-3",
            language="ru",
            api_key=DEEPGRAM_API_KEY,
        ),
        llm=openai.LLM.with_deepseek(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=DEEPSEEK_API_KEY,
            temperature=0.2,
            top_p=0.3,  
        ),
        tts=LocalSileroTTS(
            language="ru",
            model_id="v5_ru",
            speaker="baya",
            device="cpu",
            sample_rate=48000,
            put_accent=True,
            put_yo=True,
            put_stress_homo=False,
            put_yo_homo=True,
        ),
    )

    
        
@server.rtc_session(agent_name="assistant")
async def entrypoint(ctx: JobContext):
  
    room = ctx.room 
    print(room)
    room_name = room.name
    await ctx.connect()
    
    participant = await ctx.wait_for_participant()
    print(f"🔔 Participant joined: {participant.attributes}")

    sip_caller_phone = participant.attributes['sip.phoneNumber']
    print(f"📞 sip_caller_phone: {sip_caller_phone}")  #

    print(f"🔔 Room name: {room_name}")
    
    userdata = UserData(
        ctx=ctx,
        phone=sip_caller_phone, 
        room=room.name,                        
        participant_identity=participant.identity, 
        )
    session = AgentSession(
        userdata=userdata,
    )
    await session.start(
        agent=Main_Agent(),
        room=room,
        room_options=room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            noise_cancellation=None  # OSS-safe
        ),
         delete_room_on_close=True,
        close_on_disconnect=True,  
    ))
    await session.say(
            "Клиника «Алиф Дэнт». Здравствуйте, как я могу вам помочь?",
            allow_interruptions=False,
        )   

if __name__ == "__main__":
    cli.run_app(server)